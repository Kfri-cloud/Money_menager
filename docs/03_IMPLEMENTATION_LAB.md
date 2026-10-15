# 03. 60시간 구현 실습

시간은 학습 계획입니다. 단계의 확인 기준을 통과한 다음 진행하세요. 하루에 몇 단계씩 끝내야 한다는 일정은 아닙니다. 아래 명령은 구현할 프로그램의 사용 예시이며 현재 저장소에서 바로 실행되지는 않습니다.

## 전체 일정

| 단계 | 시간 | 누적 | 결과물 |
| --- | ---: | ---: | --- |
| 1. 입력·기본 문법 | 6 | 6 | 거래 입력과 검증 연습 |
| 2. 모델·패키지 설계 | 6 | 12 | Transaction, 모듈 구조, CLI 뼈대 |
| 3. 파일 저장·거래 추가 | 8 | 20 | 저장소, 초기화, add |
| 4. 목록·검색·스트리밍 | 8 | 28 | 최신순 list/search |
| 5. 수정·삭제 | 7 | 35 | 안전한 파일 재작성 |
| 6. 요약·예산·분류 | 8 | 43 | summary/budget/category |
| 7. CSV·공통 오류 처리 | 9 | 52 | import/export, 데코레이터 |
| 8. 검증·설명·제출 | 8 | 60 | 실행 증거, 제출 README |

## 1단계. 입력과 검증 — 6시간

Python 설명의 1~3절을 실행합니다. 날짜·종류·분류·금액·메모·태그를 `input()`으로 받고 딕셔너리로 묶어 출력하세요.

만들 함수:

```python
def parse_amount(text: str) -> int: ...
def parse_date(text: str) -> str: ...
def parse_month(text: str) -> str: ...
def parse_tags(text: str) -> list[str]: ...
```

종류는 소문자로 정리한 후 `income/expense`에 포함되는지 확인합니다. 날짜와 월은 실제 날짜인지까지 검사합니다. 금액은 소수·쉼표·문자를 거부하고 양수 정수만 받는 정책을 정합니다.

**완료 기준:** 정상 거래 2개를 출력하고, 0·음수·문자 금액, 없는 날짜, 허용되지 않은 종류를 안내할 수 있습니다. 아직 저장하지 않으므로 재실행하면 사라지는 것이 정상입니다.

## 2단계. 모델과 패키지 — 6시간

직접 다음 구조를 만듭니다.

```text
budget_app/
  __init__.py
  __main__.py      # main 실행과 종료 코드 전달
  models.py        # Transaction, 변환과 검증
  repository.py    # 파일 읽기·쓰기·초기화
  service.py       # 거래 규칙·검색·합계·예산·분류
  cli.py           # argparse, input, print
  errors.py        # AppError, 오류 처리 데코레이터
```

데이터 흐름은 `CLI → Service → Repository → 파일`입니다. 파일을 읽을 때는 `파일 → Repository → Transaction 검증 → Service → CLI`로 되돌아옵니다. 검증 함수를 재사용해 입력 경로에 따라 규칙이 달라지지 않게 합니다.

모델에는 고유 ID와 필수 필드를 담고 `to_dict()`와 `from_dict()`를 구현합니다. 저장소는 `Path`를 받아 파일 위치를 정합니다. 서비스는 저장소 객체를 받아 사용합니다.

추천 인터페이스:

```python
class TransactionRepository:
    def iter_transactions(self): ...
    def append(self, transaction: Transaction) -> None: ...
    def update(self, transaction_id: str, changes: dict) -> None: ...
    def delete(self, transaction_id: str) -> None: ...
```

실제 구현에서는 제너레이터 반환형도 `Iterator[Transaction]`으로 표시하세요. 저장소는 화면을 출력하지 않고 오류를 예외로 전달합니다.

`--data-dir`는 최상위 옵션으로 정합니다. 사용 예시는 `python -m budget_app --data-dir ./practice-data list`입니다. 기본값은 `./data`입니다.

**완료 기준:** `python -m budget_app --help`가 동작하고, 클래스 2개 이상·모듈 3개 이상으로 책임을 설명할 수 있습니다.

## 3단계. 저장소와 add — 8시간

1. 데이터 폴더가 없으면 생성합니다.
2. 거래·분류·예산 JSONL 파일을 없을 때만 만듭니다. 기존 파일을 초기화하지 마세요.
3. 카테고리 파일이 비었으면 기본값 `food`, `transport`, `salary`, `etc`를 생성합니다.
4. 거래 파일을 한 줄씩 읽는 제너레이터를 만듭니다. 손상 행에는 파일명·행 번호를 포함한 오류를 냅니다.
5. `add`에서 입력을 받고 검증한 뒤 `uuid.uuid4()`로 ID를 생성합니다.
6. 저장 성공 후 ID를 출력합니다. 실패했는데 성공 메시지가 나오지 않게 합니다.

```text
python -m budget_app add
날짜: 2024-01-15
종류: expense
카테고리: food
금액: 5000
메모: 점심
태그: meal,lunch
[저장 완료] id=<생성된 ID>
```

