# CSV 콘솔 가계부

터미널에서 수입과 지출을 기록하고, 검색·월별 요약·예산 관리를 할 수 있는 가계부입니다. 데이터는 CSV 파일로 저장합니다. Python 3.10 이상과 표준 라이브러리만 사용하므로 별도 패키지 설치가 필요하지 않습니다.

구현 정책은 [가계부 구현 가이드북](Plzz/B2-1_가계부_구현_가이드북.md)을 기준으로 합니다. 개념 참고는 [학습 구조도](Plzz/budget-learning-map.html), 자세한 구현 설명은 [코드 흐름](docs/06_CODE_FLOW.md)을 보세요.

## 빠르게 시작하기

프로젝트 폴더에서 다음 명령을 실행합니다.

```powershell
python --version
python -m budget_app --help
python -m budget_app add
python -m budget_app list
```

`add` 실행 시 입력 예시입니다. 메모와 태그는 Enter로 생략할 수 있습니다.

```text
날짜 (YYYY-MM-DD): 2026-10-19
종류 (income/expense): expense
카테고리: 식비
금액: 9000
메모 (선택): 점심
태그 (쉼표 구분, 선택): 학교,친구
```

`income`은 수입, `expense`는 지출입니다. 금액은 `9000`처럼 쉼표 없는 양수 정수로 입력합니다. 최초 실행 시 저장 폴더와 기본 카테고리가 생성됩니다.

연습 데이터를 따로 저장하려면 모든 명령에서 같은 폴더를 지정하세요.

```powershell
python -m budget_app --data-dir ./practice-data add
python -m budget_app --data-dir ./practice-data list
```

## 실행

저장소 루트에서 실행합니다. `--data-dir`은 명령 앞에 지정합니다. 기본 경로는 현재 실행 위치의 `./data`입니다.

```powershell
python -m budget_app --help
python -m budget_app add
python -m budget_app list --limit 20
python -m budget_app search --from 2026-10-01 --to 2026-10-31 --category 식비 --type expense --q 점심 --tags 친구,학교
python -m budget_app update --id TX-000001
python -m budget_app delete --id TX-000001
python -m budget_app summary --month 2026-10 --top 5
python -m budget_app budget set --month 2026-10
python -m budget_app budget get --month 2026-10
python -m budget_app category add
python -m budget_app category list
python -m budget_app category delete
python -m budget_app --data-dir ./practice-data import --file examples/transactions.csv
python -m budget_app --data-dir ./practice-data export --file october.csv --month 2026-10
python -m budget_app export --file period.csv --from 2026-10-01 --to 2026-10-31
```

`add`는 날짜·종류·카테고리·금액·메모·태그를 대화형으로 받습니다. `update`는 현재 값을 표시하고 Enter로 유지합니다. 메모·태그만 `:clear`로 비울 수 있습니다. 변경 전후를 표시한 뒤 확인합니다. `delete`도 확인하며 공백 제거·대소문자 무시 후 `y` 또는 `yes`만 승인합니다. 취소·변경 없음·EOF·Ctrl+C는 코드 0입니다. 예산 금액과 카테고리 이름도 대화형 입력입니다. 모든 명령과 하위 명령은 `--help`를 지원하며 짧은 옵션은 사용하지 않습니다.

Windows에서 `python` 명령이 실행되지 않으면 Python 설치와 PATH 설정을 확인하거나, Python 런처가 설치된 경우 `py`를 사용하세요.

```powershell
py -m budget_app --help
```

## 파일 구조

```text
budget_app/
  models.py        Transaction, Category, Budget
  validators.py    값 검증·정규화 함수
  repositories.py  CsvRepository, 스트리밍 CSV·ID 확보·안전한 교체
  services.py      BudgetService, 검색·집계·일괄 가져오기
  cli.py           파서·대화형 입력·출력·handler
  decorators.py    handle_errors
  errors.py        AppError·저장 데이터 오류
  __init__.py
  __main__.py
tests/test_budget.py
examples/transactions.csv
Plzz/              기준 가이드·프롬프트·학습 참고 자료
```

## 코드의 역할과 실행 흐름

| 모듈 | 역할 |
|---|---|
| `__main__.py` | `python -m budget_app`의 시작점. `main()`의 반환값을 종료 코드로 사용 |
| `cli.py` | 명령어 해석, 대화형 입력, 결과 출력. `handle_*` 함수가 각 명령 처리 |
| `services.py` | `BudgetService`가 검증과 저장을 조합하여 거래·검색·집계 작업 진행 |
| `repositories.py` | `CsvRepository`가 CSV 읽기·쓰기, 저장 형식 검사, ID 번호 예약 담당 |
| `models.py` | 거래·카테고리·예산 데이터를 담는 객체 정의 |
| `validators.py` | 날짜·금액 등 개별 값 검사와 정규화. 잘못된 값이면 예외 발생 |
| `errors.py` | 메시지·해결 힌트·종료 코드를 담는 `AppError`와 데이터 오류 생성 함수 정의 |
| `decorators.py` | `@handle_errors`로 예외를 잡아 안내 메시지와 반환 코드로 변환 |

거래 추가 명령의 실행 흐름은 다음과 같습니다.

```text
python -m budget_app add
  → __main__.py에서 main() 호출
  → create_parser().parse_args()로 명령 해석
  → CsvRepository 생성 및 저장 파일 초기화
  → BudgetService(repository) 생성
  → args.handler(args, service), 즉 handle_add() 실행
  → 사용자 입력을 service.add_transaction()에 전달
  → 값 검증 → ID 번호 예약·부여 → CSV 저장
  → 저장 완료 메시지 출력
```

`handler`는 선택한 명령을 처리할 함수입니다. `add`는 `handle_add`, `list`는 `handle_list`에 연결됩니다. `BudgetService`는 생성 시 저장소를 보관하고, 핸들러가 호출한 메서드를 실행합니다.

검증 함수와 저장소 등에서 발생한 예외는 호출한 쪽으로 전달됩니다. `@handle_errors`가 붙은 함수의 경계에서 이를 잡아 사용자에게 안내합니다. `errors.py`는 오류를 정의하고, `validators.py`는 잘못된 값을 발견하며, `decorators.py`는 오류 표시를 담당합니다.

이전 `repository.py`와 `service.py`는 복수형 모듈로 교체했습니다. 이전 UUID·JSONL API는 유지하지 않습니다. JSONL 데이터가 있는 폴더에서는 새 CSV 초기화를 차단합니다. 원본을 보관하고 별도 저장 폴더를 사용하세요. 자동 데이터 이전 기능은 없습니다.

