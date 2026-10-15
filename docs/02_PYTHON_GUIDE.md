# 02. Python 핵심 개념

예제는 개념 설명용입니다. 별도 연습 파일에서 실행하고 값을 바꿔 본 뒤 구현 실습에 연결하세요. 예제들을 모두 합쳐도 완성 프로그램이 되지는 않습니다.

## 1. 입력·정수·조건·함수

```python
def parse_amount(text: str) -> int:
    amount = int(text.strip())
    if amount <= 0:
        raise ValueError("금액은 양수 정수여야 합니다.")
    return amount

amount = parse_amount(input("금액: "))
print(f"입력 금액: {amount:,}원")
```

`input()`은 문자열을 반환하고 `strip()`은 앞뒤 공백을 없앱니다. `int()`는 정수로 바꿉니다. `int('abc')`는 `ValueError`를 발생시키지만 0과 음수는 별도 조건으로 막아야 합니다. `return`은 함수 결과를 돌려줍니다.

`text: str`, `-> int`는 타입 힌트입니다. 계약을 설명하지만 실행 중 자동 검증을 해 주지는 않습니다.

**연습:** `8000`, `0`, `-1`, `abc`를 각각 넣어 결과를 설명하세요.

## 2. 리스트·딕셔너리·반복

```python
transactions = [
    {"type": "income", "amount": 20000},
    {"type": "expense", "amount": 5000},
    {"type": "expense", "amount": 1500},
]
expense = 0
for item in transactions:
    if item["type"] == "expense":
        expense += item["amount"]
print(expense)  # 6500
```

딕셔너리는 한 거래, 리스트는 여러 거래를 담습니다. `item['amount']`는 없는 키에 `KeyError`가 납니다. `item.get('memo', '')`는 키가 없을 때 빈 문자열을 반환하며, 키를 새로 저장하지 않습니다.

태그 입력은 다음처럼 처리할 수 있습니다.

```python
text = "점심, 외식, "
tags = [part.strip() for part in text.split(",") if part.strip()]
print(tags)  # ['점심', '외식']
```

**연습:** 수입 합계와 잔액도 계산하세요. 잔액은 13,500원입니다.

## 3. 날짜 검증

```python
from datetime import date

def parse_date(text: str) -> str:
    value = date.fromisoformat(text)
    if value.isoformat() != text:
        raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다.")
    return text
```

존재하지 않는 날짜는 `fromisoformat()`이 거부합니다. 다시 문자열로 바꿔 비교하면 정확한 표기도 확인합니다. 월은 길이 7과 하이픈 위치를 확인한 뒤 `parse_date(month + '-01')`로 검사할 수 있습니다.

**연습:** `2024-02-29`는 통과하고 `2025-02-29`, `2024-13-01`, `20240101`은 거부되는지 확인하세요.

## 4. dataclass와 클래스

```python
from dataclasses import dataclass, field, asdict

@dataclass
class Transaction:
    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)

transaction = Transaction("demo-1", "expense", "2024-01-15", 5000, "food")
print(asdict(transaction))
```

`dataclass`는 초기화 메서드 등을 만들어 줍니다. 날짜·금액 검증은 별도로 구현합니다. `default_factory=list`는 거래마다 별도의 태그 리스트를 만듭니다.

두 번째 클래스는 파일 작업을 맡는 `TransactionRepository`로 설계하세요. 모델이 `input()`을 호출하거나 저장소가 화면을 출력하지 않게 역할을 나눕니다.

## 5. 경로·파일·JSONL

```python
import json
from pathlib import Path

path = Path("practice") / "transactions.jsonl"
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(asdict(transaction), ensure_ascii=False) + "\n")
```

`a`는 끝에 추가하고 `w`는 기존 내용을 지웁니다. `with`는 파일을 자동으로 닫습니다. `json.dumps()`는 파이썬 값을 JSON 문자열로, `json.loads()`는 문자열을 파이썬 값으로 바꿉니다. `ensure_ascii=False`는 한글을 읽을 수 있게 저장합니다.

JSON 문법이 맞더라도 필드가 없거나 금액이 문자열일 수 있습니다. 파일에서 읽은 값도 모델 검증을 거쳐야 합니다.

## 6. yield와 스트리밍

```python
def iter_records(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}의 {line_number}행 JSON 오류") from error
```

`yield`를 포함한 함수는 제너레이터를 만듭니다. 반복문이 다음 값을 요구할 때 실행을 이어 갑니다. 파일을 한 줄씩 읽으므로 전체 파일을 리스트에 담지 않습니다.