**완료 기준:** 서로 다른 ID의 거래 2건을 저장하고, 새 프로세스에서 같은 거래를 읽습니다. 잘못된 카테고리의 거래는 저장되지 않습니다.

## 4단계. list/search와 최신순 — 8시간

### 먼저 필터를 구현하기

`matches(transaction, filters)` 함수를 만들어 각 조건을 검사합니다. 기간의 양 끝은 포함하고 `from > to`는 오류로 처리합니다. 종류·카테고리·태그는 정확히 일치, 메모는 부분 문자열 검색으로 정합니다. 메모 대소문자 무시는 선택하되 README에 명시합니다.

조건을 여러 개 지정하면 모두 만족해야 합니다. 조건 없는 search는 전체 조회로 정할 수 있습니다. limit과 top은 양수 정수만 허용하고 기본값을 문서화합니다. 이 실습의 list 기본 limit은 10입니다.

### 임의 저장 순서와 스트리밍을 함께 해결하기

거래를 append하면 과거 날짜를 나중에 입력할 수 있습니다. 단순 파일 역순 읽기는 최신 날짜순을 보장하지 않습니다. `sorted(generator)`도 전체 메모리 적재가 됩니다.

이 실습에서는 `tempfile.TemporaryDirectory()` 안에 **파일 기반 임시 SQLite DB**를 사용합니다. DB는 정렬용 작업 파일이며 원본 저장 형식은 JSONL입니다.

1. `sqlite3.connect(임시DB경로)`로 연결합니다. `:memory:`는 쓰지 않습니다.
2. 테이블에 `sequence INTEGER`, `date TEXT`, `payload TEXT`를 둡니다.
3. JSONL을 한 줄씩 읽고 검증합니다. 검색은 이때 필터를 적용합니다.
4. 해당 거래만 SQL 파라미터로 한 건씩 삽입합니다. payload는 거래 JSON입니다.
5. 삽입이 끝나면 `ORDER BY date DESC, sequence DESC`로 조회합니다. 날짜가 같으면 나중에 저장된 거래가 먼저입니다.
6. list는 `LIMIT ?`에 양수 limit을 바인딩합니다. search는 전체 결과를 커서로 순회합니다.
7. 커서에서 한 건씩 꺼내 Transaction으로 복원하고 `yield`합니다.
8. 순회 종료·예외·조기 종료에서 커넥션과 임시 디렉터리를 닫도록 `try/finally` 또는 컨텍스트 관리자를 사용합니다.

행 전체를 `fetchall()`하거나 `list()`로 바꾸지 마세요. 이 설계는 결과 반환 전 파일 전체를 훑고 디스크 작업을 해야 하므로 첫 결과가 즉시 나오지는 않습니다. 정렬을 위한 비용과 메모리 사용을 구분해서 설명하세요. SQLite의 임시 정렬 저장은 `PRAGMA temp_store=FILE`로 설정할 수 있습니다.

```text
python -m budget_app list --limit 2
python -m budget_app search --from 2024-01-01 --to 2024-01-31 --type expense
python -m budget_app search --category food -q 점심 --tag lunch
```

**완료 기준:** 날짜를 `01-15 → 01-01 → 01-10` 순서로 저장해도 `01-15 → 01-10 → 01-01`로 나옵니다. 여러 검색 조건이 함께 적용되고 파일을 전체 리스트로 변환하지 않습니다.

## 5단계. update/delete — 7시간

update는 옵션형으로 고정합니다.

```text
python -m budget_app update --id <ID> --amount 6000 --memo 저녁
python -m budget_app delete --id <ID>
```

수정 필드는 `--date`, `--type`, `--category`, `--amount`, `--memo`, `--tags`를 제공합니다. ID 자체는 수정하지 않습니다. 옵션이 생략된 필드는 유지합니다. `--memo ""`, `--tags ""`는 값 비우기로 구분하고 수정 필드가 하나도 없으면 오류를 냅니다.

안전한 재작성 절차:

1. 같은 디렉터리에 임시 파일을 만듭니다.
2. 원본을 한 행씩 검증하며 읽습니다.
3. 대상 ID이면 변경 후 전체 모델을 다시 검증하거나, 삭제할 경우 출력에서 제외합니다.
4. 나머지 거래는 그대로 임시 파일에 기록합니다.
5. 끝까지 읽은 뒤 ID 발견 여부를 검사합니다. 없는 ID면 원본을 교체하지 않습니다.
6. 양쪽 파일을 닫고 `os.replace()`로 교체합니다.
7. 성공·실패와 무관하게 남은 임시 파일을 정리합니다.

중복 ID와 손상 행도 오류로 취급하세요. 검증을 통과하기 전 원본을 `w` 모드로 열면 안 됩니다.

**완료 기준:** 수정·삭제가 재실행 후 유지되고, 없는 ID·손상 파일·잘못된 수정값에서는 원본이 유지됩니다.

## 6단계. summary/budget/category — 8시간

