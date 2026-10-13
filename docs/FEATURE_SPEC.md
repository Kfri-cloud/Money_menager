# 용돈 기입장을 만들 때 공부할 파이썬 기본 기능

여기에 나오는 함수와 도구는 파이썬에서 기본으로 제공한다. 별도 설치는 필요 없다.

- **내장 함수**: `input()`, `print()`처럼 바로 사용할 수 있다.
- **메서드**: `문자열.strip()`, `리스트.append()`처럼 특정 값 뒤에 붙여 사용한다.
- **표준 라이브러리**: `json`, `csv`처럼 `import`해서 사용한다.
- `if`, `for`, `with`, `try`, `yield`는 함수가 아니라 파이썬 문법이다.

## 1. 입력과 출력: input(), print(), int()

`input()`은 사용자에게 입력받고, `print()`는 화면에 출력한다.
입력 결과는 항상 문자열이므로 금액을 계산하려면 `int()`로 정수로 바꾼다.

```python
memo = input("메모: ")
amount = int(input("금액: "))
print(memo, amount)
print(f"금액: {amount:,}원")  # 15000이면 금액: 15,000원
```

`int("15000")`은 가능하지만 `int("15,000")`, `int("안녕")`은 오류가 난다.
마지막 줄의 `f"..."`는 문자열 안에 값을 넣는 문법이다.

## 2. 문자열 다루기: strip(), split(), lower()

| 메서드 | 역할 | 예시와 결과 |
| --- | --- | --- |
| `strip()` | 앞뒤 공백 제거 | `" 식비 ".strip()` → `"식비"` |
| `split(",")` | 쉼표 기준으로 나눠 리스트 만들기 | `"점심,외식".split(",")` → `["점심", "외식"]` |
| `lower()` | 영문을 소문자로 바꾸기 | `"EXPENSE".lower()` → `"expense"` |

메모 검색에는 `in`을 쓴다. 이것은 함수가 아니라 포함 여부를 검사하는 연산자다.

```python
memo = "친구와 점심"
print("점심" in memo)  # True
```

## 3. 거래 여러 개 다루기: append(), len(), get()

거래 한 건은 딕셔너리로, 여러 건은 리스트로 표현할 수 있다.

```python
transactions = []
transaction = {"id": "001", "category": "식비", "amount": 8000}

transactions.append(transaction)  # 리스트에 한 건 추가
print(len(transactions))           # 개수: 1
print(transaction["amount"])       # 금액: 8000
print(transaction.get("memo", "")) # memo가 없으면 빈 문자열
```

`append()`는 리스트 메서드, `get()`은 딕셔너리 메서드, `len()`은 내장 함수다.
`transaction["amount"] = 9000`처럼 값을 바꾸면 메모리 안의 거래가 수정된다. 파일에 반영하려면 다시 저장해야 한다.

### get() 자세히 알아보기

`get()`은 **딕셔너리에서 키에 해당하는 값을 가져오는 메서드**다.
딕셔너리는 `키: 값` 형태로 데이터를 저장한다. 아래에서 `"category"`와 `"amount"`는 키이고, `"식비"`와 `8000`은 각각의 값이다.

```python
transaction = {"category": "식비", "amount": 8000}

print(transaction.get("amount"))        # 8000
print(transaction.get("memo"))          # None
print(transaction.get("memo", "없음"))  # 없음
```

사용법은 `딕셔너리.get(찾을 키, 키가 없을 때 반환할 기본값)`이다. 두 번째 인자는 생략할 수 있다.

| 호출 | 처리 과정 | 반환값 |
| --- | --- | --- |
| `transaction.get("amount")` | `"amount"`라는 키가 있으므로 저장된 값을 가져온다. | `8000` |
| `transaction.get("memo")` | `"memo"`라는 키가 없고 기본값도 지정하지 않았다. | `None` |
| `transaction.get("memo", "없음")` | `"memo"`라는 키가 없으므로 지정한 기본값을 사용한다. | `"없음"` |