## 저장 형식

UTF-8·헤더·csv 모듈을 사용합니다. 내부 날짜는 `datetime.date`, 금액은 `int`, 태그는 `list[str]`입니다. dataclass와 타입 힌트는 값 검증을 대신하지 않습니다.

| 파일 | 헤더 |
|---|---|
| transactions.csv | id,type,date,amount,category,memo,tags |
| categories.csv | name |
| budgets.csv | month,amount |
| metadata.csv | key,value |

metadata에는 `last_transaction_number,0`에서 시작하는 마지막 발급 번호가 있습니다. 네 파일 중 일부가 누락되거나 파일이 비었거나 헤더가 손상되면 자동 복구하지 않습니다. 백업에서 일관된 파일들을 복원하세요. 최초 네 파일의 생성 자체는 단일 원자적 작업이 아니므로 초기화 도중 실패한 경우에도 같은 원칙을 적용합니다.

외부 CSV 필수 열은 `date,type,category,amount`, 선택 열은 `memo,tags`입니다. 추가 열과 UTF-8 BOM은 허용하고 추가 열은 무시합니다. 중복 헤더·열 개수 불일치·잘못된 UTF-8·잘못된 값은 오류입니다. CSV 셀의 쉼표·따옴표·줄바꿈은 csv 모듈로 처리합니다.

```csv
date,type,category,amount,memo,tags
2026-10-19,expense,식비,9000,"친구와 점심, 분식","점심,친구"
```

## 확정 정책

1. ID는 `TX-000001`부터 증가하며 metadata에 먼저 확보합니다. 삭제 후에도 재사용하지 않고 수정으로 바꾸지 않습니다. 6자리 초과도 지원합니다.
2. 날짜는 정확한 YYYY-MM-DD와 실제 날짜를 검사합니다. 거래 금액은 양수 정수이며 bool·소수·쉼표 금액은 거부합니다.
3. 파일·목록·검색은 날짜와 무관하게 **숫자 ID 내림차순**입니다. 목록 기본 limit는 20입니다.
4. 검색 기간은 양끝 포함, 조건 AND, 메모는 부분 일치, 여러 태그는 전체 이름으로 모두 포함해야 합니다. 메모·태그 영문 대소문자를 무시하고 역전 기간은 오류입니다.
5. 이름은 앞뒤 공백만 제거합니다. 카테고리는 대소문자 무시 중복 차단·최초 표기 유지, 태그는 거래별 중복·빈 항목 제거·최초 표기와 순서 유지입니다.
6. 최초에만 `급여, 용돈, 기타수입, 식비, 교통, 주거, 생활용품, 여가, 기타지출`을 생성합니다. 공통 카테고리이며 유형 제한은 없습니다. 사용 중 삭제 금지, 빈 목록 자동 복원 금지, 빈 목록에서 추가·가져오기 금지입니다.
7. 예산은 월별 전체 지출 기준 0 이상 정수입니다. 재설정 시 교체하며 전후를 안내합니다. 미설정과 0원을 구분하고 0원 사용률은 계산하지 않습니다. 지출이 예산보다 클 때만 초과입니다. TOP 기본 5, 동률은 카테고리 이름 오름차순입니다.
8. 가져오기는 동일 거래·같은 파일 반복을 허용하고 항상 새 ID를 부여합니다. 입력 레코드 순서로 ID를 부여하는 보조 정책을 선택했습니다. 하나라도 잘못되면 거래 파일 전체 반영을 취소합니다. 헤더만 있으면 0건입니다(카테고리가 빈 경우에는 가져오기 차단 정책이 우선).
9. 목록·검색은 제너레이터로 스트리밍합니다. limit·top은 양수 정수이며 검색은 개수 제한 없이 출력합니다.
10. 수정·삭제는 대화형 확인, 취소·변경 없음은 저장하지 않고 0입니다. 변경값은 확인 전에 전부 검증합니다.
11. 손상 행은 건너뛰지 않습니다. 파일·레코드 위치·원인·복구 힌트를 안내합니다. 목록이 이미 출력되었다면 불완전함을 표시하고 요약은 전체 성공 후에만 출력합니다. limit 뒤의 읽지 않은 손상까지 검사했다고 보장하지 않습니다.

카테고리 이름의 줄바꿈은 거부합니다. malformed ID는 입력 오류 2, 정규 형식이지만 없는 ID는 3입니다. 입력값을 조용히 수정하지 않도록 날짜·금액의 주변 공백은 자동 제거하지 않습니다. 메모는 입력 그대로 유지합니다. 내보내기는 월 하나 또는 시작·종료일 쌍을 요구하며 기존 출력 파일은 성공 시 교체합니다. 내부 저장 파일 경로와 그 하드링크는 내보내기 대상으로 금지합니다.

## 저장 안전성과 스트리밍

쓰기 전에 필요한 기존 데이터 전체 검사를 수행합니다. 같은 디렉터리 임시 파일에 쓰고 flush·fsync 후 닫고 `os.replace`로 교체합니다. 거래 파일과 metadata는 함께 원자적으로 교체되지 않습니다. ID를 먼저 확보하므로 거래 저장 실패 시 번호 공백이 생길 수 있습니다. 완전한 전원 장애 내구성·여러 파일의 통합 트랜잭션·동시 프로세스 쓰기는 지원하지 않습니다.

가져오기는 검증한 레코드를 JSON 임시 스풀에 저장하고 레코드 시작 위치를 8바이트 인덱스 임시 파일에 저장합니다. 모든 검증 후 ID 구간을 확보하고 인덱스를 역순으로 읽습니다. CSV 셀의 실제 줄을 뒤집지 않아 여러 줄 메모가 보존됩니다. 전체 거래 목록을 메모리에 모으거나 정렬하지 않으며 최대 레코드 크기와 카테고리·예산 크기에 비례한 메모리를 사용합니다. 임시 디스크 공간은 입력 크기에 비례합니다. JSON은 이 임시 스풀에만 사용하며 영구 저장 형식은 CSV입니다.

## 종료 코드와 진단

| 코드 | 의미 |
|---:|---|
| 0 | 정상·취소·변경 없음·결과 없음 |
| 1 | 예상하지 못한 내부 오류 |
| 2 | CLI·직접 입력 값 오류 |
| 3 | 없는 대상·중복·미등록·사용 중 등 정책 충돌 |
| 4 | 파일 접근·쓰기·교체 오류 |
| 5 | 저장/가져오기 CSV 형식·내용 오류 |

