# 4일차 학습 원하는 거래를 찾고 한 달 돈을 계산하기

3일차에 저장한 거래를 사용한다. 오늘은 `search`, `summary`, `budget`, `category`를 만든다. 새 거래를 만들기보다 **이미 있는 데이터를 골라 보고 계산하는 날**이다. 아래 코드 예시는 3일차에 만든 파일 읽기·저장 함수를 사용한다.

**오늘의 결과:** 날짜·분류 같은 조건으로 거래를 찾고, 한 달의 수입·지출·잔액과 예산 사용률을 설명할 수 있다.

## 1단계 연습 데이터 준비하기

아래 네 건을 실제 프로그램에 입력한다. `간식`과 `교통`은 먼저 카테고리로 등록한다. 3일차 코드에서 카테고리 확인을 아직 하지 않았다면 오늘 등록 기능을 만든 뒤 입력한다.

| 날짜 | 종류 | 분류 | 금액 | 메모 | 태그 |
| --- | --- | --- | ---: | --- | --- |
| 2026-09-01 | income | 용돈 | 20000 | 9월 용돈 | 정기 |
| 2026-09-02 | expense | 간식 | 3000 | 빵 | 학교 |
| 2026-09-03 | expense | 교통 | 1500 | 버스 | 이동 |
| 2026-09-10 | expense | 간식 | 2000 | 우유 | 학교 |

`용돈`도 카테고리로 등록한다. 입력 후 목록에서 네 건이 보이는지 확인한다.

`category add` 기능을 만든 뒤 `용돈`, `간식`, `교통`을 등록한다. 그런 다음 3일차의 `add`로 표의 거래를 네 번 입력한다.

## 2단계 검색하기

`search`는 조건이 없는 거래는 통과시키고, 조건이 있는 거래만 비교한다. 날짜는 `YYYY-MM-DD` 형식이면 글자 순서가 날짜 순서와 같다. 날짜 형식이 올바른지는 따로 검사해야 한다.

```python
def matches(transaction, from_date=None, to_date=None,
            category=None, kind=None, keyword=None, tag=None):
    if from_date and transaction["date"] < from_date:
        return False
    if to_date and transaction["date"] > to_date:
        return False
    if category and transaction["category"] != category:
        return False
    if kind and transaction["type"] != kind:
        return False
    if keyword and keyword not in transaction.get("memo", ""):
        return False
    tags = [item.strip() for item in transaction.get("tags", "").split(",")]
    if tag and tag not in tags:
        return False
    return True
```

`--category 간식`은 2건, `--type expense`는 3건, `--q 빵`은 1건, `--tag 학교`는 2건이어야 한다. 여러 조건을 함께 주면 **모두 맞는 거래만** 보여준다. 검색 조건의 날짜도 실제 존재하는 날짜인지 검사한다. 최신순 정렬을 위해 결과 전체를 메모리에 모으는 구현은 PDF의 대용량 스트리밍 요구를 만족하지 않으므로 제출 코드에서 보완한다.

## 3단계 월별 요약 계산하기

`2026-09`로 시작하는 거래만 모아 계산한다.

- 총수입: 20,000원
- 총지출: 6,500원 (`3000 + 1500 + 2000`)
- 잔액: 13,500원 (`20000 - 6500`)
- 지출 카테고리: 간식 5,000원, 교통 1,500원

수입을 지출 카테고리 TOP N에 섞지 않는다. `--top 1`이면 `간식 5,000원`만 나온다. 거래가 없는 달은 `데이터 없음`이라고 분명히 알린다.

다음 함수는 전달받은 거래 중 해당 월만 계산한다. 반환값을 화면에 출력하는 부분은 CLI에서 작성한다.