`None`은 값이 없음을 나타내는 파이썬 값이다. 문자열 `"None"`이나 빈 문자열 `""`, 숫자 `0`과는 다르다.
`get()`은 값을 반환하고, 위 코드에서는 `print()`가 그 값을 화면에 출력한다. 반환값을 변수에 담을 수도 있다.

```python
amount = transaction.get("amount")
print(amount + 1000)  # 9000
```

**대괄호 `[]`와의 차이:** 키가 있을 때는 둘 다 같은 값을 가져오지만, 키가 없으면 동작이 다르다.

```python
print(transaction["amount"])      # 8000
print(transaction.get("amount"))  # 8000

print(transaction.get("memo"))    # None: 오류 없이 반환
# print(transaction["memo"])      # 실행하면 KeyError: 없는 키라서 오류
```

**기본값은 키가 없을 때만 사용한다.** 키가 있으면 저장된 값이 `None`, `""`, `0`이어도 그 값을 그대로 반환한다.

```python
transaction["memo"] = "점심"
print(transaction.get("memo", "없음"))  # 점심

transaction["memo"] = None
print(transaction.get("memo", "없음"))  # None
```

또한 `get()`으로 기본값을 가져와도 딕셔너리에 새 항목이 저장되지는 않는다.

```python
transaction = {"category": "식비", "amount": 8000}
memo = transaction.get("memo", "없음")

print(memo)                   # 없음
print("memo" in transaction)  # False: memo 키는 여전히 없음

transaction["memo"] = "점심"  # 실제로 저장하려면 이렇게 대입한다.
```

## 4. 합계와 정렬: sum(), sorted()

```python
transactions = [
    {"date": "2026-09-01", "amount": 8000},
    {"date": "2026-09-03", "amount": 5000},
]

total = sum(item["amount"] for item in transactions)
print(total)  # 13000

latest = sorted(transactions, key=lambda item: item["date"], reverse=True)
print(latest[:1])  # 최신 거래 1개
```

- `sum()`: 숫자들을 더한다. 월별 수입·지출 합계에 사용한다.
- `sorted()`: 정렬한 새 리스트를 반환한다. `reverse=True`는 내림차순이다.
- `key=lambda item: item["date"]`: 각 거래의 날짜를 기준으로 정렬하라는 뜻이다.
- `[:1]`: 앞에서 1개만 가져오는 슬라이싱 문법이다.

날짜가 모두 `YYYY-MM-DD` 형식이면 문자열로 정렬해도 날짜순이 된다.
위 예시는 작은 리스트를 연습하는 코드다. `sorted()`는 전체 결과를 메모리에 담으므로 대용량 파일을 한 줄씩 처리하는 것과는 차이가 있다.

### lambda와 정렬 기준 key 자세히 알아보기

`lambda`는 **짧은 함수를 만드는 파이썬 문법**이다. 원래 있는 함수를 호출하는 것이 아니라, 이 문법으로 직접 함수를 만든다.

기본 형태는 `lambda 매개변수: 반환할 표현식`이다. 매개변수는 함수가 받은 값을 담는 이름이고, `:` 뒤의 계산 결과가 반환값이 된다. `return`을 따로 쓰지 않는다.

먼저 일반 함수를 보면 다음과 같다.

```python
def double(number):
    return number * 2

print(double(3))  # 6
```

위 함수와 같은 계산을 하는 함수를 `lambda`로 만들 수도 있다. 아래 대입은 동작을 비교하기 위한 예시다. 이름을 붙여 계속 사용할 함수는 위처럼 `def`로 쓰면 읽기 쉽다.

```python
double = lambda number: number * 2
print(double(3))  # 6
```

여기서 `number`에는 `3`이 들어오고, `number * 2`의 결과인 `6`이 반환된다. `lambda` 안에는 하나의 표현식을 쓰므로 여러 문장이 필요한 함수는 `def`로 작성한다.

#### 거래 날짜를 꺼내는 함수