그러나 `list(iter_records(path))`나 `sorted(iter_records(path))`는 전체를 메모리에 올립니다. 제너레이터 함수가 있다는 것만으로 모든 후속 처리가 스트리밍이 되는 것은 아닙니다.

실제 구현에서는 각 딕셔너리를 Transaction으로 변환하고 필드도 검사하세요. 손상 행을 조용히 건너뛰면 나중에 재작성할 때 데이터가 사라질 수 있으므로 오류로 중단합니다.

## 7. 정렬 기준 함수

```python
rows = [{"date": "2024-01-02"}, {"date": "2024-01-15"}]
latest = sorted(rows, key=lambda item: item["date"], reverse=True)
print(latest[0])
```

`key`에는 비교 값을 꺼내는 함수를 전달합니다. `lambda item: item['date']`는 날짜를 반환하는 짧은 함수이며 정렬 자체는 `sorted()`가 합니다. 정확한 ISO 날짜는 문자열로 정렬해도 날짜순입니다.

위 코드는 작은 리스트 연습용입니다. 과제의 목록·검색은 임의 순서로 저장된 파일에서도 최신순이어야 하므로 구현 실습에서는 임시 디스크 정렬을 사용합니다.

## 8. 임시 파일로 안전하게 수정하기

```python
import os
from tempfile import NamedTemporaryFile

def write_records(path: Path, records) -> None:
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8",
                                dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            for record in records:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
```

부모 폴더는 먼저 만들어 두어야 합니다. 원본과 같은 디렉터리에 임시 파일을 만들고 닫은 후 교체합니다. `records`를 읽거나 쓰는 중 오류가 나면 교체하지 않으므로 원본이 남습니다.

수정·삭제는 여기에 **대상 ID 발견 여부 검사**를 추가해야 합니다. 모든 행을 검증하고 대상까지 확인한 뒤에만 교체하세요. 동시 실행과 정전 복구까지 보장하는 코드는 아니며, 실습은 단일 프로세스 실행을 가정합니다.

## 9. 데코레이터와 종료 코드

```python
import sys
from functools import wraps

def handle_errors(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (ValueError, OSError) as error:
            print(f"[오류] {error}", file=sys.stderr)
            print("[힌트] 입력 형식과 경로·권한을 확인하세요.", file=sys.stderr)
            return 1
    return wrapper

@handle_errors
def main() -> int:
    parse_amount("0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

데코레이터는 함수를 받아 공통 동작으로 감싼 새 함수를 반환합니다. `@handle_errors`는 `main = handle_errors(main)`과 같은 의미입니다. `wraps`는 원래 함수의 이름과 문서 정보를 유지합니다.

실제 구현에서는 사용자용 `AppError`에 원인과 구체적인 힌트를 담으면 좋습니다. 저장 파일·입력 문제는 경계에서 이 예외로 변환합니다. 모든 예외를 무조건 잡으면 개발 중 버그를 숨길 수 있습니다.

## 10. argparse와 CSV

```python
import argparse

parser = argparse.ArgumentParser()
commands = parser.add_subparsers(dest="command", required=True)
listing = commands.add_parser("list")
listing.add_argument("--limit", type=int, default=10)
args = parser.parse_args(["list", "--limit", "3"])
print(args.limit)  # 3
```

실제 CLI는 `parse_args()`의 인자를 생략해 터미널 입력을 읽습니다. 서브파서에 옵션을 등록하면 도움말도 생성됩니다. 음수 limit은 정수이므로 별도 범위 검사가 필요합니다.

```python
import csv

with open("examples/transactions.csv", encoding="utf-8", newline="") as stream:
    for row in csv.DictReader(stream):
        print(row["date"], parse_amount(row["amount"]))
```

`DictReader`는 헤더를 키로 사용합니다. `DictWriter`는 지정한 필드 순서로 `writeheader()`와 `writerow()`를 실행합니다. `newline=''`는 줄바꿈 처리를 CSV 모듈에 맡깁니다. 가져올 때 필수 헤더와 각 행의 값을 모두 검사하세요.

## 이해 확인

- 문자열과 정수, 딕셔너리와 JSON 문자열을 구분할 수 있나요?
- `return`과 `yield`, 함수 호출과 함수 전달의 차이를 설명할 수 있나요?
- 임시 파일 작성 중 오류가 나면 원본이 왜 유지되는지 설명할 수 있나요?
- 타입 힌트와 실제 값 검증의 역할을 구분할 수 있나요?
