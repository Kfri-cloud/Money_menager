# 3일차 학습 거래를 추가하고 고치고 지우기

1~2일차의 실습 코드는 원리를 익히기 위한 것이다. 오늘부터는 제출할 `budget_app/`의 거래 기능을 만든다. 아래 코드 예시를 읽고 함수를 하나씩 직접 작성한다.

**오늘의 결과:** 서로 다른 거래 두 건을 추가하고, 목록에서 찾고, 한 건을 고친 뒤 다른 한 건을 지울 수 있다. 프로그램을 다시 실행해도 결과가 남아야 한다.

## 1단계 저장할 모양 정하기

거래 한 건에 들어갈 이름표를 정한다.

| 이름표 | 예 | 뜻 |
| --- | --- | --- |
| `id` | `TX-01` | 거래를 찾는 고유 이름 |
| `date` | `2026-09-30` | 거래 날짜 |
| `type` | `expense` | `income` 또는 `expense` |
| `category` | `간식` | 등록된 분류 이름 |
| `amount` | `3000` | 0보다 큰 정수 |
| `memo` | `빵` | 없으면 빈 글자 |
| `tags` | `학교,간식` | 없으면 빈 글자 |

2일차에 저장한 거래에는 `id`, `memo`, `tags`가 없을 수 있다. 현재 2일차 실습은 `transaction.jsonl`이라는 단수 파일명을 사용하므로, 과제용 앱에서는 `transactions.jsonl`처럼 이름을 통일한다. 기존 기록을 보존하고 싶다면 파일을 복사해 두고 시험용 저장 폴더를 따로 사용한다.

## 2단계 파일 읽기와 저장을 함수로 묶기

`budget_app/storage.py`에 파일을 읽고 저장하는 함수를 만든다. 다음 예시의 `yield`는 파일에서 거래를 **한 건씩** 넘긴다.

```python
import json
import os


def read_transactions(path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield json.loads(line)


def save_transactions(path, transactions):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        for transaction in transactions:
            file.write(json.dumps(transaction, ensure_ascii=False) + "\n")
    os.replace(temporary, path)
```

`save_transactions`는 먼저 임시 파일에 쓰고 원본과 바꾼다. 한글을 읽기 쉽게 저장하려고 `ensure_ascii=False`를 쓴다. 저장 파일의 위치는 호출할 때 `Path("data/transactions.jsonl")`처럼 전달한다.

## 3단계 네 동작을 하나씩 만들기

`budget_app/service.py`에 거래를 다루는 함수를 만든다. 처음에는 입력과 출력 없이 **받은 값으로 계산하고 결과를 돌려주는 함수**로 작성하면 확인하기 쉽다.

1. `add`: 거래에 고유 `id`를 붙이고 저장한다. 같은 ID를 두 번 쓰지 않는다.
2. `list`: 날짜가 최신인 거래부터 보여준다. 날짜가 같으면 최근 저장한 거래부터 보여준다. `--limit N`은 앞에서 N개만 보여준다.
3. `update`: ID를 찾아 바꿀 값만 수정한 뒤 다시 저장한다.
4. `delete`: ID를 찾아 삭제한 뒤 다시 저장한다.

ID는 `uuid.uuid4()`로 만들어도 된다. 예를 들어 `"TX-" + uuid.uuid4().hex`는 충돌 가능성이 매우 낮은 고유 문자열을 만든다. 예시의 `TX-01`처럼 짧고 순서가 보이는 ID를 원하면 마지막 번호를 안전하게 기억하는 방법을 따로 설계해야 한다.

`update`와 `delete`는 거래가 없는 ID도 받아 본다. 이때 프로그램이 갑자기 끝나지 않고 `해당 ID가 없어요`처럼 알려주어야 한다.

아래는 앞의 `read_transactions`와 `save_transactions`를 사용하는 구현 예시다. 먼저 `add_transaction`만 작성해 확인하고, 나머지를 한 함수씩 추가한다.