```python
def get_date(item):
    return item["date"]

transaction = {"date": "2026-09-01", "amount": 8000}
print(get_date(transaction))  # 2026-09-01
```

`item`은 거래 딕셔너리 한 개를 받는 매개변수다. 파이썬에서 정해 놓은 이름이 아니므로 `transaction` 등 다른 이름으로 바꿔도 된다.
이 함수의 입력과 반환 부분을 짧게 쓴 것이 `lambda item: item["date"]`다.

#### sorted()의 key에 함수를 전달하기

`sorted()`의 `key`에는 **각 항목에서 비교할 값을 꺼내거나 계산하는 함수**를 전달한다. `key`가 딕셔너리의 키 이름이라는 뜻은 아니다.

```python
transactions = [
    {"date": "2026-09-01", "amount": 8000},
    {"date": "2026-09-03", "amount": 5000},
]

latest = sorted(transactions, key=get_date, reverse=True)
print(latest)
# [{'date': '2026-09-03', 'amount': 5000},
#  {'date': '2026-09-01', 'amount': 8000}]
```

`key=get_date`는 함수 자체를 전달한다. `key=get_date()`처럼 괄호를 붙이면 그 자리에서 함수를 실행하려고 하는데, 여기서는 필요한 `item`을 주지 않아 오류가 난다. `item`을 넣어 호출하는 역할은 `sorted()`가 맡는다.

처리 과정은 다음과 같다.

1. `sorted()`가 첫 거래를 `get_date()`에 전달해 `"2026-09-01"`을 얻는다.
2. 두 번째 거래에서도 같은 방법으로 `"2026-09-03"`을 얻는다.
3. 꺼낸 날짜들을 비교해 거래들의 순서를 정한다. `reverse=True`이므로 더 늦은 날짜가 먼저 온다.
4. 날짜만 담는 것이 아니라 **거래 딕셔너리 전체를 정렬한 새 리스트**를 반환한다. 원래 리스트의 순서는 그대로다.

별도의 `get_date()` 함수를 정의하지 않고 그 자리에 짧은 함수를 만들면 다음과 같다. 두 코드는 같은 기준으로 정렬한다.

```python
latest = sorted(transactions, key=lambda item: item["date"], reverse=True)
```

`lambda`가 정렬을 하는 것은 아니다. `lambda`로 만든 함수는 날짜를 꺼내 주고, 정렬은 `sorted()`가 한다.

기준을 금액으로 바꾸려면 반환하는 값만 바꾸면 된다.

```python
by_amount = sorted(transactions, key=lambda item: item["amount"], reverse=True)
# 8000원 거래 → 5000원 거래 순서
```

## 5. 파일 읽기와 쓰기: open(), write()

`open()`은 파일을 연다. `with`를 함께 쓰면 작업이 끝났을 때 자동으로 닫힌다.

```python
with open("practice.txt", "a", encoding="utf-8") as file:
    file.write("식비 8000원\n")

with open("practice.txt", "r", encoding="utf-8") as file:
    for line in file:
        print(line.strip())
```

| 모드 | 의미 |
| --- | --- |
| `"r"` | 읽기. 파일이 없으면 오류 |
| `"w"` | 쓰기. 기존 파일이 있으면 내용을 지우고 새로 씀 |
| `"a"` | 기존 내용 뒤에 추가. 파일이 없으면 생성 |

`write()`는 열린 파일 객체의 메서드다. `\n`은 줄바꿈이다.
`for line in file`은 파일을 한 줄씩 읽는다.

## 6. 거래를 파일에 저장하기: json.dumps(), json.loads()

`json`은 딕셔너리 같은 데이터를 문자열로 바꾸거나 다시 복원하는 표준 라이브러리다.

```python
import json

transaction = {"category": "식비", "amount": 8000}
text = json.dumps(transaction, ensure_ascii=False)
print(text)  # {"category": "식비", "amount": 8000}

restored = json.loads(text)
print(restored["amount"])  # 8000
```

