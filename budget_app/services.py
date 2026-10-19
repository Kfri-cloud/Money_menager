"""검증·저장·검색·집계 작업을 조정하는 서비스."""
import json
import os
import struct
from collections import defaultdict
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryFile
from typing import Iterator
from .errors import AppError, data_error
from .models import Transaction, Category, Budget
from .repositories import CsvRepository, EXTERNAL_FIELDS
from .validators import (validate_transaction_type, validate_date, validate_amount, validate_category,
                         validate_month, validate_budget_amount, normalize_name, normalize_tags,
                         validate_period)


class BudgetService:
    def __init__(self, repository: CsvRepository):
        self.repository = repository

    def prepare_transaction(self, *, date, type, category, amount, memo="", tags="", id="") -> Transaction:
        if not isinstance(memo, str):
            raise AppError("메모는 문자열이어야 합니다.")
        return Transaction(id, validate_transaction_type(type), validate_date(date), validate_amount(amount),
                           validate_category(category, self.repository.load_categories()), memo, normalize_tags(tags))

    def add_transaction(self, **values) -> Transaction:
        tx = self.prepare_transaction(**values)
        number = self.repository.reserve_ids(1)
        tx.id = f"TX-{number:06d}"
        self.repository.add_transaction(tx)
        return tx

    def list_transactions(self, limit: int = 20) -> Iterator[Transaction]:
        limit = validate_amount(limit)
        with closing(self.repository.iter_transactions()) as transactions:
            for count, tx in enumerate(transactions, 1):
                yield tx
                if count >= limit:
                    return

    def search_transactions(self, *, start=None, end=None, category=None, type=None, q=None, tags="",
                            month=None) -> Iterator[Transaction]:
        start, end = validate_period(start, end)
        if month is not None:
            validate_month(month)
        if category is not None:
            category = validate_category(category, self.repository.load_categories())
        if type is not None:
            validate_transaction_type(type)
        wanted = {t.casefold() for t in normalize_tags(tags)}
        with closing(self.repository.iter_transactions()) as transactions:
            for tx in transactions:
                if start and tx.date < start or end and tx.date > end:
                    continue
                if month is not None and tx.date.isoformat()[:7] != month:
                    continue
                if category is not None and tx.category != category or type is not None and tx.type != type:
                    continue
                if q is not None and q.casefold() not in tx.memo.casefold():
                    continue
                if not wanted.issubset({t.casefold() for t in tx.tags}):
                    continue
                yield tx

    def get_transaction(self, transaction_id: str) -> Transaction:
        return self.repository.get_transaction(transaction_id)

    def preview_update(self, transaction_id: str, **changes) -> Transaction:
        old = self.get_transaction(transaction_id)
        values = {k: getattr(old, k) for k in ("date", "type", "category", "amount", "memo", "tags")}
        if set(changes) - set(values):
            raise AppError("수정할 수 없는 필드입니다.")
        values.update(changes)
        return self.prepare_transaction(id=old.id, **values)

    def update_transaction(self, transaction_id: str, **changes) -> Transaction:
        old = self.get_transaction(transaction_id)
        tx = self.preview_update(transaction_id, **changes)
        if tx != old:
            self.repository.validate_all()
            self.repository.update_transaction(tx)
        return tx

    def delete_transaction(self, transaction_id: str) -> None:
        self.get_transaction(transaction_id)
        self.repository.validate_all()
        self.repository.delete_transaction(transaction_id)

    def get_monthly_summary(self, month: str, top: int = 5) -> dict:
        validate_month(month)
        top = validate_amount(top)
        income = expense = count = 0
        categories = defaultdict(int)
        for tx in self.search_transactions(month=month):
            count += 1
            if tx.type == "income":
                income += tx.amount
            else:
                expense += tx.amount
                categories[tx.category] += tx.amount
        budget = self.get_budget(month)
        return {"count": count, "income": income, "expense": expense, "balance": income - expense,
                "top": sorted(categories.items(), key=lambda item: (-item[1], item[0]))[:top],
                "budget": budget.amount if budget is not None else None}

    def set_budget(self, month: str, amount: str | int) -> tuple[Budget | None, Budget]:
        month, amount = validate_month(month), validate_budget_amount(amount)
        self.repository.validate_all()
        values = self.repository.load_budgets()
        previous = values.get(month)
        values[month] = Budget(month, amount)
        self.repository.save_budgets(list(values.values()))
        return previous, values[month]

    def get_budget(self, month: str) -> Budget | None:
        return self.repository.load_budgets().get(validate_month(month))

    def add_category(self, name: str) -> Category:
        name = normalize_name(name)
        self.repository.validate_all()
        categories = self.list_categories()
        if any(c.name.casefold() == name.casefold() for c in categories):
            raise AppError(f"중복 카테고리: {name}", "기존 등록 표기를 사용하세요.", 3)
        category = Category(name)
        self.repository.save_categories(categories + [category])
        return category

    def list_categories(self) -> list[Category]:
        return self.repository.load_categories()

    def delete_category(self, name: str) -> None:
        name = validate_category(name, self.list_categories())
        self.repository.validate_all()
        for tx in self.repository.iter_transactions():
            if tx.category == name:
                raise AppError(f"사용 중인 카테고리: {name}", "해당 거래를 수정·삭제하세요.", 3)
        self.repository.save_categories([c for c in self.list_categories() if c.name != name])

    def import_transactions(self, path: str | Path) -> int:
        count = 0
        # JSON 레코드 스풀 + 고정폭 오프셋 인덱스: CSV 물리적 줄을 뒤집지 않는다.
        with TemporaryFile(dir=self.repository.directory) as spool, TemporaryFile(dir=self.repository.directory) as index:
            if not self.list_categories():
                raise data_error("카테고리가 없습니다. category add로 먼저 등록하세요.")
            for number, row in enumerate(self.repository.records(Path(path), EXTERNAL_FIELDS, external=True), 1):
                try:
                    tx = self.prepare_transaction(**{k: row.get(k, "") for k in EXTERNAL_FIELDS})
                except AppError as error:
                    raise data_error(f"{path} 레코드 {number}: {error}") from None
                index.write(struct.pack("<Q", spool.tell()))
                spool.write((json.dumps(self.repository.transaction_row(tx), ensure_ascii=False) + "\n").encode("utf-8"))
                count += 1
            first = self.repository.reserve_ids(count)
            if not count:
                return 0
            def new_transactions():
                for position in range(count - 1, -1, -1):
                    index.seek(position * 8)
                    spool.seek(struct.unpack("<Q", index.read(8))[0])
                    row = json.loads(spool.readline())
                    row["id"] = f"TX-{first + position:06d}"
                    yield self.prepare_transaction(**row)
            self.repository.prepend_transactions(new_transactions())
        return count

    def export_transactions(self, path: str | Path, *, month=None, start=None, end=None) -> int:
        if (month is not None and (start is not None or end is not None)) or (month is None and (start is None or end is None)):
            raise AppError("--month 또는 --from과 --to를 함께 지정하세요.")
        if month is not None:
            validate_month(month)
        start, end = validate_period(start, end)
        output = Path(path)
        if any(output.resolve() == p.resolve() or (output.exists() and os.path.samefile(output, p)) for p in self.repository.paths):
            raise AppError("원본 저장 파일로 내보낼 수 없습니다.", "별도 경로를 지정하세요.", 3)
        # 기존 출력 파일도 오류 시 보존. 성공한 경우에만 교체한다.
        count = 0
        def rows():
            nonlocal count
            for tx in self.search_transactions(month=month, start=start, end=end):
                row = self.repository.transaction_row(tx)
                del row["id"]
                count += 1
                yield row
        self.repository.write(output, EXTERNAL_FIELDS, rows())
        return count


