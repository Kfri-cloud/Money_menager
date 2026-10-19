# CSV 콘솔 가계부

Python 3.10 이상과 표준 라이브러리만 사용합니다. `Plzz/B2-1_가계부_구현_가이드북.md`의 확정 정책으로 재구성했습니다. 개념 참고는 [학습 구조도](Plzz/budget-learning-map.html), 구현 설명은 [코드 흐름](docs/06_CODE_FLOW.md)을 보세요. 원본 과제 PDF와의 별도 대조는 이번 재구성에 포함하지 않았습니다.

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

Windows에서 `python`이 Microsoft Store 실행 별칭으로 연결되어 실행되지 않으면 설치된 Python 경로를 사용하세요. 이 작업 환경의 실행 예시는 다음과 같습니다.

```powershell
& "$env:APPDATA\uv\python\cpython-3.14-windows-x86_64-none\python.exe" -m budget_app --help
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

현재 Python 3.14에서 19개 테스트가 통과했습니다. 10,000건 여러 줄 메모 가져오기, ID 순서·재사용 방지, 일괄 취소, 교체 실패와 ID 공백, 대화형 확인, 오류 코드, 모든 help, 실제 CLI 프로세스를 검증합니다. Python 3.10 실실행은 별도로 검증하지 않았습니다. 테스트는 tempfile로 별도 자료를 만들고 정리합니다. 현재 Windows 샌드박스에서는 Python 3.14 tempfile 디렉터리 권한 제한이 있어 테스트 실행에 샌드박스 밖 실행이 필요했습니다.

[요구사항](docs/01_REQUIREMENTS.md) · [Python 안내](docs/02_PYTHON_GUIDE.md) · [실습](docs/03_IMPLEMENTATION_LAB.md) · [제출 점검](docs/04_SUBMISSION_CHECKLIST.md) · [검증 기록](docs/05_VERIFICATION.md)

`output/pdf/money_manager_evaluation_guide.pdf`는 기존 문서로 그대로 보존합니다. 현재 CSV 구현의 사용법은 이 README를 기준으로 보세요.