- `json.dumps()`: 파이썬 데이터를 JSON 문자열로 변환한다.
- `json.loads()`: JSON 문자열을 파이썬 데이터로 변환한다.
- `ensure_ascii=False`: 한글이 읽을 수 있는 형태로 나오게 한다.

JSONL은 JSON 한 건을 한 줄에 저장하는 형식이다. 다음처럼 사용할 수 있다.

```python
with open("practice.jsonl", "a", encoding="utf-8") as file:
    file.write(json.dumps(transaction, ensure_ascii=False) + "\n")
```

## 7. CSV 가져오기와 내보내기: csv.DictReader(), csv.DictWriter()

이 둘은 표준 라이브러리 `csv`에서 제공하는 클래스다. 괄호로 호출해서 읽기/쓰기 객체를 만든다.

```python
import csv

with open("practice.csv", "w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=["date", "type", "category", "amount", "memo", "tags"])
    writer.writeheader()  # 열 이름 쓰기
    writer.writerow({
        "date": "2026-09-01", "type": "expense",
        "category": "식비", "amount": 8000, "memo": "점심", "tags": "외식,점심",
    })

with open("practice.csv", "r", encoding="utf-8", newline="") as file:
    for row in csv.DictReader(file):
        print(row["category"], int(row["amount"]))
```

`DictReader`는 첫 줄의 열 이름을 이용해 각 행을 딕셔너리로 읽는다.
읽은 값은 문자열이므로 금액은 `int()`로 변환한다.
`writeheader()`와 `writerow()`는 쓰기 객체의 메서드다. CSV 안의 쉼표 처리는 라이브러리가 해준다.

## 8. 날짜 검사: datetime.strptime()

```python
from datetime import datetime

date_value = datetime.strptime("2026-09-28", "%Y-%m-%d").date()
print(date_value.year)   # 2026
print(date_value.month)  # 9
```

`%Y`는 연도, `%m`은 월, `%d`는 일이다.
`strptime()`은 지정한 형식으로 날짜를 해석하며 `2026-02-30`처럼 존재하지 않는 날짜에는 오류를 낸다.
월·일에 반드시 두 자리를 입력하게 하려면 입력 길이와 형식도 따로 확인해야 한다.

## 9. 그다음 공부할 표준 라이브러리

| 제공되는 도구 | 이 과제에서 쓰는 곳 |
| --- | --- |
| `argparse.ArgumentParser()`, `add_argument()`, `parse_args()` | `--limit 10` 같은 명령줄 옵션을 읽고 도움말 만들기 |
| `pathlib.Path`, `Path.exists()`, `Path.mkdir()` | 저장 경로를 다루고 파일 존재 여부 확인, 폴더 만들기 |
| `uuid.uuid4()` | 거래 ID로 쓸 무작위 UUID 생성. 문자열로 쓰려면 `str(uuid.uuid4())` |
| `collections.defaultdict(int)` | 카테고리별 지출 합계 누적 |
| `dataclasses.dataclass` | 거래 데이터를 담는 클래스를 편하게 정의하는 데코레이터 |
| `tempfile.NamedTemporaryFile()`, `os.replace()` | 임시 파일에 수정 결과를 쓴 뒤 원본 파일 교체하기 |

## 10. 함께 알아야 할 문법: try/except, yield

`try/except`는 오류를 처리하는 문법이다. 금액을 잘못 입력했을 때 안내하는 데 쓴다.

```python
try:
    amount = int(input("금액: "))
    if amount <= 0:
        print("금액은 0보다 커야 합니다.")
    else:
        print(amount)
except ValueError:
    print("정수로 입력하세요. 예: 8000")
```

`yield`는 데이터를 한 번에 전부 반환하지 않고 하나씩 넘길 때 쓰는 문법이다.
과제의 파일 스트리밍을 구현할 때 공부하면 된다.

처음에는 **입출력 → 문자열 → 리스트·딕셔너리 → 파일 → JSON 또는 CSV** 순서로 위 예제를 실행해 보면 된다.