```python
from collections import defaultdict


def summarize(transactions, month, top=3):
    rows = [row for row in transactions if row["date"].startswith(month + "-")]
    if not rows:
        return None
    income = sum(row["amount"] for row in rows if row["type"] == "income")
    expense = sum(row["amount"] for row in rows if row["type"] == "expense")
    categories = defaultdict(int)
    for row in rows:
        if row["type"] == "expense":
            categories[row["category"]] += row["amount"]
    leaders = sorted(categories.items(), key=lambda item: -item[1])[:top]
    return income, expense, income - expense, leaders
```

## 4단계 예산과 카테고리 다루기

`budget set --month 2026-09 --amount 5000`으로 예산을 저장한다. 9월 지출 6,500원이므로 사용률은 `130.0%`이고 **예산 초과**라고 알려야 한다. 저장한 예산은 재실행 후에도 `summary`에서 보여야 한다.

`category add/list/remove`로 분류를 추가·조회·삭제한다. 이미 거래에서 사용 중인 `간식`은 삭제를 막거나 대체 분류를 요청한다. 어느 방법을 택했는지 README에 적는다. 분류가 없는 거래를 새로 추가하지 않도록 `add`에도 등록 여부 확인을 연결한다.

예산과 카테고리도 거래와 **다른 파일**에 저장한다. 아래는 3일차의 읽기·저장 함수를 재사용하는 예시다. `categories_path`와 `budgets_path`는 각각 `data/categories.jsonl`, `data/budgets.jsonl`을 가리킨다.

```python
def add_category(categories_path, name):
    name = name.strip()
    if not name:
        raise ValueError("카테고리 이름을 입력하세요.")
    rows = list(read_transactions(categories_path))
    if any(row["name"] == name for row in rows):
        raise ValueError("이미 있는 카테고리입니다.")
    rows.append({"name": name})
    save_transactions(categories_path, rows)


def set_budget(budgets_path, month, amount):
    if amount <= 0:
        raise ValueError("예산은 0보다 커야 합니다.")
    rows = [row for row in read_transactions(budgets_path)
            if row["month"] != month]
    rows.append({"month": month, "amount": amount})
    save_transactions(budgets_path, rows)


def remove_category(categories_path, transactions_path, name):
    if any(row["category"] == name for row in read_transactions(transactions_path)):
        raise ValueError("사용 중인 카테고리는 삭제할 수 없습니다.")
    rows = [row for row in read_transactions(categories_path)
            if row["name"] != name]
    save_transactions(categories_path, rows)
```

요약에서 예산 사용률은 `expense / budget_amount * 100`으로 계산한다. 예산 금액이 0이면 안 되며, 계산할 월의 형식도 검사한다. `remove_category`에서 이름이 없을 때 안내하는 처리도 추가한다.

## 오늘의 확인 실험

작성한 `budget_app`에서 아래 명령을 실행한다.

```text
python -m budget_app search --category 간식
python -m budget_app search --from 2026-09-02 --to 2026-09-03
python -m budget_app summary --month 2026-09 --top 1
python -m budget_app budget set --month 2026-09 --amount 5000
python -m budget_app category list
```

첫 검색은 2건, 기간 검색은 2건이다. 예산을 저장한 뒤 요약을 다시 실행하면 130.0%와 초과 안내가 나와야 한다. 날짜, 금액, 카테고리를 바꾸어도 결과가 맞는지 확인한다.

## 다 했는지 확인하기

- [ ] 기간·분류·종류·메모·태그로 검색할 수 있다.
- [ ] 검색 결과가 최신순이고 조건을 함께 적용할 수 있다.
- [ ] 9월 예시의 수입 20,000원, 지출 6,500원, 잔액 13,500원이 맞다.
- [ ] 예산 5,000원에 사용률 130.0%와 초과 안내가 나온다.
- [ ] 사용 중인 카테고리를 지울 때 안전하게 처리한다.

**함께 돕는 어른에게:** 아이가 계산한 숫자와 프로그램 출력을 먼저 손으로 비교하게 한다. 기능을 실행할 때마다 터미널 결과를 진행표에 기록하면 무엇이 완성됐는지 분명해진다.
