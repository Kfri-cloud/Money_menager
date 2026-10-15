"""JSONL 영구 저장과 임시 파일 교체. 단일 프로세스 사용을 가정한다."""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterable, Iterator

from .errors import AppError
from .models import Transaction, category_name, parse_month, positive


class Repository:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.transactions = self.directory / "transactions.jsonl"
        self.categories = self.directory / "categories.jsonl"
        self.budgets = self.directory / "budgets.jsonl"
        self.directory.mkdir(parents=True, exist_ok=True)
        for path in self.paths:
            path.touch(exist_ok=True)
        if not self.category_names():
            self.write(self.categories, ({"name": name} for name in ("food", "transport", "salary", "etc")))

    @property
    def paths(self) -> tuple[Path, ...]:
        return self.transactions, self.categories, self.budgets

    def records(self, path: Path) -> Iterator[dict[str, Any]]:
        with path.open(encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError("JSON 객체가 아닙니다")
                except ValueError as error:
                    raise AppError(f"{path} {number}행 오류: {error}", "원본을 백업하고 해당 행을 복구하세요.") from None
                yield row

    def write(self, path: Path, rows: Iterable[dict[str, Any]]) -> None:
        temporary = None
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                    prefix=".budget-", delete=False) as stream:
                temporary = Path(stream.name)
                for row in rows:
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def category_names(self) -> set[str]:
        names = set()
        for row in self.records(self.categories):
            if set(row) != {"name"} or category_name(row["name"]) != row["name"] or row["name"] in names:
                raise AppError("카테고리 파일에 잘못된 값 또는 중복이 있습니다.", "categories.jsonl을 확인하세요.")
            names.add(row["name"])
        return names

    def budget_values(self) -> dict[str, int]:
        values = {}
        for row in self.records(self.budgets):
            if set(row) != {"month", "amount"}:
                raise AppError("예산 파일 필드가 올바르지 않습니다.")
            month = parse_month(row["month"])
            if month in values or type(row["amount"]) is not int:
                raise AppError("예산 파일의 중복 월 또는 금액 오류입니다.")
            values[month] = positive(row["amount"])
        return values

    def iter_transactions(self) -> Iterator[Transaction]:
        categories = self.category_names()
        for number, row in enumerate(self.records(self.transactions), 1):
            try:
                transaction = Transaction.from_dict(row)
                if transaction.category not in categories:
                    raise AppError(f"미등록 카테고리: {transaction.category}")
            except AppError as error:
                raise AppError(f"{self.transactions} 거래 {number}: {error}", "원본을 백업하고 거래 필드를 복구하세요.") from None
            yield transaction
