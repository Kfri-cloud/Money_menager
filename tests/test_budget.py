"""표준 unittest와 실제 CLI 프로세스로 과제 계약을 검증한다."""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from budget_app.errors import AppError
from budget_app.models import Transaction
from budget_app.repository import Repository
from budget_app.service import BudgetService

ROOT = Path(__file__).resolve().parents[1]


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.repo = Repository(self.directory / "data")
        self.service = BudgetService(self.repo)

    def seed(self):
        self.assertEqual(self.service.import_csv(str(ROOT / "examples/transactions.csv")), 4)

    def cli(self, *args, input=None):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        return subprocess.run([sys.executable, "-m", "budget_app", "--data-dir", str(self.repo.directory), *args],
                              cwd=ROOT, input=input, text=True, encoding="utf-8", capture_output=True, env=env)

    def test_sample_summary_filters_and_order(self):
        self.seed()
        self.service.set_budget("2024-01", "5000")
        summary = self.service.summary("2024-01", 3)
        self.assertEqual((summary["income"], summary["expense"], summary["balance"], summary["budget"]),
                         (20000, 6500, 13500, 5000))
        self.assertEqual(summary["top"], [("food", 5000), ("transport", 1500)])
        self.assertEqual([tx.date for tx in self.service.select(limit=2)], ["2024-02-01", "2024-01-15"])
        self.assertEqual(len(list(self.service.select(category="food", query="점심", tag="lunch"))), 1)
        self.assertEqual(len(list(self.service.select(start="2024-01-12", end="2024-01-15", type="expense"))), 2)
        self.assertEqual(self.service.summary("2024-03", 3)["count"], 0)
        result = self.cli("summary", "--month", "2024-01")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("130.0%", result.stdout)
        self.assertIn("예산 초과", result.stdout)

    def test_add_update_delete_and_restart(self):
        result = self.cli("add", input="2024-01-15\nexpense\nfood\n5000\n점심\nmeal,lunch\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        tx = next(self.repo.iter_transactions())
        result = self.cli("update", "--id", tx.id, "--amount", "6000", "--memo", "", "--tags", "")
        self.assertEqual(result.returncode, 0, result.stderr)
        updated = next(Repository(self.repo.directory).iter_transactions())
        self.assertEqual((updated.amount, updated.memo, updated.tags, updated.id), (6000, "", [], tx.id))
        self.assertEqual(self.cli("delete", "--id", tx.id).returncode, 0)
        self.assertEqual(list(self.repo.iter_transactions()), [])

    def test_csv_round_trip(self):
        self.seed()
        output = self.directory / "out.csv"
        self.assertEqual(self.service.export_csv(str(output), month="2024-01", start=None, end=None), 3)
        other = BudgetService(Repository(self.directory / "other"))
        self.assertEqual(other.import_csv(str(output)), 3)
        self.assertEqual(other.summary("2024-01", 3), self.service.summary("2024-01", 3))
        self.assertEqual(next(other.select(category="food")).memo, "친구와 점심, 분식")
        self.assertEqual(next(other.select(category="food")).tags, ["meal", "lunch"])
        self.assertEqual(self.service.export_csv(str(output), month=None, start="2024-01-12", end="2024-01-15"), 2)

    def test_import_rollback_and_no_temporary_files(self):
        self.seed()
        original = self.repo.transactions.read_bytes()
        source = self.directory / "bad.csv"
        source.write_text("date,type,category,amount\n2024-01-01,income,salary,10\n2024-01-01,expense,food,-1\n", encoding="utf-8")
        with self.assertRaises(AppError):
            self.service.import_csv(str(source))
        self.assertEqual(self.repo.transactions.read_bytes(), original)
        self.assertEqual(list(self.repo.directory.glob(".budget-*")), [])

    def test_failed_mutations_preserve_bytes(self):
        self.seed()
        original = self.repo.transactions.read_bytes()
        tx = next(self.repo.iter_transactions())
        for args in (("missing", None), (tx.id, {"date": "2024-02-30"}), (tx.id, {"category": "unknown"}), (tx.id, {})):
            with self.assertRaises(AppError):
                self.service.change(*args)
            self.assertEqual(self.repo.transactions.read_bytes(), original)
        self.repo.transactions.write_bytes(original + b'{broken}\n')
        corrupted = self.repo.transactions.read_bytes()
        with self.assertRaises(AppError):
            self.service.change(tx.id)
        self.assertEqual(self.repo.transactions.read_bytes(), corrupted)

    def test_categories_and_budget_persist(self):
        self.service.category("add", "books")
        self.assertIn("books", Repository(self.repo.directory).category_names())
        self.service.category("remove", "books")
        self.seed()
        with self.assertRaises(AppError):
            self.service.category("remove", "food")
        self.service.set_budget("2024-01", "100")
        self.service.set_budget("2024-01", "5000")
        self.assertEqual(Repository(self.repo.directory).budget_values(), {"2024-01": 5000})

    def test_duplicate_and_invalid_stored_types(self):
        tx = Transaction.create(type="expense", date="2024-01-01", amount="10", category="food")
        self.repo.write(self.repo.transactions, [tx.to_dict(), tx.to_dict()])
        with self.assertRaises(AppError):
            list(self.service.select())
        for value in (True, 1.5, "10", 0):
            row = tx.to_dict()
            row["amount"] = value
            with self.assertRaises(AppError):
                Transaction.from_dict(row)

    def test_cli_errors_and_help(self):
        for args in (("list", "--limit", "0"), ("summary", "--month", "2024-13"),
                     ("delete", "--id", "missing"), ("export", "--out", "out.csv"),
                     ("search", "--from", "2024-02-01", "--to", "2024-01-01"),
                     ("list", "--unknown"), ("summary", "--month", "2024-01", "--top", "abc")):
            result = self.cli(*args)
            self.assertNotEqual(result.returncode, 0, args)
            self.assertIn("[힌트]", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        for command in ([], ["add"], ["list"], ["search"], ["summary"], ["budget"], ["budget", "set"],
                        ["category"], ["category", "add"], ["category", "list"], ["category", "remove"],
                        ["update"], ["delete"], ["import"], ["export"]):
            result = self.cli(*command, "--help")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_export_protects_original_and_existing_output(self):
        self.seed()
        with self.assertRaises(AppError):
            self.service.export_csv(str(self.repo.transactions), month="2024-01", start=None, end=None)
        output = self.directory / "existing.csv"
        output.write_text("keep", encoding="utf-8")
        with self.assertRaises(AppError):
            self.service.export_csv(str(output), month="2024-13", start=None, end=None)
        self.assertEqual(output.read_text(), "keep")

    def test_replace_failure_preserves_original(self):
        self.seed()
        original = self.repo.transactions.read_bytes()
        tx = next(self.repo.iter_transactions())
        with patch("budget_app.repository.os.replace", side_effect=PermissionError("denied")):
            with self.assertRaises(PermissionError):
                self.service.change(tx.id, {"amount": 123})
        self.assertEqual(self.repo.transactions.read_bytes(), original)
        self.assertEqual(list(self.repo.directory.glob(".budget-*")), [])

    def test_large_out_of_order_stream_and_early_close(self):
        self.repo.write(self.repo.transactions, (
            Transaction(str(i), "expense", f"2024-01-{i % 28 + 1:02}", 1, "food").to_dict()
            for i in range(10000)))
        transactions = self.service.select(limit=3)
        self.assertEqual([tx.id for tx in transactions], ["9995", "9967", "9939"])
        transactions = self.service.select()
        self.assertEqual(next(transactions).date, "2024-01-28")
        transactions.close()
        self.assertEqual(self.service.summary("2024-01", 3)["expense"], 10000)

    def test_empty_csv_missing_header_and_category_cli(self):
        source = self.directory / "header.csv"
        source.write_text("date,type,category,amount\n", encoding="utf-8")
        self.assertEqual(self.service.import_csv(str(source)), 0)
        source.write_text("date,amount\n", encoding="utf-8")
        with self.assertRaises(AppError):
            self.service.import_csv(str(source))
        self.assertEqual(self.cli("category", "add", input="books\n").returncode, 0)
        self.assertIn("books", self.cli("category", "list").stdout)
        self.assertEqual(self.cli("category", "remove", input="books\n").returncode, 0)


if __name__ == "__main__":
    unittest.main()
