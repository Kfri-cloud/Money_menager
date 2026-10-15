# 나만의 용돈 기입장

Python 3.10 이상과 표준 라이브러리만 사용하는 파일 기반 콘솔 가계부입니다. 거래 추가·조회·검색·수정·삭제, 월별 요약, 예산, 카테고리, CSV 가져오기·내보내기를 구현했습니다. 별도 패키지 설치가 필요 없습니다.

## 실행

저장소 루트에서 실행합니다. Windows에서 `python`이 인식되지 않으면 `py` 또는 설치한 Python 실행 파일 경로를 사용하세요.

```powershell
python -m budget_app --help
python -m budget_app add
python -m budget_app list --limit 10
```

add는 날짜 → 종류 → 카테고리 → 금액 → 메모 → 태그 순서로 대화형 입력을 받습니다. 날짜는 `YYYY-MM-DD`, 종류는 `income/expense`, 금액은 쉼표 없는 양수 정수입니다. 메모·태그는 Enter로 생략하고 태그는 쉼표로 구분합니다. 저장 후 고유 UUID를 출력합니다.

## 명령 예시

```powershell
python -m budget_app search --from 2024-01-01 --to 2024-01-31 --type expense
python -m budget_app search --category food -q 점심 --tag lunch
python -m budget_app summary --month 2024-01 --top 3
python -m budget_app budget set --month 2024-01 --amount 5000
python -m budget_app category add
python -m budget_app category list
python -m budget_app category remove
python -m budget_app update --id <거래ID> --amount 6000 --memo 저녁
python -m budget_app delete --id <거래ID>
python -m budget_app import --from examples/transactions.csv
python -m budget_app export --out january.csv --month 2024-01
python -m budget_app export --out period.csv --from 2024-01-01 --to 2024-01-31
```

`<거래ID>`는 list에서 확인한 실제 ID로 바꿉니다. 모든 명령과 하위 명령은 `--help`를 지원합니다. 기본 limit은 10, top은 3입니다.

update는 옵션형입니다. `--date`, `--type`, `--category`, `--amount`, `--memo`, `--tags` 중 지정한 필드만 수정합니다. ID는 유지됩니다. 메모·태그를 비우려면 `--memo ""`, `--tags ""`를 사용합니다. PowerShell 5.1의 빈 인자 전달 문제가 있으면 cmd 터미널에서 실행하세요.

카테고리 추가·삭제는 이름을 대화형으로 받습니다. 기본 분류는 `food`, `transport`, `salary`, `etc`입니다. 중복·빈 이름은 거부하고 사용 중인 분류는 삭제하지 않습니다.

검색은 조건을 AND로 결합합니다. 기간 양 끝을 포함하며 분류·종류·태그는 정확히 일치해야 합니다. 메모는 대소문자를 무시한 부분 검색입니다. 조건 없는 search는 전체 조회입니다. 최신 날짜순으로 출력하며 같은 날짜에서는 나중에 저장한 거래가 먼저입니다.

월 요약은 수입·지출·잔액과 지출 카테고리 TOP N을 출력합니다. 예산이 있으면 사용률을 표시하고 지출이 예산보다 클 때 경고합니다. 빈 월은 데이터 없음을 표시합니다. 같은 월 예산 재설정은 갱신입니다.

## 저장 위치와 형식

기본 경로는 실행 위치의 `./data`입니다. 최초 실행 시 폴더와 파일을 생성하고 카테고리가 비어 있으면 기본 분류를 생성합니다. 다른 폴더는 서브명령 앞에 지정합니다.

```powershell
python -m budget_app --data-dir ./practice-data list
```

UTF-8 JSONL로 한 줄에 객체 하나를 저장합니다.

| 파일 | 필드 |
| --- | --- |
| `data/transactions.jsonl` | id, type, date, amount, category, memo, tags |
| `data/categories.jsonl` | name |
| `data/budgets.jsonl` | month, amount |

```json
{"id":"예시-ID","type":"expense","date":"2024-01-15","amount":5000,"category":"food","memo":"점심","tags":["meal","lunch"]}
```

