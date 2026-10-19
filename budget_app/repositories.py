"""CSV 직렬화, 스트리밍 검사, 임시 파일을 이용한 원자적 교체."""
import csv
import os
from contextlib import closing
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Iterator
from .errors import AppError, data_error
from .models import Transaction, Category, Budget
from .validators import (validate_transaction_type, validate_date, validate_amount,
                         validate_category, validate_month, validate_budget_amount,
                         normalize_name, normalize_tags, id_number)

TX_FIELDS = ["id", "type", "date", "amount", "category", "memo", "tags"]
EXTERNAL_FIELDS = ["date", "type", "category", "amount", "memo", "tags"]
DEFAULT_CATEGORIES = "급여 용돈 기타수입 식비 교통 주거 생활용품 여가 기타지출".split()


class CsvRepository:
    def __init__(self, data_dir: str | Path):
        self.directory = Path(data_dir)
        self.transactions = self.directory / "transactions.csv"
        self.categories = self.directory / "categories.csv"
        self.budgets = self.directory / "budgets.csv"
        self.metadata = self.directory / "metadata.csv"

    @property
    def paths(self) -> tuple[Path, ...]:
        return self.transactions, self.categories, self.budgets, self.metadata

    def initialize_files(self) -> None:
        existing = [p.exists() for p in self.paths]
        if any(existing):
            if not all(existing):
                raise data_error("저장 CSV 일부가 누락되었습니다. 백업에서 네 파일을 함께 복원하세요.")
            return
        if any(self.directory.glob("*.jsonl")):
            raise AppError("기존 JSONL 자료가 있습니다.", "원본을 보관하고 별도 --data-dir을 지정하세요. 자동 변환하지 않습니다.", 3)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.write(self.transactions, TX_FIELDS, ())
        self.save_categories([Category(n) for n in DEFAULT_CATEGORIES])
        self.save_budgets([])
        self.write(self.metadata, ["key", "value"], [{"key": "last_transaction_number", "value": 0}])

    def records(self, path: Path, fields: list[str], *, external=False) -> Iterator[dict[str, str]]:
        number = 0
        try:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream, strict=True)
                header = reader.fieldnames or []
                valid = (set(EXTERNAL_FIELDS[:4]).issubset(header) if external else header == fields)
                if not valid or len(header) != len(set(header)):
                    raise data_error(f"{path}: 헤더가 잘못되었습니다. 필요 열: {fields}")
                for number, row in enumerate(reader, 1):
                    if None in row or any(v is None for v in row.values()):
                        raise data_error(f"{path} 레코드 {number}: 열 개수가 헤더와 다릅니다.")
                    yield row
        except (csv.Error, UnicodeError) as error:
            line = reader.line_num if 'reader' in locals() else 0
            raise data_error(f"{path} 레코드 {number + 1}, 파서 줄 {line}: {error}") from None

    def write(self, path: Path, fields: list[str], rows: Iterable[dict]) -> None:
        temporary = None
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent,
                                    prefix=".budget-", delete=False) as stream:
                temporary = Path(stream.name)
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def load_categories(self) -> list[Category]:
        result, seen = [], set()
        for number, row in enumerate(self.records(self.categories, ["name"]), 1):
            try:
                name = normalize_name(row["name"])
                if name != row["name"] or name.casefold() in seen:
                    raise AppError("이름의 비정규 형식 또는 중복")
                seen.add(name.casefold())
                result.append(Category(name))
            except AppError as error:
                raise data_error(f"{self.categories} 레코드 {number}: {error}") from None
        return result

    def save_categories(self, categories: list[Category]) -> None:
        self.write(self.categories, ["name"], ({"name": c.name} for c in categories))

    def load_budgets(self) -> dict[str, Budget]:
        result = {}
        for number, row in enumerate(self.records(self.budgets, ["month", "amount"]), 1):
            try:
                month = validate_month(row["month"])
                if month in result:
                    raise AppError("중복 월")
                result[month] = Budget(month, validate_budget_amount(row["amount"]))
            except AppError as error:
                raise data_error(f"{self.budgets} 레코드 {number}: {error}") from None
        return result

    def save_budgets(self, budgets: list[Budget]) -> None:
        self.write(self.budgets, ["month", "amount"], ({"month": b.month, "amount": b.amount} for b in budgets))

    def last_number(self) -> int:
        rows = list(self.records(self.metadata, ["key", "value"]))
        try:
            if len(rows) != 1 or rows[0]["key"] != "last_transaction_number":
                raise AppError("메타데이터 키/행 오류")
            return validate_budget_amount(rows[0]["value"])
        except AppError as error:
            raise data_error(f"{self.metadata} 레코드 1: {error}") from None

    def iter_transactions(self) -> Iterator[Transaction]:
        categories = self.load_categories()
        last = self.last_number()
        previous = last + 1
        for number, row in enumerate(self.records(self.transactions, TX_FIELDS), 1):
            try:
                numeric = id_number(row["id"])
                if numeric >= previous:
                    raise AppError("ID 순서·중복 또는 metadata보다 큰 ID")
                previous = numeric
                category = validate_category(row["category"], categories)
                tags = normalize_tags(row["tags"])
                if category != row["category"] or ",".join(tags) != row["tags"]:
                    raise AppError("카테고리/태그 정규화 오류")
                yield Transaction(row["id"], validate_transaction_type(row["type"]),
                                  validate_date(row["date"]), validate_amount(row["amount"]),
                                  category, row["memo"], tags)
            except AppError as error:
                raise data_error(f"{self.transactions} 레코드 {number}: {error}") from None

    @staticmethod
    def transaction_row(tx: Transaction) -> dict:
        return {"id": tx.id, "type": tx.type, "date": tx.date.isoformat(), "amount": tx.amount,
                "category": tx.category, "memo": tx.memo, "tags": ",".join(tx.tags)}

    def validate_all(self) -> None:
        self.load_budgets()
        for _ in self.iter_transactions():
            pass

    def reserve_ids(self, count: int) -> int:
        self.validate_all()
        last = self.last_number()
        if count:
            self.write(self.metadata, ["key", "value"], [{"key": "last_transaction_number", "value": last + count}])
        return last + 1

    def prepend_transactions(self, new: Iterable[Transaction]) -> None:
        def rows():
            for tx in new:
                yield self.transaction_row(tx)
            for tx in self.iter_transactions():
                yield self.transaction_row(tx)
        self.write(self.transactions, TX_FIELDS, rows())

    def add_transaction(self, transaction: Transaction) -> None:
        self.prepend_transactions([transaction])

    def get_transaction(self, transaction_id: str) -> Transaction:
        id_number(transaction_id)
        with closing(self.iter_transactions()) as transactions:
            for tx in transactions:
                if tx.id == transaction_id:
                    return tx
        raise AppError(f"없는 ID: {transaction_id}", "list로 ID를 확인하세요.", 3)

    def _rewrite(self, transaction_id: str, replacement: Transaction | None) -> None:
        def rows():
            found = False
            for tx in self.iter_transactions():
                if tx.id == transaction_id:
                    found = True
                    if replacement is not None:
                        yield self.transaction_row(replacement)
                else:
                    yield self.transaction_row(tx)
            if not found:
                raise AppError(f"없는 ID: {transaction_id}", "list로 ID를 확인하세요.", 3)
        self.write(self.transactions, TX_FIELDS, rows())

    def update_transaction(self, transaction: Transaction) -> None:
        self._rewrite(transaction.id, transaction)

    def delete_transaction(self, transaction_id: str) -> None:
        self._rewrite(transaction_id, None)