```python
import json
import uuid

from .storage import read_transactions, save_transactions


def add_transaction(path, date, kind, category, amount):
    if kind not in ("income", "expense") or amount <= 0:
        raise ValueError("종류 또는 금액을 다시 확인하세요.")
    transaction = {
        "id": "TX-" + uuid.uuid4().hex,
        "date": date, "type": kind, "category": category,
        "amount": amount, "memo": "", "tags": "",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(transaction, ensure_ascii=False) + "\n")
    return transaction["id"]


def list_transactions(path, limit=None):
    rows = list(read_transactions(path))
    rows.sort(key=lambda row: row["date"], reverse=True)
    return rows[:limit] if limit is not None else rows


def update_amount(path, transaction_id, new_amount):
    if new_amount <= 0:
        raise ValueError("금액은 0보다 커야 합니다.")
    rows = list(read_transactions(path))
    for row in rows:
        if row.get("id") == transaction_id:
            row["amount"] = new_amount
            save_transactions(path, rows)
            return True
    return False


def delete_transaction(path, transaction_id):
    rows = list(read_transactions(path))
    remaining = [row for row in rows if row.get("id") != transaction_id]
    if len(remaining) == len(rows):
        return False
    save_transactions(path, remaining)
    return True
```

이 예시의 `list`는 날짜가 같은 거래의 저장 순서를 별도로 정하지 않고, 정렬을 위해 목록 전체를 메모리에 모은다. PDF의 최신순·대용량 처리 조건은 제출 코드에서 추가로 확인한다. 날짜·등록 카테고리 검사와 메모·태그 입력도 뒤에서 붙인다.

## 4단계 명령으로 연결하기

`budget_app/__main__.py`에서 사용자가 `add`, `list`, `update`, `delete` 중 무엇을 원하는지 받아 알맞은 함수를 부른다. 1일차에 배운 `input()`으로 `add`의 값들을 순서대로 받을 수 있다. 최종 실행 형태는 다음과 같다.

```text
python -m budget_app add
python -m budget_app list --limit 2
python -m budget_app update --id <실제로_출력된_ID> --amount 3500
python -m budget_app delete --id <실제로_출력된_ID>
```

`argparse`가 아직 어렵다면 오늘은 명령 이름만 연결하고, `--id`와 `--limit` 옵션은 5일차에 붙여도 된다. 단, **제출할 때는 위 옵션 방식과 각 명령의 `--help`가 동작해야 한다.** `update`는 PDF에서 옵션 방식 또는 대화형 방식 중 하나를 골라 문서에 명확히 적도록 했다. 위 예시는 옵션 방식을 선택한 경우다.

## 오늘의 확인 실험

작성한 `budget_app`에서 위 명령을 순서대로 해 본다. 기존 기록과 구분되는 시험용 저장 폴더를 사용한다.

1. `간식 3000원 지출`, `용돈 10000원 수입`을 추가한다. 화면에 서로 다른 ID 두 개가 나온다.
2. 목록에서 두 건이 보인다. `--limit 1`은 한 건만 보여준다.
3. 간식 거래의 금액을 `3500`으로 고친다. 프로그램을 다시 실행해도 `3500`이다.
4. 용돈 거래를 지운다. 프로그램을 다시 실행해도 다시 나타나지 않는다.
5. 없는 ID로 수정·삭제를 시도한다. 안내 문구가 나오고 기존 기록은 유지된다.

## 다 했는지 확인하기

- [ ] 거래마다 다른 ID가 생긴다.
- [ ] 목록이 최신순이고 개수 제한이 된다.
- [ ] 수정과 삭제 결과가 재실행 후에도 남는다.
- [ ] 없는 ID를 처리한다.
- [ ] `read_transactions`와 저장 함수를 직접 설명할 수 있다.

**함께 돕는 어른에게:** 오늘은 네 동작 중 하나를 완성할 때마다 실행해 보게 한다. 특히 `update`에서 파일 전체를 다시 쓰면 원래 기록이 사라질 수 있으므로 실습 데이터 사본으로 확인한다.
