"""가이드북 정책·CLI·실패 시 원본 보존을 검증한다."""
import csv
import inspect
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
from budget_app.cli import main
from budget_app.decorators import handle_errors
from budget_app.errors import AppError
from budget_app.models import Category
from budget_app.repositories import CsvRepository, TX_FIELDS, EXTERNAL_FIELDS, DEFAULT_CATEGORIES
from budget_app.services import BudgetService
from budget_app.validators import validate_date, validate_amount, validate_budget_amount

ROOT = Path(__file__).resolve().parents[1]


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.repo = CsvRepository(self.directory / 'data')
        self.repo.initialize_files()
        self.service = BudgetService(self.repo)

    def add(self, **changes):
        values = dict(date='2026-10-19', type='expense', category='식비', amount='100', memo='Lunch', tags='Meal, friend')
        values.update(changes)
        return self.service.add_transaction(**values)

    def cli(self, *args, inputs=()):
        out, err = io.StringIO(), io.StringIO()
        with patch('builtins.input', side_effect=inputs), redirect_stdout(out), redirect_stderr(err):
            code = main(['--data-dir', str(self.repo.directory), *args])
        return code, out.getvalue(), err.getvalue()

    def source(self, rows, fields=EXTERNAL_FIELDS):
        path = self.directory / 'input.csv'
        with path.open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def row(self, **changes):
        result = dict(date='2026-10-19', type='expense', category='식비', amount='100', memo='', tags='')
        result.update(changes)
        return result

    def assert_code(self, code, action):
        with self.assertRaises(AppError) as caught:
            action()
        self.assertEqual(caught.exception.code, code)

    def test_initialize_and_partial_loss(self):
        self.assertEqual([c.name for c in self.service.list_categories()], DEFAULT_CATEGORIES)
        self.assertTrue(all(p.exists() for p in self.repo.paths))
        self.repo.metadata.unlink()
        self.assert_code(5, self.repo.initialize_files)
        self.assertFalse(self.repo.metadata.exists())

    def test_old_jsonl_is_not_overwritten(self):
        directory = self.directory / 'legacy'
        directory.mkdir()
        original = directory / 'transactions.jsonl'
        original.write_text('legacy')
        self.assert_code(3, lambda: CsvRepository(directory).initialize_files())
        self.assertEqual(original.read_text(), 'legacy')
        self.assertEqual(list(directory.glob('*.csv')), [])

    def test_dates_and_amounts(self):
        self.assertEqual(validate_date('2024-02-29').day, 29)
        for value in ('2026-02-29', '2024-2-01', '0000-01-01', '20240101'):
            self.assert_code(2, lambda: validate_date(value))
        for value in (True, 0, -1, '1.1', 1.2, '1,000'):
            self.assert_code(2, lambda: validate_amount(value))
        self.assertEqual(validate_budget_amount(0), 0)
        self.assert_code(2, lambda: self.add(type='wrong'))
        self.assert_code(3, lambda: self.add(category='unknown'))

    def test_id_order_persistence_and_no_reuse(self):
        first = self.add(date='2026-12-01')
        second = self.add(date='2020-01-01')
        self.assertEqual([t.id for t in self.service.list_transactions()], [second.id, first.id])
        self.service.update_transaction(first.id, date='2010-01-01')
        self.service.delete_transaction(second.id)
        service = BudgetService(CsvRepository(self.repo.directory))
        third = service.add_transaction(date='2026-10-19', type='income', category='식비', amount=1)
        self.assertEqual(third.id, 'TX-000003')
        self.assertEqual([t.id for t in service.list_transactions()], [third.id, first.id])

    def test_case_normalization_and_tags(self):
        self.service.add_category('  Book Shop  ')
        self.assert_code(3, lambda: self.service.add_category('book shop'))
        tx = self.add(category=' book SHOP ', tags=' One,one,, TWO ,two,')
        self.assertEqual((tx.category, tx.tags), ('Book Shop', ['One', 'TWO']))
        self.assert_code(3, lambda: self.service.delete_category('BOOK SHOP'))

    def test_empty_categories_not_reseeded(self):
        self.repo.save_categories([])
        self.repo.initialize_files()
        self.assertEqual(self.service.list_categories(), [])
        self.assert_code(3, self.add)
        path = self.source([])
        self.assert_code(5, lambda: self.service.import_transactions(path))
        self.service.add_category('식비')
        self.add()

    def test_search_boundaries_and_all_tags(self):
        self.add(date='2026-10-01', tags='Meal, Friend')
        self.add(date='2026-10-31', tags='Meal')
        self.add(date='2026-11-01', memo='Dinner')
        self.assertEqual(len(list(self.service.search_transactions(start='2026-10-01', end='2026-10-31'))), 2)
        matches = list(self.service.search_transactions(start='2026-10-01', end='2026-10-31', category=' 식비 ',
                                                       type='expense', q='lUn', tags='meal,FRIEND'))
        self.assertEqual(len(matches), 1)
        self.assertEqual(len(list(self.service.search_transactions(tags='Me'))), 0)
        self.assertEqual(len(list(self.service.search_transactions(end='2026-10-01'))), 1)
        self.assert_code(2, lambda: list(self.service.search_transactions(start='2026-10-31', end='2026-10-01')))

    def test_budget_zero_unset_equal_exceeded_empty(self):
        self.assertIsNone(self.service.get_budget('2026-10'))
        self.service.set_budget('2026-10', 0)
        code, out, _ = self.cli('summary', '--month', '2026-10')
        self.assertEqual(code, 0)
        self.assertIn('거래 없음', out)
        self.assertIn('계산 불가', out)
        self.assertNotIn('초과', out)
        self.add()
        self.assertIn('초과', self.cli('summary', '--month', '2026-10')[1])
        old, new = self.service.set_budget('2026-10', 100)
        self.assertEqual((old.amount, new.amount), (0, 100))
        self.assertNotIn('초과', self.cli('summary', '--month', '2026-10')[1])
        self.assertEqual(self.service.get_monthly_summary('2026-10')['top'], [('식비', 100)])

    def test_update_clear_confirm_cancel_noop(self):
        tx = self.add()
        original = self.repo.transactions.read_bytes()
        code, out, _ = self.cli('update', '--id', tx.id, inputs=[''] * 6)
        self.assertEqual(code, 0)
        self.assertIn('변경 없음', out)
        self.assertEqual(self.repo.transactions.read_bytes(), original)
        self.cli('update', '--id', tx.id, inputs=['', '', '', '200', ':clear', ':clear', 'no'])
        self.assertEqual(self.repo.transactions.read_bytes(), original)
        self.cli('update', '--id', tx.id, inputs=['', '', '', '200', ':clear', ':clear', ' YES '])
        updated = self.service.get_transaction(tx.id)
        self.assertEqual((updated.amount, updated.memo, updated.tags), (200, '', []))
        self.cli('delete', '--id', tx.id, inputs=['n'])
        self.assertEqual(self.service.get_transaction(tx.id), updated)
        self.assertEqual(self.cli('delete', '--id', tx.id, inputs=['y'])[0], 0)
        self.assertEqual(self.cli('delete', '--id', tx.id)[0], 3)

    def test_import_repeat_multiline_roundtrip(self):
        memo = '한글, "따옴표"\n다음 줄'
        source = self.source([self.row(memo=memo, tags='Meal, Friend'), self.row(date='2000-01-01')])
        self.assertEqual(self.service.import_transactions(source), 2)
        self.assertEqual(self.service.import_transactions(source), 2)
        transactions = list(self.service.list_transactions())
        self.assertEqual([t.id for t in transactions], [f'TX-{i:06d}' for i in (4, 3, 2, 1)])
        self.assertEqual(transactions[1].memo, memo)
        output = self.directory / 'out.csv'
        self.assertEqual(self.service.export_transactions(output, start='1999-01-01', end='2026-12-31'), 4)
        other = CsvRepository(self.directory / 'other')
        other.initialize_files()
        service = BudgetService(other)
        self.assertEqual(service.import_transactions(output), 4)
        self.assertEqual(service.get_monthly_summary('2026-10'), self.service.get_monthly_summary('2026-10'))

    def test_invalid_import_rolls_back(self):
        self.add()
        original = self.repo.transactions.read_bytes()
        for changes in (dict(amount='-1'), dict(category='unknown'), dict(date='2026-02-30'), dict(type='bad')):
            source = self.source([self.row(), self.row(**changes)])
            self.assert_code(5, lambda: self.service.import_transactions(source))
            self.assertEqual(self.repo.transactions.read_bytes(), original)
        source = self.source([], fields=['date', 'amount'])
        self.assert_code(5, lambda: self.service.import_transactions(source))
        self.assertEqual(self.service.import_transactions(self.source([])), 0)
        self.assertEqual(list(self.repo.directory.glob('.budget-*')), [])

    def test_corrupt_stream_partial_and_summary_no_output(self):
        self.add()
        with self.repo.transactions.open('a', encoding='utf-8') as f:
            f.write('bad,expense,2026-10-19,100,식비,,\n')
        original = self.repo.transactions.read_bytes()
        code, _, err = self.cli('list')
        self.assertEqual(code, 5)
        self.assertIn('불완전', err)
        self.assertIn('레코드 2', err)
        self.assertEqual(self.cli('list', '--limit', '1')[0], 0)
        code, out, _ = self.cli('summary', '--month', '2026-10')
        self.assertEqual((code, out), (5, ''))
        self.assert_code(5, self.add)
        self.assertEqual(self.repo.transactions.read_bytes(), original)
        output = self.directory / 'out.csv'
        output.write_text('keep')
        self.assert_code(5, lambda: self.service.export_transactions(output, month='2026-10'))
        self.assertEqual(output.read_text(), 'keep')

    def test_metadata_and_duplicate_order_corruption(self):
        self.add()
        with self.repo.transactions.open('a', encoding='utf-8') as f:
            f.write('TX-000001,expense,2026-10-19,100,식비,,\n')
        self.assert_code(5, lambda: list(self.repo.iter_transactions()))
        self.repo.metadata.write_text('key,value\nlast_transaction_number,0\n', encoding='utf-8')
        self.assert_code(5, self.add)

    def test_replace_failure_preserves_original_and_reserved_gap(self):
        self.add()
        original = self.repo.transactions.read_bytes()
        real_replace = os.replace
        def fail_transactions(source, target):
            if Path(target) == self.repo.transactions:
                raise PermissionError('injected')
            return real_replace(source, target)
        with patch('budget_app.repositories.os.replace', side_effect=fail_transactions):
            with self.assertRaises(PermissionError):
                self.add()
        self.assertEqual(self.repo.transactions.read_bytes(), original)
        self.assertEqual(self.repo.last_number(), 2)
        self.assertEqual(self.add().id, 'TX-000003')
        self.assertEqual(list(self.repo.directory.glob('.budget-*')), [])

    def test_import_replace_failure_and_id_gap(self):
        original = self.repo.transactions.read_bytes()
        source = self.source([self.row(), self.row()])
        real_replace = os.replace
        def fail_transactions(source, target):
            if Path(target) == self.repo.transactions:
                raise PermissionError('injected')
            return real_replace(source, target)
        with patch('budget_app.repositories.os.replace', side_effect=fail_transactions):
            with self.assertRaises(PermissionError):
                self.service.import_transactions(source)
        self.assertEqual(self.repo.transactions.read_bytes(), original)
        self.assertEqual(self.add().id, 'TX-000003')

    def test_codes_and_decorator_metadata(self):
        self.assertEqual(self.cli('list', '--limit', '0')[0], 2)
        self.assertEqual(self.cli('list', '--limit', 'abc')[0], 2)
        self.assertEqual(self.cli('list', '--unknown')[0], 2)
        self.assertEqual(self.cli('import', '--file', str(self.directory / 'missing.csv'))[0], 4)
        self.assertEqual(self.cli('export', '--file', 'x.csv')[0], 2)
        self.assertEqual(self.cli('category', 'add', inputs=[EOFError()])[0], 0)
        @handle_errors
        def broken():
            raise RuntimeError('injected')
        self.assertEqual(broken.__name__, 'broken')
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(broken(), 1)
        self.assertNotIn('Traceback', err.getvalue())

    def test_all_help_no_files_and_actual_process(self):
        directory = self.directory / 'help-data'
        commands = [[], ['add'], ['list'], ['search'], ['update'], ['delete'], ['summary'], ['budget'],
                    ['budget', 'set'], ['budget', 'get'], ['category'], ['category', 'add'],
                    ['category', 'list'], ['category', 'delete'], ['import'], ['export']]
        for command in commands:
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as exit:
                main(['--data-dir', str(directory), *command, '--help'])
            self.assertEqual(exit.exception.code, 0)
        self.assertFalse(directory.exists())
        env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        result = subprocess.run([sys.executable, '-m', 'budget_app', '--data-dir', str(directory), 'list'],
                                capture_output=True, text=True, encoding='utf-8', cwd=ROOT, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('거래 없음', result.stdout)
        result = subprocess.run([sys.executable, '-m', 'budget_app', 'list', '--limit', '0'],
                                capture_output=True, text=True, encoding='utf-8', cwd=ROOT, env=env)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stderr)

    def test_large_import_generator_and_close(self):
        source = self.source(self.row(memo=f'행 {i}\n다음 줄') for i in range(10000))
        self.assertEqual(self.service.import_transactions(source), 10000)
        gen = self.service.list_transactions(3)
        self.assertTrue(inspect.isgenerator(gen))
        self.assertEqual([t.id for t in gen], ['TX-010000', 'TX-009999', 'TX-009998'])
        gen = self.repo.iter_transactions()
        next(gen)
        gen.close()
        self.assertEqual(self.service.get_monthly_summary('2026-10')['expense'], 1000000)

    def test_export_protects_storage_and_options(self):
        for path in self.repo.paths:
            self.assert_code(3, lambda: self.service.export_transactions(path, month='2026-10'))
        output = self.directory / 'existing.csv'
        output.write_text('keep')
        self.assert_code(2, lambda: self.service.export_transactions(output, month='2026-13'))
        self.assert_code(2, lambda: self.service.export_transactions(output, month='2026-10', start='2026-10-01'))
        self.assertEqual(output.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
