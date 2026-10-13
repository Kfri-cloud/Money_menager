# 2일차 학습 거래를 파일에 저장하고 다시 읽기

1일차에는 거래를 입력하고 화면에 보여주었다. 프로그램을 끝내면 그 기록은 사라졌다. 오늘은 기록을 파일에 남겨서 **프로그램을 다시 실행해도 보이게** 만든다.

**예상 시간:** 90~120분. 막히면 한 단계씩 실행하고 결과를 확인한다.

## 오늘의 목표

- 거래 한 건을 `data/transactions.jsonl`에 저장한다.
- 파일에 저장된 거래를 다시 읽어 화면에 보여준다.
- 과제에서 필요한 저장 파일 3개를 만든다: `transactions.jsonl`, `categories.jsonl`, `budgets.jsonl`.

오늘 사용하는 JSONL은 **한 줄에 기록 한 건**을 적는 파일 형식이다. 거래 파일에는 거래 한 건을 한 줄에 쓴다. 카테고리와 예산 파일은 오늘 비어 있어도 된다. 그 안의 내용을 다루는 기능은 뒤에서 만든다.

실습 파일은 `Script/day2_practice.py`로 만든다. 저장소의 맨 위 폴더에서 실행한다.

```text
python Script/day2_practice.py
```

## 1단계 폴더와 파일 준비하기 20분

`pathlib`는 파일과 폴더의 위치를 다루는 파이썬 기본 도구다. 아래 코드를 입력하고 실행한다.

```python
from pathlib import Path

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

for filename in ("transactions.jsonl", "categories.jsonl", "budgets.jsonl"):
    (data_dir / filename).touch(exist_ok=True)

print("저장 폴더:", data_dir)
```

`mkdir()`은 폴더를, `touch()`는 빈 파일을 만든다. `exist_ok=True`는 이미 있어도 오류를 내지 않는다. 실행한 뒤 `data` 폴더와 파일 3개가 생겼는지 직접 확인한다.

## 2단계 거래 한 건 저장하기 25분

먼저 입력 대신 정해진 거래 하나로 파일 쓰기를 연습한다. 아래 코드를 1단계 코드 **아래에** 붙이고 실행한다.

```python
import json

transaction = {
    "date": "2026-09-30",
    "type": "expense",
    "category": "간식",
    "amount": 3000,
}

transaction_file = data_dir / "transactions.jsonl"
with transaction_file.open("a", encoding="utf-8") as file:
    file.write(json.dumps(transaction, ensure_ascii=False) + "\n")

print("저장했어요")
```

`json.dumps()`는 딕셔너리를 파일에 적을 수 있는 글자로 바꾼다. `"a"`는 기존 내용을 지우지 않고 **끝에 추가**한다는 뜻이다. `"\n"`은 다음 거래를 새 줄에 적기 위한 줄바꿈이다. `with`는 파일 사용을 마치면 파일을 닫아 준다.

**확인:** `data/transactions.jsonl`을 열어 한 줄이 생겼는지 본다. 같은 프로그램을 한 번 더 실행하면 같은 거래가 한 줄 더 생긴다. 지금은 추가 저장을 연습하는 중이므로 정상이다.

## 3단계 저장된 거래 읽기 25분

이번에는 파일에서 한 줄씩 읽는다. 아래 코드를 2단계 코드 아래에 붙인다.

```python
with transaction_file.open("r", encoding="utf-8") as file:
    for line in file:
        saved_transaction = json.loads(line)
        print(saved_transaction["date"], saved_transaction["category"], saved_transaction["amount"])
```

`"r"`은 읽기다. `for line in file`은 파일에서 한 줄씩 꺼낸다. `json.loads()`는 그 줄을 다시 딕셔너리로 바꾼다.

**생각해 보기:** 저장할 때는 `dumps`, 읽을 때는 `loads`를 쓴다. 두 이름이 하는 일을 자신의 말로 설명해 본다.

## 4단계 오늘의 작품 만들기 25~40분

2단계의 정해진 거래를 지우고, 1일차처럼 사용자가 입력한 거래를 저장하도록 바꾼다. 입력할 값은 날짜, 종류, 분류, 금액이다. 금액에는 `int()`를 사용한다. 저장한 뒤 파일의 모든 거래를 한 줄씩 보여준다.

1. 첫 실행에서 간식 지출을 입력한다.
2. 프로그램을 종료하고 다시 실행해 용돈 수입을 입력한다.
3. 화면에 **두 거래가 모두** 보이는지 확인한다.

<details>
<summary>막힐 때 펼쳐 보는 예시 코드</summary>

```python
import json
from pathlib import Path

data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
for filename in ("transactions.jsonl", "categories.jsonl", "budgets.jsonl"):
    (data_dir / filename).touch(exist_ok=True)

transaction = {
    "date": input("날짜(YYYY-MM-DD): "),
    "type": input("종류(income/expense): "),
    "category": input("분류: "),
    "amount": int(input("금액: ")),
}

transaction_file = data_dir / "transactions.jsonl"
with transaction_file.open("a", encoding="utf-8") as file:
    file.write(json.dumps(transaction, ensure_ascii=False) + "\n")

print("지금까지 저장한 거래:")
with transaction_file.open("r", encoding="utf-8") as file:
    for line in file:
        saved_transaction = json.loads(line)
        print(saved_transaction["date"], saved_transaction["type"],
              saved_transaction["category"], saved_transaction["amount"], "원")
```

</details>

## 다 했는지 확인하기

- [ ] `data` 폴더에 세 파일이 생겼다.
- [ ] 프로그램을 두 번 실행하고 서로 다른 거래를 입력했다.
- [ ] 두 번째 실행에서도 첫 번째 거래가 보인다.
- [ ] `"a"`와 `"r"`의 차이를 말할 수 있다.
- [ ] 파일을 열어 거래 한 건이 한 줄에 저장된 모습을 봤다.

**시간이 남으면:** 1일차의 `memo`와 `tags`도 거래에 넣어 저장해 본다. 기존 거래에는 두 값이 없을 수 있으므로 읽을 때는 `saved_transaction.get("memo", "")`처럼 기본값을 사용한다.

**함께 돕는 어른에게:** 저장이 안 된 것처럼 보이면 먼저 터미널이 어느 폴더에서 실행 중인지 살펴본다. `Path("data")`는 터미널의 현재 폴더를 기준으로 한다. 오늘은 저장 원리를 익히는 날이다. 잘못된 날짜나 금액을 다루는 코드는 뒤의 오류 처리 단계에서 추가한다.
