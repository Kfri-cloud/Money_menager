# 5일차 학습 CSV와 오류 처리를 마치고 제출 점검하기

오늘은 어제까지 만든 기능을 **하나의 실행 가능한 프로그램**으로 마무리한다. `import`와 `export`를 붙이고, 잘못된 입력에서도 알기 쉬운 안내가 나오는지 확인한다. 아래 코드 예시는 3일차의 `read_transactions`와 `save_transactions`를 사용한다. 마지막에는 [5일 진행 지표](FIVE_DAY_PROGRESS.md)의 PDF 요구사항 표를 전부 확인한다.

**오늘의 결과:** 새 폴더에서 `python -m budget_app --help`를 시작으로 10개 기능을 시연하고, README만 보고 다시 실행할 수 있다.

## 1단계 CSV 내보내기와 가져오기

CSV는 첫 줄에 열 이름이 있는 표 파일이다. 파이썬 기본 도구 `csv.DictWriter`와 `csv.DictReader`를 쓴다. 열 순서는 다음과 같이 고정한다.

```text
date,type,category,amount,memo,tags
```

`export --out export.csv --month 2026-09`는 해당 월 거래만 쓴다. `--from 2026-09-02 --to 2026-09-03`처럼 날짜 구간을 주어도 된다. 모든 날짜 조건은 시작일과 끝일을 **포함**한다. 내보낸 파일은 UTF-8, 헤더 포함, 거래 건수 출력이 필요하다.

`import --from import.csv`는 각 행의 날짜·종류·등록된 카테고리·양의 정수 금액을 확인하고 저장한다. `memo`와 `tags`는 빈 값도 허용한다. 화면에 `가져옴 N건, 건너뜀 M건`처럼 결과를 보여준다. 같은 CSV를 다시 가져올 때 중복 거래를 어떻게 처리할지 정하고 README에 적는다. 안전하게 시험하려면 **거래가 없는 테스트용 data 폴더**에서 시작하고, 가져올 CSV에서 사용하는 카테고리는 먼저 등록한다.

**왕복 확인:** 4일차의 거래 4건을 내보낸다. 다른 테스트 폴더에 `용돈`, `간식`, `교통` 카테고리를 등록하고 거래 4건을 가져온다. 목록에서 4건과 금액 합계 6,500원 지출을 확인한다. `id`는 가져오면서 새로 만들어도 된다.

아래 예시에서 `transactions_path`는 `data/transactions.jsonl`, `categories`는 등록된 카테고리 이름의 집합이다. 내보내기는 거래를 한 줄씩 읽어 CSV에 쓴다. 가져오기는 필요한 열을 먼저 확인하고, 잘못된 행과 이미 있는 거래를 건너뛴다.

```python
import csv
import uuid
from datetime import date

COLUMNS = ("date", "type", "category", "amount", "memo", "tags")


def export_csv(transactions_path, out_path, month=None):
    count = 0
    with out_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        for row in read_transactions(transactions_path):
            if month and not row["date"].startswith(month + "-"):
                continue
            writer.writerow({name: row.get(name, "") for name in COLUMNS})
            count += 1
    return count


def checked_row(raw, categories):
    day = (raw.get("date") or "").strip()
    if date.fromisoformat(day).isoformat() != day:
        raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다.")
    kind = (raw.get("type") or "").strip()
    category = (raw.get("category") or "").strip()
    amount = int((raw.get("amount") or "").strip())
    if kind not in ("income", "expense") or amount <= 0:
        raise ValueError("종류 또는 금액을 확인하세요.")
    if category not in categories:
        raise ValueError("카테고리를 먼저 등록하세요.")
    return {
        "id": "TX-" + uuid.uuid4().hex,
        "date": day, "type": kind, "category": category,
        "amount": amount, "memo": (raw.get("memo") or "").strip(),
        "tags": (raw.get("tags") or "").strip(),
    }


def import_csv(source_path, transactions_path, categories):
    rows = list(read_transactions(transactions_path))
    def key(row):
        return tuple(str(row.get(name, "")) for name in COLUMNS)
    known = {key(row) for row in rows}
    imported = skipped = 0
    with source_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames or not set(COLUMNS[:4]).issubset(reader.fieldnames):
            raise ValueError("CSV 헤더에 date,type,category,amount가 필요합니다.")
        for line_number, raw in enumerate(reader, start=2):
            try:
                row = checked_row(raw, categories)
            except ValueError as error:
                print(f"{line_number}행 건너뜀: {error}")
                skipped += 1
                continue
            if key(row) in known:
                skipped += 1
                continue
            known.add(key(row))
            rows.append(row)
            imported += 1
    if imported:
        save_transactions(transactions_path, rows)
    return imported, skipped
```

`date.fromisoformat()`이 존재하지 않는 날짜에 내는 `ValueError`도 위 `import_csv`에서 잡아 건너뛴다. 가져오기를 두 번 실행하면 내용이 같은 거래는 두 번째에 건너뛴다. 이 예시는 월별 내보내기만 보여준다. 과제의 `--from`·`--to` 기간 옵션도 추가해야 한다.

## 2단계 잘못된 입력에 안내하기

아래 입력을 각각 시험한다. 오류가 나면 원인과 다시 입력할 예를 알려주고, 실행 결과는 0이 아닌 종료 코드여야 한다. 파이썬 오류의 긴 추적 화면이 사용자에게 보이면 개선한다.

