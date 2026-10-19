"""파일과 콘솔에 의존하지 않는 값 검증·정규화."""
import re
from datetime import date
from collections.abc import Iterable
from .errors import AppError
from .models import Category


def validate_transaction_type(value: str) -> str:
    if value not in ("income", "expense"):
        raise AppError("종류는 income 또는 expense여야 합니다.")
    return value


def validate_date(value: str | date) -> date:
    if type(value) is date:
        return value
    try:
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise ValueError
        return date.fromisoformat(value)
    except ValueError:
        raise AppError(f"잘못된 날짜: {value}", "실제 존재하는 YYYY-MM-DD 날짜를 입력하세요.") from None


def integer(value: str | int, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not re.fullmatch(r"[0-9]+", str(value)):
        raise AppError(f"정수가 필요합니다: {value}")
    result = int(value)
    if result < minimum:
        raise AppError(f"{minimum} 이상의 정수가 필요합니다: {value}")
    return result


def validate_amount(value: str | int) -> int:
    return integer(value, 1)


def validate_budget_amount(value: str | int) -> int:
    return integer(value, 0)


def normalize_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(c in value for c in "\r\n"):
        raise AppError("이름은 비어 있거나 줄바꿈을 포함할 수 없습니다.")
    return value.strip()


def validate_category(value: str, registered: Iterable[Category]) -> str:
    name = normalize_name(value)
    for category in registered:
        if category.name.casefold() == name.casefold():
            return category.name
    raise AppError(f"미등록 카테고리: {name}", "category add로 먼저 등록하세요.", 3)


def validate_month(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}", value):
        raise AppError(f"잘못된 월: {value}", "YYYY-MM을 입력하세요.")
    validate_date(value + "-01")
    return value


def normalize_tags(value: str | list[str]) -> list[str]:
    parts = value.split(",") if isinstance(value, str) else value
    if not isinstance(parts, list) or any(not isinstance(p, str) or "," in p for p in parts):
        raise AppError("태그는 쉼표 구분 문자열 또는 쉼표 없는 문자열 목록이어야 합니다.")
    seen, result = set(), []
    for part in parts:
        name = part.strip()
        if name and name.casefold() not in seen:
            seen.add(name.casefold())
            result.append(name)
    return result


def id_number(value: str) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"TX-[0-9]{6,}", value) or int(value[3:]) < 1:
        raise AppError(f"잘못된 거래 ID: {value}")
    number = int(value[3:])
    if value != f"TX-{number:06d}":
        raise AppError(f"정규 형식이 아닌 거래 ID: {value}")
    return number


def validate_period(start=None, end=None):
    start = validate_date(start) if start is not None else None
    end = validate_date(end) if end is not None else None
    if start and end and start > end:
        raise AppError("시작일이 종료일보다 늦습니다.")
    return start, end