월 요약은 제너레이터로 순회하며 수입·지출을 누적하고 `defaultdict(int)`로 지출 카테고리별 합계를 구합니다. 전체 거래 목록을 보관할 필요는 없습니다. TOP N을 구할 때 카테고리 합계만 정렬하세요.

```text
python -m budget_app summary --month 2024-01 --top 3
python -m budget_app budget set --month 2024-01 --amount 5000
python -m budget_app category add
python -m budget_app category list
python -m budget_app category remove
```

예산 금액은 이 실습에서 양수 정수만 허용합니다. 같은 월 재설정은 중복 행 추가가 아니라 갱신입니다. 예산 없음과 지출 0을 구분하세요. 거래가 없는 월은 `데이터 없음`을 출력하되 설정된 예산이 있으면 사용률 0.0%도 표시할 수 있습니다.

분류 이름은 앞뒤 공백을 지우고 빈 이름·중복을 거부합니다. 삭제 시 거래를 순회해 사용 여부를 검사합니다. 사용 중인 분류는 삭제를 거부하고 관련 거래를 먼저 정리하라는 힌트를 출력합니다.

**완료 기준:** 수입 20,000원·지출 6,500원이면 잔액은 13,500원, 예산 5,000원이면 사용률 130.0%와 초과 경고가 나옵니다. 예산·분류는 재실행 후 유지됩니다.

## 7단계. CSV와 데코레이터 — 9시간

### 가져오기 정책

이 실습에서는 **전체 성공 또는 전체 실패**로 정합니다. 잘못된 행을 조용히 건너뛰지 않습니다. 원문이 이 정책까지 강제하는 것은 아닙니다.

1. `DictReader`로 필수 헤더를 확인합니다.
2. 기존 거래를 검증하며 임시 거래 파일에 복사합니다.
3. CSV를 한 행씩 검증하고 새 ID를 붙여 임시 파일에 추가합니다.
4. 오류에 CSV 행 번호를 표시합니다. 오류면 원본을 교체하지 않습니다.
5. 모두 성공하면 임시 파일로 교체하고 imported 건수를 출력합니다.

헤더만 있는 CSV는 0건 성공으로 처리합니다. 중복 가져오기는 새 거래를 추가하는 것으로 정합니다. ID를 CSV에서 복원하지 않으므로 자동 중복 제거를 기대하면 안 됩니다. UTF-8 BOM을 허용하려면 읽기에 `utf-8-sig`를 사용합니다.

### 내보내기 정책

열 순서는 `date,type,category,amount,memo,tags`입니다. 태그 리스트를 쉼표 구분 문자열로 바꾸고 `DictWriter`가 인용 처리하도록 합니다. 선택한 월 또는 시작·종료일 기간을 적용합니다. 월과 기간을 동시에 주면 오류로 처리하고 기간 모드는 양 끝 날짜를 요구합니다.

데이터가 없으면 헤더만 만들고 0건을 출력합니다. 출력 경로가 원본 데이터 파일과 같으면 거부합니다. 임시 파일을 같은 출력 폴더에 만들어 성공 후 교체하면 실패 시 기존 CSV도 보호할 수 있습니다.

```text
python -m budget_app import --from examples/transactions.csv
python -m budget_app export --out january.csv --month 2024-01
python -m budget_app export --out period.csv --from 2024-01-01 --to 2024-01-31
```

### 오류 처리 적용

`AppError`와 이를 처리하는 데코레이터를 구현하고 CLI 진입 함수에 적용합니다. 출력에는 구체적인 원인과 해결 힌트가 있어야 합니다. `SystemExit(main())`로 반환 코드를 프로세스에 전달합니다. `argparse`의 잘못된 옵션은 기본적으로 종료 코드 2를 사용하므로 과제의 오류 종료 조건에 맞습니다.

**완료 기준:** 새 저장 폴더로 CSV를 가져온 후 월 합계가 일치합니다. 중간 행 오류에서 기존 거래가 보존됩니다. 잘못된 날짜·없는 ID·파일 접근 실패가 스택트레이스 없이 안내되고 종료 코드는 0이 아닙니다.

## 8단계. 검증과 제출 — 8시간

[제출 점검표](04_SUBMISSION_CHECKLIST.md)를 실제 명령으로 확인합니다. 새 데이터 폴더와 재실행을 사용해 파일 영구 저장을 입증하세요. 출력·오류·종료 코드를 기록하고 확인하지 않은 항목은 미완료로 남깁니다.

최종 README는 이 학습 안내 대신 실제 프로그램 실행법과 저장 형식을 설명하도록 다시 작성합니다. 선택 기능보다 필수 조건을 먼저 완성하세요.

설명 연습:

1. 거래 추가 한 건이 어떤 모듈을 거쳐 파일에 저장되는가?
2. 제너레이터를 사용했는데도 `sorted()`로 감싸면 왜 전체 메모리를 쓰는가?
3. 임시 디스크 정렬의 장점과 비용은 무엇인가?
4. 수정 중 오류가 나면 원본은 어떻게 보호되는가?
5. 데코레이터와 타입 힌트가 코드 구조에 어떤 도움을 주는가?