가져오기의 미등록 카테고리도 5이고 파일을 열 수 없으면 4입니다. 화면에 스택트레이스는 표시하지 않습니다. 개발자는 `budget_app.decorators` 로거를 DEBUG 수준으로 설정해 내부 예외 기록을 받을 수 있습니다. 기본 실행에서는 별도 로그 파일을 만들지 않습니다.

## 검증

```powershell
python -m unittest discover -s tests -v
```

테스트는 여러 줄 메모 가져오기, ID 순서·재사용 방지, 일괄 취소, 교체 실패와 ID 공백, 대화형 확인, 오류 코드, 도움말, 실제 CLI 프로세스를 검사합니다. `tempfile`로 별도 테스트 데이터를 만들어 사용합니다. 이전 실행 결과와 환경별 제한은 [검증 기록](docs/05_VERIFICATION.md)을 참고하세요.

[요구사항](docs/01_REQUIREMENTS.md) · [Python 안내](docs/02_PYTHON_GUIDE.md) · [실습](docs/03_IMPLEMENTATION_LAB.md) · [제출 점검](docs/04_SUBMISSION_CHECKLIST.md) · [검증 기록](docs/05_VERIFICATION.md)

`output/pdf/money_manager_evaluation_guide.pdf`는 이전 JSONL 구현의 평가 자료입니다. 아래 설명은 그 평가 항목을 현재 CSV 구현에 맞춰 정리한 것입니다. 이전 문서의 UUID, 날짜순 정렬, `import --from`, `export --out` 예시는 현재 구현에 적용되지 않습니다.

## 평가 항목 1: 기능과 데이터 유지

### 기본 명령 8개

| 명령 | 현재 동작 | 구현 위치 |
|---|---|---|
| `add` | 대화형 입력 → 값 검증 → 새 ID 부여 → 저장 | `handle_add`, `BudgetService.add_transaction` |
| `list` | 숫자 ID 내림차순, 기본 20건 출력 | `list_transactions` |
| `search` | 기간·유형·카테고리·메모·태그 조건을 AND로 검색 | `search_transactions` |
| `summary` | 월별 수입·지출·잔액, 카테고리별 지출 TOP, 예산 출력 | `get_monthly_summary`, `handle_summary` |
| `export` | 월 또는 기간의 거래를 외부 CSV로 저장 | `export_transactions` |
| `import` | 외부 CSV 전체 검증 후 새 ID로 일괄 저장 | `import_transactions` |
| `update` | 현재 값 표시 → 변경값 검증 → 전후 비교 → 승인 후 저장 | `handle_update`, `preview_update` |
| `delete` | 대상 표시 → 승인 후 해당 거래 제거 | `handle_delete`, `delete_transaction` |

ID는 날짜와 무관한 발급 순서입니다. 삭제한 번호는 재사용하지 않으며 수정 시 ID를 유지합니다. 검색 기간은 양끝을 포함하고, 여러 태그를 지정하면 모두 포함한 거래만 반환합니다.

### 재실행 후에도 데이터가 유지되는가?

거래는 `transactions.csv`, 카테고리는 `categories.csv`, 예산은 `budgets.csv`, 마지막 발급 번호는 `metadata.csv`에 저장합니다. 메모리 변수만 사용하는 것이 아니라 명령마다 같은 저장 폴더의 파일을 읽으므로 프로세스를 다시 실행해도 유지됩니다. 단, 같은 작업 폴더 또는 동일한 `--data-dir`을 사용해야 합니다.

```powershell
python -m budget_app --data-dir ./eval-data category add
python -m budget_app --data-dir ./eval-data budget set --month 2026-10
# 아래 명령들은 각각 새 프로세스이며, 앞에서 저장한 값을 읽습니다.
python -m budget_app --data-dir ./eval-data category list
python -m budget_app --data-dir ./eval-data budget get --month 2026-10
Get-ChildItem ./eval-data/*.csv
```

### 카테고리 추가·목록·삭제

`category add`는 이름을 입력받아 중복을 검사하고 저장합니다. `category list`는 저장된 목록을 출력합니다. 삭제 전에는 전체 거래를 확인하여 사용 중인 카테고리 삭제를 거부하고, 해당 거래를 먼저 수정·삭제하라는 힌트를 출력합니다.

**요구 항목의 `category remove`에 해당하는 현재 명령은 `category delete`입니다. `remove` 별칭은 구현되어 있지 않습니다.** 명령어 철자까지 `remove`를 요구하는 평가라면 이 부분은 불일치입니다.

```powershell
python -m budget_app category add
python -m budget_app category list
python -m budget_app category delete
```

### 예산 저장과 사용률·초과 표시

`budget set --month 2026-10`에서 입력받은 0 이상 정수를 저장합니다. 같은 월을 다시 설정하면 기존 값을 교체합니다. `summary`는 해당 월 전체 지출을 기준으로 사용률을 계산합니다.

```text
사용률 = 월 지출 / 월 예산 × 100
예: 지출 9,000원 / 예산 5,000원 → 사용률 180.0%, 예산 초과
```

예산과 지출이 같으면 초과가 아닙니다. 예산 미설정과 0원은 구분하며, 0원일 때는 나눗셈 대신 계산 불가 안내를 출력합니다.

### CSV 스키마와 오류 처리

외부 CSV 출력은 UTF-8이며 헤더 순서는 `date,type,category,amount,memo,tags`입니다. 가져오기는 앞의 네 열을 필수로 요구하고 메모·태그는 생략할 수 있습니다. 추가 열과 UTF-8 BOM은 허용합니다. 내부 거래 CSV에는 별도로 `id` 열이 있습니다.

`csv.DictReader`와 `csv.DictWriter`를 사용하므로 쉼표·따옴표·여러 줄 메모를 CSV 인용 규칙에 따라 처리합니다. 금액·날짜·카테고리는 별도 검증합니다. 중복 헤더, 열 개수 불일치, 잘못된 인코딩은 오류로 처리합니다.

`@handle_errors`는 입력·파일·저장 데이터 오류를 메시지와 힌트로 바꿔 출력합니다. 기본 CLI 실행에서는 스택트레이스를 출력하지 않습니다. 오류 종료 코드는 위 표의 1~5이며 PowerShell에서 다음처럼 확인합니다.

```powershell
python -m budget_app delete --id invalid
$LASTEXITCODE
# 예상: 2 (잘못된 ID 형식)
```

사용자 취소·EOF·Ctrl+C는 실패가 아닌 취소로 간주하여 0을 반환합니다. 예상하지 못한 내부 오류도 1을 반환합니다.

## 평가 항목 2: 책임 분리와 안전한 파일 수정

### 모듈과 클래스의 책임을 어떻게 나눴는가?