변경 결과는 같은 폴더의 임시 파일에 기록·검증하고 닫은 후 원본과 교체합니다. 잘못된 입력·손상 행·없는 ID에서는 원본을 교체하지 않습니다. 단일 프로세스 실행을 가정하며 동시 실행 충돌 방지와 여러 파일의 통합 트랜잭션은 지원하지 않습니다.

## CSV 계약

UTF-8과 헤더를 사용합니다. 가져오기는 UTF-8 BOM도 허용합니다.

| 열 | 필수 | 형식 |
| --- | --- | --- |
| date | 예 | YYYY-MM-DD |
| type | 예 | income / expense |
| category | 예 | 등록된 분류 |
| amount | 예 | 양수 정수 |
| memo | 아니요 | 문자열 |
| tags | 아니요 | 쉼표 구분 문자열 |

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,5000,"친구와 점심, 분식","meal,lunch"
```

가져오기는 모든 행이 성공해야 반영합니다. 실패하면 원본을 유지하고 CSV 행 번호를 안내합니다. 매번 새 ID를 생성하므로 같은 CSV를 다시 가져오면 중복 거래가 추가됩니다. 헤더만 있으면 0건 성공입니다.

내보내기는 월 또는 시작일·종료일을 요구하고 두 방식을 혼용할 수 없습니다. 결과가 없으면 헤더만 저장합니다. 원본 JSONL 경로로 내보내기는 거부합니다. 기존 출력 CSV도 실패 시 유지됩니다.

## 샘플 실행

새 폴더를 사용하고 import는 한 번만 실행하세요.

```powershell
python -m budget_app --data-dir ./verify-data import --from examples/transactions.csv
python -m budget_app --data-dir ./verify-data budget set --month 2024-01 --amount 5000
python -m budget_app --data-dir ./verify-data summary --month 2024-01
```

예상 결과: 4건 가져오기, 1월 수입 20,000원·지출 6,500원·잔액 13,500원, 예산 사용률 130.0%와 초과 경고입니다. 전체 목록의 최신 날짜는 2월 1일입니다.

## 구조와 과제 조건

| 모듈 | 책임 |
| --- | --- |
| `models.py` | Transaction dataclass, 날짜·금액·태그 검증 |
| `repository.py` | Repository 클래스, JSONL 제너레이터, 초기화·안전한 쓰기 |
| `service.py` | BudgetService 클래스, 업무 규칙·합계·CSV·디스크 정렬 |
| `cli.py` | argparse, 대화형 입력, 출력 |
| `errors.py` | AppError, CLI 공통 오류 처리 데코레이터 |
| `__main__.py` | main 호출과 종료 코드 전달 |

파일은 한 줄씩 읽고 제너레이터로 전달합니다. 최신순 정렬은 임시 파일 기반 SQLite에 저장한 뒤 커서를 순회합니다. SQLite는 표준 라이브러리이며 영구 저장은 JSONL입니다. 전체 거래를 Python 리스트에 올리지 않지만 첫 결과 전 전체 순회와 임시 디스크 공간이 필요합니다. 요약은 카테고리별 합계를 메모리에 누적합니다.

`@handle_errors`를 CLI 진입 함수에 적용했습니다. 정상 종료는 0, 사용자 입력·파일 오류는 1입니다. 오류는 원인과 해결 힌트로 표시합니다. PowerShell에서는 명령 직후 `$LASTEXITCODE`로 확인합니다.

## 검증과 자료

```powershell
python -m unittest discover -s tests -v
```

실제 CLI 프로세스, 저장과 재실행, CSV 왕복, 검색·예산, 오류 시 원본 보존을 검증합니다. [검증 결과](docs/05_VERIFICATION.md)에 환경과 확인 범위를 기록했습니다.

- [과제 요구사항](docs/01_REQUIREMENTS.md)
- [Python 핵심 개념](docs/02_PYTHON_GUIDE.md)
- [구현 학습 자료](docs/03_IMPLEMENTATION_LAB.md)
- [수동 제출 점검표](docs/04_SUBMISSION_CHECKLIST.md)