| 시험 입력 | 기대하는 안내 |
| --- | --- |
| `2026-02-30` | 존재하지 않는 날짜, `YYYY-MM-DD` 예시 |
| `type=gift` | `income` 또는 `expense` 입력 안내 |
| `amount=0`, `amount=-1`, `amount=삼천` | 0보다 큰 정수 안내 |
| 없는 카테고리 | 먼저 `category add` 안내 |
| 없는 거래 ID | ID를 찾지 못했다는 안내 |
| 없는 CSV 파일·잘못된 헤더 | 파일 위치 또는 필요한 열 안내 |

2일차의 `int(input(...))`는 잘못된 글자를 입력하면 오류가 났다. 이제는 `try/except ValueError`로 사용자가 이해할 문장을 출력한다. 오류가 난 거래는 저장하지 않았는지 파일과 목록을 다시 확인한다.

다음 데코레이터는 여러 명령에서 생긴 오류를 같은 방식으로 안내할 때 쓸 수 있다. `@friendly_errors`를 명령 처리 함수에 붙여 실제로 적용한다.

```python
import sys
from functools import wraps


def friendly_errors(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (ValueError, OSError) as error:
            print(f"오류: {error}", file=sys.stderr)
            return 1
    return wrapper
```

`@wraps`는 감싼 함수의 이름을 유지한다. 명령 처리 함수의 반환값을 `SystemExit`에 전달해야 `return 1`이 실제 종료 코드가 된다. 틀린 날짜를 넣어 긴 오류 추적 대신 짧은 안내와 0이 아닌 종료 코드를 확인한다.

```text
python -m budget_app export --out day5_export.csv --from 2026-02-30
```

## 3단계 과제의 구조 요구 확인하기

PDF는 기능뿐 아니라 코드 구조도 요구한다. 완성 코드에 다음이 실제로 쓰였는지 확인한다.

```text
budget_app/
    __main__.py   명령 읽기와 화면 출력
    model.py      Transaction 같은 데이터 클래스
    storage.py    파일 읽기와 저장
    service.py    검색과 합계 등 계산
```

- **클래스 2개 이상:** 예를 들어 `Transaction`과 `TransactionRepository`.
- **모듈 3개 이상:** 위 예시는 4개다. 파일만 나누고 아무 기능도 없는 모듈은 세지 않는다.
- **제너레이터:** 거래 파일을 `for line in file`로 한 줄씩 읽으며 `yield`로 거래를 하나씩 넘긴다. `list`와 `search`에서 실제로 사용한다.
- **데코레이터:** 실행 시간 측정, 로그, 또는 공통 오류 처리 중 하나를 함수에 `@...`로 붙여 실제로 사용한다.
- **타입 힌트:** 중요한 함수의 입력과 반환값에 붙인다.
- **안전한 수정·삭제:** 수정한 전체 목록을 임시 파일에 쓴 다음 `os.replace()`로 원본과 교체한다. 쓰는 도중 오류가 나면 원본 기록을 보존한다.

오늘 새 개념을 모두 처음부터 배우기 어렵다면, 어른과 함께 [기본 기능 학습 문서](FEATURE_SPEC.md)의 해당 부분을 하나씩 읽고 실제 코드에서 그 부분을 찾아 설명해 본다. **코드에 이름만 넣은 것은 완료가 아니다.** 실행하며 동작을 확인해야 한다.

문서의 코드 조각은 각 기능을 이해하기 위한 예시다. 과제용 `budget_app`에 합친 뒤, `python -m budget_app` 실행, 카테고리 확인을 `add`에 연결하기, 명령별 도움말과 스트리밍 정렬 등을 마지막으로 점검한다.

## 4단계 사용법과 제출 점검

README에 실제 실행 명령, 데이터 파일 위치·형식, 초기 카테고리 사용법, 10개 명령의 예, CSV 열, 중복 가져오기 규칙, `update` 방식과 카테고리 삭제 방식을 적는다. README의 명령을 **복사해서 실행**해 보고 맞지 않는 설명은 고친다.

```text
python -m budget_app --help
python -m budget_app add
python -m budget_app list --limit 3
python -m budget_app search --category 간식
python -m budget_app summary --month 2026-09 --top 2
python -m budget_app budget set --month 2026-09 --amount 5000
python -m budget_app category list
python -m budget_app update --id <실제_ID> --amount 3500
python -m budget_app delete --id <실제_ID>
python -m budget_app export --out export.csv --month 2026-09
python -m budget_app import --from export.csv
```

각 명령에 `--help`를 붙여 사용법이 나오는지도 확인한다. 프로그램을 종료하고 다시 켠 뒤 거래·카테고리·예산이 남아 있는지 확인한다. 샘플 데이터가 실제 기록과 섞이지 않도록 `--data-dir`을 지원한다면 시험용 폴더를 따로 지정한다.

## 다 했는지 확인하기

- [ ] CSV 내보내기와 가져오기 결과의 건수와 값이 맞다.
- [ ] 잘못된 입력 여섯 종류에서 이해할 만한 안내가 나온다.
- [ ] 10개 기능과 각 도움말이 실제로 실행된다.
- [ ] 파일 3개, 클래스 2개, 모듈 3개, 제너레이터, 데코레이터가 실제 코드에서 쓰인다.
- [ ] README의 실행 예시가 현재 코드와 일치한다.
- [ ] [5일 진행 지표](FIVE_DAY_PROGRESS.md)의 제출 점검표를 근거와 함께 채웠다.

**함께 돕는 어른에게:** 시간이 부족하면 현재 동작과 남은 요구를 진행 지표에 사실대로 기록한다. 모든 칸을 채우려고 작동하지 않는 코드를 덧붙이기보다, 각 기능을 실제 실행해 확인하고 빠진 요구를 분명히 적는다.