입출력, 작업 규칙, 저장 방식이 서로 다른 이유로 변경된다는 점을 기준으로 나눴습니다. 콘솔 문구는 `cli.py`, 작업 진행은 `services.py`, CSV 처리는 `repositories.py`에서 변경합니다. 값 검증은 `validators.py`, 데이터 구조는 `models.py`, 오류 정의와 공통 처리는 각각 `errors.py`, `decorators.py`에 둡니다.

대표 클래스의 경계는 다음과 같습니다.

| 클래스 | 책임 | 경계를 정한 이유 |
|---|---|---|
| `BudgetService` | 값 검증과 저장 호출을 조합하여 거래·검색·집계 작업 수행 | 콘솔 입력이나 CSV 작성 코드를 작업 규칙과 분리 |
| `CsvRepository` | 파일 경로, CSV 변환, 저장 데이터 검사, 파일 교체 | 파일 저장 방식을 바꿀 때 관련 코드를 모아서 수정 |
| `Transaction` | ID·날짜·금액·태그 등 한 거래의 데이터 보관 | 딕셔너리 키를 곳곳에서 직접 다루는 대신 명시적인 객체 사용 |

`BudgetService(repository)`처럼 저장소 객체를 생성자에 전달하고 `self.repository`에 보관합니다. 서비스가 직접 콘솔 입력을 받거나 CSV 스트림을 작성하지 않도록 역할을 나눴습니다.

### update/delete를 어떻게 안전하게 처리하는가?

CSV 파일의 특정 줄을 직접 덮어쓰지 않고 `_rewrite()`에서 전체 거래를 순회합니다. 수정은 대상 행을 새 거래로 교체하고, 삭제는 대상 행을 출력하지 않습니다. 다른 거래는 그대로 기록합니다.

`write()`는 같은 디렉터리의 임시 파일에 헤더와 전체 행을 작성한 뒤 `flush()` → `os.fsync()` → 파일 닫기 → `os.replace()` 순서로 원본을 교체합니다. 작성·검증 중 오류가 발생하면 교체하지 않으며 `finally`에서 임시 파일을 정리합니다. CLI에서는 수정·삭제 전에 사용자의 확인도 받습니다.

이는 단일 파일의 불완전한 덮어쓰기를 피하는 방식입니다. 여러 파일의 동시 트랜잭션과 동시 실행에 대한 잠금은 제공하지 않습니다. metadata는 거래 파일보다 먼저 갱신되므로 저장 실패 시 ID 번호에 공백이 생길 수 있습니다.

## 평가 항목 3: 제너레이터·데코레이터·타입 힌트

### 스트리밍을 어떻게 구현했고 왜 유리한가?

```text
records(): CSV 행을 딕셔너리로 yield
  → iter_transactions(): 검증한 Transaction을 yield
  → list_transactions()/search_transactions(): 필요한 거래를 yield
  → show_transactions(): 받은 거래를 바로 출력
```

전체 거래를 리스트로 만들지 않으므로 거래 수에 비례하는 객체 목록을 메모리에 유지할 필요가 없습니다. 목록은 지정한 개수에 도달하면 읽기를 종료합니다. 검색은 전체를 순회하지만 일치하는 거래를 발견할 때마다 전달합니다. `closing()`은 조기 종료 때 제너레이터와 파일을 닫는 데 사용합니다.

스트리밍은 전체 검색 시간을 자동으로 줄이지 않습니다. 검색은 여전히 O(N)이며, 목록의 제한 뒤에 있는 손상 행까지 검사했다고 보장하지 않습니다.

### 데코레이터로 분리한 공통 기능은 무엇인가?

`@handle_errors`는 `main()`과 핸들러에서 발생한 예외를 오류 메시지·해결 힌트·반환 코드로 변환합니다. 동일한 `try-except`를 명령마다 반복하지 않고 출력 규칙을 한곳에서 관리하기 위해 분리했습니다. `functools.wraps`로 원래 함수의 이름 등 메타데이터도 유지합니다.

### 타입 힌트는 어떻게 도움이 되는가?

```python
def get_transaction(self, transaction_id: str) -> Transaction:
    ...

def iter_transactions(self) -> Iterator[Transaction]:
    ...

def _rewrite(self, transaction_id: str, replacement: Transaction | None) -> None:
    ...
```

각각 문자열 ID를 받아 거래 하나를 반환한다는 점, 거래를 한 건씩 제공한다는 점, 대체 거래가 없을 수도 있다는 점을 함수 선언에서 알 수 있습니다. IDE에서 반환된 거래의 `amount`, `date` 같은 속성 자동 완성과 타입 정보 확인에 도움을 줍니다. 정적 분석 도구를 사용하면 `get_transaction(123)`처럼 인자 타입이 다른 호출을 실행 전에 지적할 수 있습니다.

현재 정적 타입 검사 도구를 실행해 전체 코드의 타입 적합성을 확인한 것은 아닙니다. 타입 힌트 자체는 실행 중 잘못된 값을 막지 않으므로 실제 검증은 `validate_date`, `validate_amount` 등이 담당합니다.

## 평가 항목 4: 저장 형식과 확장성

### CSV와 JSONL 비교 및 선택 이유

| 기준 | CSV | JSONL |
|---|---|---|
| 구조 | 헤더와 행으로 이루어진 표 | 한 줄마다 JSON 객체 |
| 장점 | 스프레드시트·외부 도구와 교환하기 편하고 고정 열에 적합 | 숫자·배열·중첩 객체를 자연스럽게 표현 |
| 단점 | 타입 복원과 태그 표현 규칙이 필요, 여러 줄 셀 인용 처리 필요 | 키가 반복되고 스프레드시트에서 바로 다루기 불편 |
| 공통 한계 | 인덱스 없이 ID 검색은 전체 순회 | 인덱스 없이 ID 검색은 전체 순회 |

현재 거래·카테고리·예산은 고정 열 구조이고, 외부 CSV 교환과 저장 스키마를 일관되게 유지하기 위해 CSV를 선택했습니다. 날짜는 ISO 문자열, 태그는 쉼표 구분 문자열로 저장하고 읽을 때 검증·복원합니다. CSV는 한 레코드에 여러 물리적 줄이 들어갈 수 있으므로 문자열 `split(',')`나 줄 뒤집기 대신 `csv` 모듈로 처리합니다.

영구 저장은 CSV입니다. import 구현에서 JSON을 사용하지만 이는 검증한 거래를 임시 스풀에 담기 위한 용도입니다.

### 거래가 10만 건이라면 병목과 개선 방향

