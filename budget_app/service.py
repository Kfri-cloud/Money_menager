"""거래 규칙, 디스크 기반 정렬, CSV 교환."""
import csv
import json
import os
import sqlite3
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Iterator

from .errors import AppError
from .models import Transaction, category_name, parse_date, parse_month, parse_tags, positive
from .repository import Repository

FIELDS = ["date", "type", "category", "amount", "memo", "tags"]


class BudgetService:
    def __init__(self, repository: Repository):
        self.repo = repository

    @contextmanager
    def ordered(self) -> Iterator[sqlite3.Connection]:
        """전체 거래를 Python 리스트에 올리지 않고 임시 디스크에 정렬한다."""
        with TemporaryDirectory(prefix="budget-sort-") as directory:
            connection = sqlite3.connect(str(Path(directory) / "sort.db"))
            try:
                connection.execute("PRAGMA temp_store=FILE")
                connection.execute("CREATE TABLE tx (seq INTEGER PRIMARY KEY, id TEXT UNIQUE, date TEXT, payload TEXT)")
                for tx in self.repo.iter_transactions():
                    try:
                        connection.execute("INSERT INTO tx(id,date,payload) VALUES (?,?,?)",
                                           (tx.id, tx.date, json.dumps(tx.to_dict(), ensure_ascii=False)))
                    except sqlite3.IntegrityError:
                        raise AppError(f"중복 거래 ID: {tx.id}", "거래 파일의 중복 ID를 복구하세요.") from None
                connection.commit()
                yield connection
            except sqlite3.Error as error:
                raise AppError(f"임시 정렬 실패: {error}", "임시 폴더의 여유 공간과 권한을 확인하세요.") from None
            finally:
                connection.close()

    def select(self, *, start: str | None = None, end: str | None = None,
               category: str | None = None, type: str | None = None,
               query: str | None = None, tag: str | None = None,
               month: str | None = None, limit: int | None = None) -> Iterator[Transaction]:
        if start is not None:
            parse_date(start)
        if end is not None:
            parse_date(end)
        if start and end and start > end:
            raise AppError("시작일이 종료일보다 늦습니다.")
        if month:
            parse_month(month)
        if limit is not None:
            positive(limit)
        count = 0
        with self.ordered() as db:
            for (payload,) in db.execute("SELECT payload FROM tx ORDER BY date DESC, seq DESC"):
                tx = Transaction.from_dict(json.loads(payload))
                if start and tx.date < start or end and tx.date > end:
                    continue
                if month and not tx.date.startswith(month + "-"):
                    continue
                if category is not None and tx.category != category or type is not None and tx.type != type:
                    continue
                if query is not None and query.casefold() not in tx.memo.casefold() or tag is not None and tag not in tx.tags:
                    continue
                yield tx
                count += 1
                if limit is not None and count >= limit:
                    break

    def validate_category(self, tx: Transaction) -> None:
        if tx.category not in self.repo.category_names():
            raise AppError(f"등록되지 않은 카테고리: {tx.category}", "category add로 먼저 등록하세요.")

    def add(self, tx: Transaction) -> None:
        self.validate_category(tx)
        with self.ordered() as db:
            if db.execute("SELECT 1 FROM tx WHERE id=?", (tx.id,)).fetchone():
                raise AppError(f"중복 거래 ID: {tx.id}")
            def rows():
                for (payload,) in db.execute("SELECT payload FROM tx ORDER BY seq"):
                    yield json.loads(payload)
                yield tx.to_dict()
            self.repo.write(self.repo.transactions, rows())

    def change(self, transaction_id: str, changes: dict | None = None) -> None:
        if changes == {}:
            raise AppError("수정할 필드를 지정하지 않았습니다.", "--amount, --memo 등 수정 옵션을 지정하세요.")
        with self.ordered() as db:
            if not db.execute("SELECT 1 FROM tx WHERE id=?", (transaction_id,)).fetchone():
                raise AppError(f"없는 데이터: {transaction_id}", "list에서 ID를 확인하세요.")
            def rows():
                for (payload,) in db.execute("SELECT payload FROM tx ORDER BY seq"):
                    row = json.loads(payload)
                    if row["id"] == transaction_id:
                        if changes is None:
                            continue
                        row.update(changes)
                        tx = Transaction.from_dict(row)
                        self.validate_category(tx)
                        row = tx.to_dict()
                    yield row
            self.repo.write(self.repo.transactions, rows())

    def category(self, action: str, name: str) -> None:
        name = category_name(name)
        names = self.repo.category_names()
        if action == "add":
            if name in names:
                raise AppError(f"이미 등록된 카테고리: {name}")
            names.add(name)
        else:
            if name not in names:
                raise AppError(f"없는 카테고리: {name}")
            with self.ordered() as db:
                for (payload,) in db.execute("SELECT payload FROM tx"):
                    if json.loads(payload)["category"] == name:
                        raise AppError(f"사용 중인 카테고리: {name}", "해당 거래를 먼저 수정·삭제하세요.")
            names.remove(name)
        self.repo.write(self.repo.categories, ({"name": n} for n in sorted(names)))

    def set_budget(self, month: str, amount: str) -> None:
        values = self.repo.budget_values()
        values[parse_month(month)] = positive(amount)
        self.repo.write(self.repo.budgets, ({"month": m, "amount": a} for m, a in sorted(values.items())))

    def summary(self, month: str, top: int) -> dict:
        parse_month(month)
        positive(top)
        income = expense = count = 0
        categories: dict[str, int] = defaultdict(int)
        # ordered() also validates duplicate IDs without retaining an in-memory ID set.
        for tx in self.select(month=month):
            count += 1
            if tx.type == "income":
                income += tx.amount
            else:
                expense += tx.amount
                categories[tx.category] += tx.amount
        return {"count": count, "income": income, "expense": expense, "balance": income - expense,
                "top": sorted(categories.items(), key=lambda item: (-item[1], item[0]))[:top],
                "budget": self.repo.budget_values().get(month)}

    def import_csv(self, path: str) -> int:
        count = 0
        with self.ordered() as db:
            def rows():
                nonlocal count
                for (payload,) in db.execute("SELECT payload FROM tx ORDER BY seq"):
                    yield json.loads(payload)
                with Path(path).open(encoding="utf-8-sig", newline="") as stream:
                    reader = csv.DictReader(stream, strict=True)
                    headers = reader.fieldnames or []
                    if not set(FIELDS[:4]).issubset(headers) or len(headers) != len(set(headers)):
                        raise AppError("CSV 필수 헤더가 없거나 중복되었습니다.", "date,type,category,amount 헤더를 확인하세요.")
                    try:
                        for row in reader:
                            try:
                                if None in row or any(value is None for value in row.values()):
                                    raise AppError("열 개수가 헤더와 다릅니다.")
                                tx = Transaction.create(**{key: row.get(key, "") for key in FIELDS})
                                self.validate_category(tx)
                            except AppError as error:
                                raise AppError(f"CSV {reader.line_num}행: {error}", "해당 행을 수정한 뒤 다시 가져오세요. 기존 거래는 유지됩니다.") from None
                            count += 1
                            yield tx.to_dict()
                    except csv.Error as error:
                        raise AppError(f"CSV {reader.line_num}행 문법 오류: {error}") from None
            self.repo.write(self.repo.transactions, rows())
        return count

    def export_csv(self, path: str, *, month: str | None, start: str | None, end: str | None) -> int:
        if bool(month) == bool(start or end) or (not month and not (start and end)):
            raise AppError("내보내기 조건이 잘못되었습니다.", "--month 또는 --from과 --to를 함께 지정하세요.")
        output = Path(path)
        if any(output.resolve() == p.resolve() or (output.exists() and os.path.samefile(output, p)) for p in self.repo.paths):
            raise AppError("원본 데이터 파일로 내보낼 수 없습니다.", "별도 CSV 경로를 지정하세요.")
        temporary = None
        count = 0
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=output.parent,
                                    prefix=".budget-export-", delete=False) as stream:
                temporary = Path(stream.name)
                writer = csv.DictWriter(stream, fieldnames=FIELDS)
                writer.writeheader()
                for tx in self.select(month=month, start=start, end=end):
                    row = tx.to_dict()
                    del row["id"]
                    row["tags"] = ",".join(tx.tags)
                    writer.writerow(row)
                    count += 1
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return count
