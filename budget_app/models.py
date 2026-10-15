"""거래 모델 및 입력/파일 공통 검증."""
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any
from uuid import uuid4

from .errors import AppError


def parse_date(value: str) -> str:
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError:
        raise AppError(f"잘못된 날짜: {value}", "실제 존재하는 YYYY-MM-DD 날짜를 입력하세요.") from None
    return value


def parse_month(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}", value):
        raise AppError(f"잘못된 월: {value}", "YYYY-MM 형식으로 입력하세요.")
    parse_date(value + "-01")
    return value


def positive(value: str | int) -> int:
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value)) or int(value) <= 0:
        raise AppError(f"양수 정수가 필요합니다: {value}", "쉼표 없이 1 이상의 정수를 입력하세요.")
    return int(value)


def parse_tags(value: str) -> list[str]:
    return list(dict.fromkeys(part.strip() for part in value.split(",") if part.strip()))


def category_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(c in value for c in "\r\n"):
        raise AppError("카테고리 이름이 비어 있거나 줄바꿈이 있습니다.")
    return value.strip()


@dataclass
class Transaction:
    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise AppError("거래 ID는 비어 있지 않은 문자열이어야 합니다.")
        if self.type not in ("income", "expense"):
            raise AppError("종류는 income 또는 expense여야 합니다.")
        parse_date(self.date)
        if type(self.amount) is not int:
            raise AppError("저장된 금액은 정수여야 합니다.")
        positive(self.amount)
        self.category = category_name(self.category)
        if not isinstance(self.memo, str):
            raise AppError("메모는 문자열이어야 합니다.")
        if not isinstance(self.tags, list) or any(not isinstance(t, str) or not t.strip() or "," in t for t in self.tags):
            raise AppError("태그는 쉼표 없는 문자열 목록이어야 합니다.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "Transaction":
        try:
            return cls(**row)
        except TypeError as error:
            raise AppError(f"거래 필드 오류: {error}") from None

    @classmethod
    def create(cls, *, type: str, date: str, amount: str | int, category: str,
               memo: str = "", tags: str = "") -> "Transaction":
        return cls(str(uuid4()), type, date, positive(amount), category, memo, parse_tags(tags))