현재 구현의 복잡도는 다음과 같습니다. N은 전체 거래 수, K는 지출 카테고리 수입니다.

| 작업 | 병목 |
|---|---|
| 목록 | 필요한 개수만 읽어 조기 종료 가능 |
| 조건 검색·월별 요약 | 인덱스가 없어 전체 거래 O(N) 읽기·검증 |
| 요약 TOP | 집계 후 카테고리 정렬 O(K log K) |
| 단건 추가·수정·삭제 | 기존 데이터 검사와 거래 파일 전체 재작성 O(N) |
| 일괄 import | 입력 검증·임시 스풀 쓰기·역순 읽기·기존 파일 재작성에 따른 디스크 I/O |

단건 추가를 반복하면 매번 커진 파일을 다시 쓰므로 누적 작업량이 O(N²) 수준으로 커질 수 있습니다. 10만 건의 실제 실행 시간과 메모리 사용량은 아직 측정하지 않았습니다.

개선은 먼저 10만 건 데이터로 첫 출력 시간·전체 처리 시간·메모리·디스크 사용량을 측정하고 진행합니다. 파일 방식을 유지해야 한다면 일괄 추가, 월별 파일 분할, 인덱스와 캐시를 고려할 수 있습니다. 다만 인덱스 갱신과 장애 복구 규칙이 함께 필요합니다. 저장 방식 변경이 허용된다면 SQLite와 ID·날짜·카테고리 인덱스, 트랜잭션을 사용해 전체 파일 재작성과 동시 쓰기 문제를 줄이는 방향이 적합합니다. 이는 개선 제안이며 현재 구현은 아닙니다.

### 깨진 import 행은 어떻게 처리하는가?

현재 정책은 **한 행이라도 잘못되면 전체 가져오기를 반영하지 않는 것**입니다. 정상 행만 조용히 저장하는 부분 성공은 제공하지 않습니다.

1. 입력 CSV를 한 행씩 읽고 헤더·열 개수·날짜·금액·등록 카테고리를 검증합니다.
2. 검증한 행은 영구 거래 파일 대신 임시 스풀과 오프셋 인덱스에 기록합니다.
3. 전체 입력 검증에 성공한 뒤 ID 범위를 예약합니다.
4. 새 거래와 기존 거래를 임시 CSV에 기록하고, 완성되면 거래 파일을 교체합니다.
5. 성공한 경우에만 `imported=N`을 출력합니다.

입력 오류는 파일과 레코드 번호, 원인을 안내합니다. CSV 파싱 오류에는 파서 줄 번호도 포함하며, 사용자는 원본을 수정한 뒤 다시 시도할 수 있습니다. 전체 오류 목록을 별도 리포트 파일로 만드는 기능은 없고 첫 오류에서 중단합니다.

검증 실패 시 기존 거래 파일과 ID metadata는 변경하지 않습니다. 검증 성공 후 저장 단계에서 실패하면 기존 거래 파일은 보존하지만, 이미 예약한 ID 번호는 남을 수 있습니다. 따라서 여러 파일 전체를 되돌리는 완전한 롤백이라고 표현하지 않습니다. 향후 부분 성공을 추가한다면 명시적인 선택 옵션과 성공·실패 건수, 행별 오류 리포트, 중복 재시도 정책을 함께 제공해야 합니다.

### 테스트 근거 확인

2026-10-19에 Python 3.14에서 기존 테스트 19개를 실행하여 모두 통과했습니다. 최초 샌드박스 실행은 임시 폴더 접근 권한으로 실패했고, 권한 제한을 해제한 재실행에서 통과했습니다. 문서만 수정했으며 애플리케이션 코드는 변경하지 않았습니다.

`tests/test_budget.py`에는 다음 평가 항목을 확인하는 테스트가 있습니다.

| 검증 대상 | 테스트 예시 |
|---|---|
| ID 유지·순서·재사용 방지 | `test_id_order_persistence_and_no_reuse` |
| 검색 기간·다중 태그 | `test_search_boundaries_and_all_tags` |
| 예산 미설정·0원·동일·초과 | `test_budget_zero_unset_equal_exceeded_empty` |
| 수정 확인·취소·초기화 | `test_update_clear_confirm_cancel_noop` |
| CSV 왕복·여러 줄 메모 | `test_import_repeat_multiline_roundtrip` |
| 잘못된 import 미반영 | `test_invalid_import_rolls_back` |
| 파일 교체 실패 시 원본 보존 | `test_replace_failure_preserves_original_and_reserved_gap` |
| 종료 코드·데코레이터 | `test_codes_and_decorator_metadata` |
| 실제 CLI 프로세스·도움말 | `test_all_help_no_files_and_actual_process` |
| 대량 import·제너레이터 닫기 | `test_large_import_generator_and_close` |

테스트의 존재와 모든 평가 조건의 충족은 별개입니다. 특히 `category remove` 명령 이름, 정적 타입 검사, 10만 건 성능은 위에서 밝힌 차이와 검증 범위를 기준으로 판단해야 합니다.

## 요구사항 1 실제 CLI 검증 기록 (2026-10-19)

기존 데이터와 애플리케이션 코드를 변경하지 않고 `.cli-verification-20261019` 아래의 별도 저장소에서 검증했습니다. 각 명령은 `python -m budget_app --data-dir <검증폴더>`로 새 프로세스를 실행했으며, 표의 명령은 이 접두사를 생략했습니다. 프로세스의 표준 출력·표준 오류·실제 종료 코드와 저장 파일 내용을 확인했습니다.

상세 입력과 출력은 [실행 로그](.cli-verification-20261019/results.json)에 있습니다. 기본 검증 스크립트는 [verify.py](.cli-verification-20261019/verify.py)이며, 중복 헤더·열 개수 불일치·깨진 따옴표 검증은 추가 실행하여 로그에 기록했습니다. 스크립트를 다시 실행하려면 기존 검증 폴더와 다른 데이터 경로를 사용해야 합니다.

| 항목 | 실행 명령·입력 | 예상 결과 | 실제 결과 | 종료 코드 | 판정 |
|---|---|---|---|---|---|
| add | `add`: 지출 120,000원·수입 300,000원 | 저장·ID 발급 | `TX-000001`, `TX-000002` 저장 | 0 | 통과 |
| list·재실행 유지 | 새 프로세스에서 `list` | 기존 거래 출력 | 두 거래와 금액 유지 | 0 | 통과 |
| search | 기간·카테고리·종류·메모·다중 태그 지정 | AND 조건 검색 | 조건에 맞는 지출 1건만 출력 | 0 | 통과 |
| summary | `summary --month 2026-10` | 월별 집계 | 수입 300,000원·지출 120,000원·잔액 180,000원 | 0 | 통과 |
| update | `update --id TX-000001`: 125,000원·메모 수정 후 `y` | 수정 저장 | 새 프로세스에서 수정값 유지 | 0 | 통과 |
| delete | `delete --id TX-000001`: `y` | 삭제 저장 | 새 프로세스 목록에서 제거 확인 | 0 | 통과 |
| 저장 파일 수 | 최초 실행 후 파일 확인 | 3개 이상 | `transactions.csv`, `categories.csv`, `budgets.csv`, `metadata.csv` 생성 | 최초 실행 0 | 통과 |
| category add/list | 추가 후 새 프로세스에서 목록 확인 | 카테고리 유지 | `검증분류` 유지 | 0 | 통과 |
| 사용 중 카테고리 삭제 | `category delete`: `검증분류` | 삭제 차단·힌트 | 거래 수정·삭제 안내, 저장 파일 유지 | 3 | 통과 |
| 미사용 카테고리 삭제 | 추가 → `category delete` → 목록 확인 | 카테고리 제거 | 목록에서 제거 확인 | 0 | 통과 |
| category remove | `category remove` | 요구된 명령 지원 | 미지원, 실제 명령은 `delete` | 2 | 실패 |
| budget set·재실행 유지 | 100,000원 설정 후 새 프로세스에서 `budget get` | 예산 유지 | 100,000원 출력 | 0 | 통과 |
| 예산 사용률·초과 | 지출 120,000원 상태에서 월 요약 | 120%·초과 경고 | `사용률 120.0%`, `[경고] 예산 초과` | 0 | 통과 |
| 미설정·0원 예산 | 미설정 월과 0원 설정 월 요약 | 구분·나눗셈 오류 방지 | `예산 미설정`, `계산 불가 — 예산 0원` | 0 | 통과 |
| export 스키마 | 월별 `export` 후 파일 해독·헤더 검사 | UTF-8·정해진 열 순서 | `date,type,category,amount,memo,tags` 확인 | 0 | 통과 |
| CSV 특수문자·왕복 | 한글·쉼표·따옴표·여러 줄 메모 import/export, 별도 저장소 재import | 거래 내용 보존 | ID·순서를 제외한 거래 내용 일치 | 0 | 통과 |
| import 열 정책 | 필수 4열만 입력, BOM·추가 열 포함 입력 | 문서화된 정책대로 허용 | 두 경우 모두 성공 | 0 | 통과 |
| 잘못된 입력 | 잘못된 날짜·음수 금액·ID·카테고리·명령 인자 | 오류·힌트·비정상 종료 | 스택트레이스 없이 안내 | 2·3 | 통과 |
| 없는 파일 | `import --file <없는 파일>` | 파일 오류·힌트 | 경로·권한·여유 공간 확인 안내 | 4 | 통과 |
| 깨진 CSV | 잘못된 값·필수 열 누락·중복 헤더·열 개수 불일치·깨진 따옴표·잘못된 UTF-8 | 거부·원인 안내 | 모두 오류·힌트 출력, 스택트레이스 없음 | 5 | 통과 |
| 실패 import 원본 보존 | 정상 행 뒤 잘못된 값 입력 | 전체 반영 취소 | 저장 CSV 바이트가 실행 전과 동일 | 5 | 통과 |
| 실패 update/delete 원본 보존 | 음수 금액 수정·없는 ID 삭제 | 변경 거부 | 저장 CSV 바이트가 실행 전과 동일 | 2·3 | 통과 |
| 실제 저장 실패 | Windows 파일 핸들로 테스트 거래 파일을 잠근 뒤 import/update/delete | 파일 오류·거래 원본 보존 | 세 작업 모두 오류·힌트 출력, 거래 파일 바이트 동일 | 4 | 통과 |

저장 파일의 역할은 거래(`transactions.csv`), 카테고리(`categories.csv`), 월별 예산(`budgets.csv`), 마지막 발급 ID 번호(`metadata.csv`)입니다. 위 표의 항목 중 미검증으로 남은 항목은 없습니다. 결과는 실행한 입력과 장애 조건에 대한 확인이며 모든 가능한 입력·장애를 보장하지는 않습니다.

### 요구사항 불일치와 보완점

- **명령 이름:** `category remove`는 지원하지 않습니다. 요구사항이 이 이름을 지정한다면 `remove` 별칭을 추가하거나 요구사항을 `delete`로 맞춰야 합니다.
- **CSV 허용 범위:** export는 정확히 6열을 출력하지만 import는 필수 4열만 있어도 허용하고 추가 열을 무시합니다. 정확히 6열만 허용해야 한다면 검증 정책 변경이 필요합니다.
- **import 오류 힌트:** 잘못된 입력 파일에도 일반적인 백업·CSV 복구 힌트가 나옵니다. 입력 파일의 해당 행을 수정하라는 안내로 구체화할 수 있습니다.
- **저장 실패와 ID:** 잠금으로 import 저장이 실패해도 거래 파일은 보존되지만 이미 예약한 ID 번호는 소비됩니다. 여러 파일 전체의 롤백이 아니며 ID 사이에 빈 번호가 생길 수 있습니다.

이번 검증에서는 위 불일치와 보완점을 기록했으며 애플리케이션 코드는 수정하지 않았습니다.

## 평가 질문별 답변 위치와 코드 안내

답변은 이 README의 **186행부터**, 실제 CLI 검증 결과는 **381행부터** 있습니다. 아래 줄 번호는 이 안내를 작성한 시점 기준이며 파일 수정에 따라 달라질 수 있습니다. 제목 링크는 문서 안의 해당 설명으로 이동하고, 코드 링크의 `L` 뒤 숫자는 해당 파일의 시작 행입니다.

| 평가 항목 | README 시작 행 | 설명 위치 |
|---|---|---|
| 항목 1: 기능·데이터 유지 | 186 | [평가 항목 1](#평가-항목-1-기능과-데이터-유지) |
| 항목 2: 책임 분리·안전한 파일 수정 | 255 | [평가 항목 2](#평가-항목-2-책임-분리와-안전한-파일-수정) |
| 항목 3: 제너레이터·데코레이터·타입 힌트 | 279 | [평가 항목 3](#평가-항목-3-제너레이터데코레이터타입-힌트) |
| 항목 4: 저장 형식·확장성 | 315 | [평가 항목 4](#평가-항목-4-저장-형식과-확장성) |
| 실제 CLI 검증 결과 | 381 | [검증 기록](#요구사항-1-실제-cli-검증-기록-2026-10-19) |
| 요구사항 불일치·보완점 | 415 | [불일치와 보완점](#요구사항-불일치와-보완점) |

### 항목 1 질문별 답변과 구현 근거

**1. add/list/search/summary/export/import/update/delete가 요구사항대로 동작하는가?**

설명은 **188행**, [기본 명령 8개](#기본-명령-8개)부터입니다. 실제 CLI에서 여덟 명령의 주요 동작을 확인했습니다.

| 명령 | 처리 방식 | 구현 시작 위치 |
|---|---|---|
| add | 입력값 검증 → ID 발급 → 저장 | [services.py 28행](budget_app/services.py#L28) |
| list | ID 내림차순으로 제한 개수만 전달 | [services.py 35행](budget_app/services.py#L35) |
| search | 기간·종류·카테고리·메모·태그를 AND로 검색 | [services.py 43행](budget_app/services.py#L43) |
| summary | 월별 수입·지출·잔액·지출 TOP 집계 | [services.py 91행](budget_app/services.py#L91) |
| export | 월 또는 기간의 거래를 외부 CSV로 저장 | [services.py 168행](budget_app/services.py#L168) |
| import | 전체 입력 검증 후 새 ID로 일괄 저장 | [services.py 141행](budget_app/services.py#L141) |
| update | 변경값 검증 후 대상 거래 교체 | [services.py 78행](budget_app/services.py#L78) |
| delete | 대상 거래 확인 후 제거 | [services.py 86행](budget_app/services.py#L86) |

수정·삭제의 사용자 확인은 각각 [cli.py 109행](budget_app/cli.py#L109), [135행](budget_app/cli.py#L135)부터입니다. 수정은 Enter로 기존 값을 유지하고 메모·태그는 `:clear`로 비울 수 있습니다.

**2. 재실행 후 거래·카테고리·예산이 유지되는가? 저장 파일은 3개 이상인가?**

설명은 **203행**, [재실행 후에도 데이터가 유지되는가?](#재실행-후에도-데이터가-유지되는가)부터입니다. 거래·카테고리·예산·마지막 ID를 CSV 4개에 저장합니다. 경로 정의는 [repositories.py 20행](budget_app/repositories.py#L20), 초기화는 [31행](budget_app/repositories.py#L31)입니다. 같은 `--data-dir`로 실행하면 기존 파일을 읽습니다. 실제 검증에서도 저장과 조회를 서로 다른 프로세스로 실행해 유지 여부를 확인했습니다.

**3. category add/list/remove가 정상 동작하는가? 사용 중인 카테고리는 어떻게 처리하는가?**

설명은 **216행**, [카테고리 추가·목록·삭제](#카테고리-추가목록삭제)부터입니다. [services.py 120행](budget_app/services.py#L120)에서 추가·중복 검사를, [130행](budget_app/services.py#L130)에서 목록 조회를, [133행](budget_app/services.py#L133)에서 삭제를 처리합니다. 삭제 전 전체 거래를 확인하고 사용 중이면 종료 코드 3과 거래 수정·삭제 힌트를 제공합니다. 미사용 카테고리는 삭제됩니다. **현재 명령은 `category delete`이며 `category remove`는 미지원이므로 명령 이름 요구사항에는 불일치합니다.**

**4. budget set이 저장되며 summary에 사용률·초과 여부가 출력되는가?**

설명은 **228행**, [예산 저장과 사용률·초과 표시](#예산-저장과-사용률초과-표시)부터입니다. 저장은 [services.py 108행](budget_app/services.py#L108), 사용률·경고 출력은 [cli.py 146행](budget_app/cli.py#L146)입니다. `월 지출 ÷ 예산 × 100`으로 계산하며 지출이 예산보다 클 때 경고합니다. 실제 실행에서 예산 100,000원·지출 120,000원에 `120.0%`와 초과 경고를 확인했습니다. 미설정과 0원을 구분하고 0원에서는 나눗셈 대신 계산 불가를 안내합니다.

**5. import/export가 UTF-8·헤더·컬럼 스키마를 따르는가?**

설명은 **239행**, [CSV 스키마와 오류 처리](#csv-스키마와-오류-처리)부터입니다. 스키마는 [repositories.py 14행](budget_app/repositories.py#L14), 읽기 검사는 [45행](budget_app/repositories.py#L45), UTF-8 쓰기는 [62행](budget_app/repositories.py#L62)입니다. export 헤더는 `date,type,category,amount,memo,tags`이며 특수문자와 여러 줄 메모의 왕복 보존을 확인했습니다. import는 필수 4열과 선택 2열 정책으로, BOM·추가 열을 허용합니다. 정확히 6열만 허용해야 하는 평가라면 정책 변경이 필요합니다.

**6. 잘못된 입력·파일 오류에서 스택트레이스 없이 오류와 해결 힌트를 출력하는가?**

설명은 **245행**, [CSV 스키마와 오류 처리](#csv-스키마와-오류-처리)에 있습니다. [decorators.py 8행](budget_app/decorators.py#L8)의 `handle_errors`가 예외를 잡아 `[오류]`, `[힌트]`와 반환 코드로 변환합니다. 잘못된 날짜·금액·ID·카테고리·명령 인자, 없는 파일, 깨진 CSV, 실제 파일 잠금 저장 실패에서 스택트레이스 없이 안내하는 것을 확인했습니다.

**7. 오류 상황에서 실제 종료 코드가 0이 아닌가?**

종료 코드 표는 **161행**, [종료 코드와 진단](#종료-코드와-진단)에 있고 확인 예시는 **245행**부터입니다. [__main__.py 3행](budget_app/__main__.py#L3)의 `SystemExit(main())`이 반환값을 실제 종료 코드로 전달합니다. 잘못된 입력은 2, 없는 ID·카테고리 관련 오류는 3, 파일 오류는 4, CSV 오류는 5입니다. 내부 오류는 1이며 사용자 취소·EOF·Ctrl+C는 취소로 구분해 0을 반환합니다. PowerShell에서는 명령 실행 직후 `$LASTEXITCODE`로 확인합니다.

### 항목 2 질문별 답변과 구현 근거

**1. 모듈 책임을 어떻게 나눴는가?**

설명은 **257행**, [모듈과 클래스의 책임](#모듈과-클래스의-책임을-어떻게-나눴는가)부터입니다. 서로 다른 이유로 변경되는 코드를 분리했습니다. `cli.py`는 명령·입출력·확인, `services.py`는 작업 규칙과 검색·집계, `repositories.py`는 CSV 읽기·쓰기·교체를 담당합니다. `models.py`는 데이터 구조, `validators.py`는 검증·정규화, `errors.py`는 오류 정의, `decorators.py`는 공통 예외 처리를 담당합니다. 예를 들어 콘솔 문구를 바꿀 때 파일 저장 코드를 함께 수정할 필요가 줄어듭니다.

**2. 최소 두 클래스의 책임 경계를 어떻게 정했는가?**

설명은 **261행**부터입니다. [BudgetService](budget_app/services.py#L18)는 작업 규칙을 조정하고, [CsvRepository](budget_app/repositories.py#L19)는 CSV 변환과 저장을 담당하며, [Transaction](budget_app/models.py#L7)은 거래 한 건의 데이터를 표현합니다. “사용 중인 카테고리를 삭제할 수 없다”는 서비스 책임이고 “카테고리를 UTF-8 CSV로 기록한다”는 저장소 책임입니다. `BudgetService(repository)`로 저장소를 생성자에 전달하여 연결 지점을 명확하게 했습니다.

**3. 파일 기반 update/delete를 어떻게 안전하게 처리했는가?**

설명은 **271행**, [안전한 update/delete](#updatedelete를-어떻게-안전하게-처리하는가)부터입니다. [repositories.py 174행](budget_app/repositories.py#L174)의 `_rewrite()`가 수정 대상을 교체하거나 삭제 대상을 생략합니다. [62행](budget_app/repositories.py#L62)의 `write()`는 임시 파일 작성 → `flush` → `fsync` → 파일 닫기 → `os.replace` 순서로 처리합니다. 중간 오류가 나면 원본을 교체하지 않습니다. 실제 잠금 장애에서도 거래 원본 보존을 확인했습니다. 여러 파일 전체의 트랜잭션이나 동시 실행 잠금은 제공하지 않습니다.

### 항목 3 질문별 답변과 구현 근거

**1. list/search 스트리밍을 어떻게 구현했고 왜 유리한가?**

설명은 **281행**, [스트리밍 구현과 이점](#스트리밍을-어떻게-구현했고-왜-유리한가)부터입니다. [records()](budget_app/repositories.py#L45) → [iter_transactions()](budget_app/repositories.py#L118) → [list/search](budget_app/services.py#L35) → [show_transactions()](budget_app/cli.py#L64) 순서로 한 거래씩 `yield`하고 바로 출력합니다. 전체 거래 객체를 리스트에 모으지 않아 메모리 사용을 줄이고 목록 제한에 도달하면 읽기를 중단합니다. `closing()`으로 조기 종료 시 파일도 닫습니다. 검색은 인덱스가 없어 여전히 O(N)입니다.

**2. 데코레이터로 무엇을 분리했고 왜 필요한가?**

설명은 **294행**, [데코레이터의 공통 기능](#데코레이터로-분리한-공통-기능은-무엇인가)부터입니다. [decorators.py 8행](budget_app/decorators.py#L8)에서 예외 처리·오류와 힌트 출력·종료 코드 변환을 분리했습니다. 각 명령에 같은 `try/except`를 반복하지 않고 오류 안내를 한곳에서 관리하기 위해서입니다. `functools.wraps`는 원래 함수의 이름 등 메타데이터를 유지합니다.

**3. 타입 힌트가 실제 코드에서 어떻게 도움이 되는가?**

설명은 **298행**, [타입 힌트의 이점](#타입-힌트는-어떻게-도움이-되는가)부터입니다. [get_transaction()](budget_app/repositories.py#L166)의 `str -> Transaction`은 입력과 반환 계약을, [iter_transactions()](budget_app/repositories.py#L118)의 `Iterator[Transaction]`은 거래를 한 건씩 제공함을 나타냅니다. [_rewrite()](budget_app/repositories.py#L174)의 `Transaction | None`은 대체 거래가 없을 수 있음을 명시합니다. IDE 자동완성·코드 이해·정적 분석에 도움이 됩니다. 정적 타입 검사기를 실행해 검증한 것은 아니며 실행 중 입력 검증은 `validators.py`가 담당합니다.

### 항목 4 질문별 답변과 구현 근거

**1. CSV와 JSONL의 장단점 및 CSV 선택 근거는 무엇인가?**

설명은 **317행**, [CSV와 JSONL 비교](#csv와-jsonl-비교-및-선택-이유)부터입니다. CSV는 고정 열과 스프레드시트 교환에 편리하지만 날짜·금액 타입 복원과 태그 목록 표현이 필요합니다. JSONL은 숫자·배열·중첩 구조 표현에 편리하지만 키가 반복되고 스프레드시트에서 바로 다루기 불편합니다. 현재 자료가 고정 열 구조이고 CSV 교환이 필요하므로 CSV를 선택했습니다. import에서 사용하는 JSON은 임시 스풀용이며 영구 저장은 CSV입니다.

**2. 거래가 10만 건이면 병목은 어디이고 어떻게 개선하는가?**

설명은 **330행**, [10만 건의 병목과 개선 방향](#거래가-10만-건이라면-병목과-개선-방향)부터입니다. 검색·요약은 전체 파일 읽기 O(N), 단건 추가·수정·삭제는 전체 재작성 O(N)이며 반복 단건 추가의 누적 비용은 O(N²) 수준으로 커질 수 있습니다. 먼저 실제 시간·메모리·디스크 사용량을 측정하고 일괄 추가·월별 분할을 고려합니다. 저장 방식 변경이 가능하면 SQLite의 ID·날짜·카테고리 인덱스와 트랜잭션으로 개선할 수 있습니다. 10만 건 성능 측정과 SQLite 전환은 현재 검증 결과가 아니라 개선 제안입니다.

**3. 일부 깨진 import 행을 어떻게 처리해 사용자 신뢰를 지키는가?**

설명은 **346행**, [깨진 import 행 처리](#깨진-import-행은-어떻게-처리하는가)부터이며 구현은 [services.py 141행](budget_app/services.py#L141)입니다. 전체 입력을 검증하고 임시 스풀에 기록한 다음, 모두 유효할 때만 ID 예약과 거래 파일 교체를 진행합니다. 한 행이라도 잘못되면 전체 import를 반영하지 않고 파일·레코드 번호·원인을 안내합니다. 입력 검증 실패는 거래와 metadata를 보존하지만 ID 예약 후 저장 실패는 거래만 보존하고 번호를 소비할 수 있습니다. 부분 성공·전체 오류 리포트는 현재 없으며 첫 오류에서 중단합니다. 부분 성공을 추가한다면 명시적인 선택과 성공·실패 건수·행별 오류 리포트를 함께 제공해야 합니다.
