# 코드 흐름과 Python 개념

구현 기준은 [Plzz 가이드북](../Plzz/B2-1_가계부_구현_가이드북.md)입니다. 개념은 [학습 구조도](../Plzz/budget-learning-map.html)와 연결해 읽으세요. 아래 설명은 실제 CSV 구현 기준입니다.

## 1. 함수 하나가 하는 일

### models.py — 값 객체

`Transaction`은 id·type·date·amount·category·memo·tags를 담습니다. `Category`는 이름, `Budget`은 월·금액을 담습니다. `@dataclass`가 `__init__`, `__repr__`, `__eq__`를 생성합니다. 필수 필드 뒤에 기본 필드를 두며 `field(default_factory=list)`로 거래마다 별도 태그 리스트를 생성합니다. dataclass는 날짜나 금액을 검증하지 않습니다.

### validators.py — 값 검사 함수

| 함수 | 하는 일 |
|---|---|
| validate_transaction_type | income/expense 검사 |
| validate_date | 정확한 날짜 모양과 실제 날짜 검사, date 반환 |
| integer | bool·소수 배제, 정수 변환과 최솟값 검사 |
| validate_amount | 양수 정수 거래 금액·limit·top 검사 |
| validate_budget_amount | 0 이상 정수 검사 |
| normalize_name | 앞뒤 공백 제거·빈 이름·줄바꿈 거부 |
| validate_category | 등록 목록과 대소문자 무시 비교, 최초 등록 표기 반환 |
| validate_month | YYYY-MM과 실제 연월 검사 |
| normalize_tags | 쉼표 분리·빈 항목 제거·대소문자 무시 중복 제거 |
| id_number | 정규 ID 모양 검사·숫자 부분 반환 |
| validate_period | 열린 날짜 경계 허용·역전 금지, date 쌍 반환 |

이 함수들은 파일을 읽지 않고 필요한 등록 목록을 인자로 받습니다. `raise`는 처리를 중단하고 오류를 호출자에게 전달합니다. `try/except`는 어떤 오류를 어느 문맥으로 바꿔 안내할지 결정합니다. 날짜 변환에는 표준 라이브러리 `datetime.date`를 사용합니다.

### repositories.py — CsvRepository의 메서드

| 메서드/속성 | 하는 일 |
|---|---|
| __init__ | 저장 디렉터리와 네 CSV 경로만 설정 |
| paths | 보호·초기화 검사에 사용할 네 경로 반환 |
| initialize_files | 최초 파일·기본 분류 생성, 부분 유실·기존 JSONL 차단 |
| records | CSV 헤더·행 길이·문법·UTF-8 검사 후 문자열 행 yield |
| write | 임시 CSV 작성·flush/fsync·닫기·os.replace·임시 파일 정리 |
| load_categories | 정규 이름·중복 검사 후 Category 목록 반환 |
| save_categories | Category 목록을 name 행으로 직렬화하여 교체 |
| load_budgets | 월·금액·중복 월 검사 후 월별 Budget 사전 반환 |
| save_budgets | Budget 목록을 월·금액 행으로 저장 |
| last_number | metadata의 단일 키·번호 검사·마지막 발급 번호 반환 |
| iter_transactions | 날짜·금액·카테고리 참조·태그·ID 순서 검사 후 Transaction yield |
| transaction_row | Transaction을 CSV 문자열/숫자 행으로 변환 |
| validate_all | 예산과 거래 전체 순회 검사; 카테고리·metadata도 거래 순회에서 검사 |
| reserve_ids | 전체 검사 후 ID 구간을 metadata에 먼저 영구 확보 |
| prepend_transactions | 새 거래 역순 스트림 뒤에 기존 거래 스트림을 이어 저장 |
| add_transaction | 단건 거래를 맨 앞에 반영 |
| get_transaction | ID 검사 후 스트리밍 조회, 발견하면 파일 닫고 반환 |
| _rewrite | 전체를 순회해 대상 거래 교체/제외, 없으면 오류 |
| update_transaction | _rewrite에 교체 거래 전달 |
| delete_transaction | _rewrite에 None을 전달해 대상 제외 |

CSV 행의 날짜는 문자열이지만 `iter_transactions`는 date로 변환합니다. 저장 시에는 `isoformat()`으로 되돌립니다. 금액도 읽을 때 int로, 태그도 list로 바꿉니다. `records`는 공통 CSV 문법 검사이고 `iter_transactions`는 거래의 의미 검사입니다. 두 검사를 구분해 가져오기에서도 재사용합니다.

`write` 내부의 임시 파일은 원본과 같은 폴더에 있습니다. 행 생성 도중 예외가 발생하면 마지막 교체까지 도달하지 않으므로 원본이 유지됩니다. metadata는 별도 파일이므로 거래와 통합 원자성을 갖지 않습니다.

### services.py — BudgetService의 메서드

| 메서드 | 하는 일 |
|---|---|
| __init__ | 전달받은 저장소 객체를 self.repository에 보관 |
| prepare_transaction | 검증·정규화한 거래 생성, ID 발급·저장하지 않음 |
| add_transaction | 검증 → ID 확보 → 거래 ID 부여 → 단건 저장 |
| list_transactions | limit 검사 후 필요한 건수만 yield |
| search_transactions | 기간·카테고리·유형·메모·태그 AND 필터링, 전부 스트리밍 |
| get_transaction | 저장소의 ID 조회에 위임 |
| preview_update | 기존 거래와 변경값 결합·검증, 저장 전 표시용 거래 반환 |
| update_transaction | 변경 확인 후 전체 검사·저장; 같은 값은 저장 생략 |
| delete_transaction | 존재 확인·전체 검사·삭제 요청 |
| get_monthly_summary | 한 번 순회해 수입/지출/카테고리별 누적, TOP·예산 반환 |
| set_budget | 월·금액 검사·기존 자료 검사·교체, 전후 Budget 반환 |
| get_budget | 월 검사·해당 Budget 또는 None 반환 |
| add_category | 이름·중복 검사 후 최초 표기로 등록 |
| list_categories | 저장소의 Category 목록 반환 |
| delete_category | 전체 검사·사용 중 차단 후 등록 목록에서 제거 |
| import_transactions | 전체 입력 검사·스풀/오프셋 기록·ID 구간 확보·역순 일괄 저장 |
| export_transactions | 필수 범위·저장 경로 보호 검사·필터링·임시 출력 후 교체 |

같은 이름의 `add_transaction`도 서비스는 업무 순서, 저장소는 CSV 반영을 담당합니다. 서비스는 `input()`과 `print()`를 하지 않으므로 CLI 없이 테스트할 수 있습니다. 검색은 필터링이고 요약은 누적·그룹별 집계입니다. TOP은 작은 카테고리 집계만 정렬하며 전체 거래를 정렬하지 않습니다.

가져오기는 `spool`에 JSON 레코드를 쓰고 `index`에 레코드 시작 위치를 8바이트로 기록합니다. 내부 함수 `new_transactions`가 인덱스를 뒤에서부터 읽어 입력 역순으로 새 거래를 만듭니다. JSON의 줄바꿈 이스케이프 덕분에 CSV 여러 줄 셀도 온전히 유지됩니다. 이 임시 JSON은 영구 저장 형식과 별개입니다.

### cli.py — 화면과 명령 함수

| 함수/메서드 | 하는 일 |
|---|---|
| Parser.__init__ | argparse 기본 -h를 끄고 --help만 등록 |
| Parser.error | 파싱 오류를 힌트가 있는 AppError(2)로 전환 |
| create_parser | 모든 명령·옵션·기본값·handler 연결 |
| show_transaction | 거래 한 건 표시 |
| show_transactions | 제너레이터 순회·0건 안내·도중 오류 시 불완전 목록 표시 |
| confirm | y/yes만 True 반환 |
| handle_add | 등록 분류 표시·입력·추가·새 ID 출력 |
| handle_list | limit을 서비스에 전달하고 결과 순회 |
| handle_search | 검색 옵션 전달·전부 순회 출력 |
| handle_update | 현재 값·변경 입력·검증·전후 표시·승인 후 저장 |
| handle_delete | 대상 표시·확인 후 삭제 |
| show_budget | 미설정·0원·사용률·초과 상태 표시 |
| handle_summary | 전체 집계가 끝난 결과만 출력 |
| handle_budget | 대화형 금액 설정·전후 안내 또는 예산 조회 |
| handle_category | 이름 입력·등록/삭제 또는 목록 출력 |
| handle_import | 파일 경로 전달·처리 건수 출력 |
| handle_export | 출력 경로·범위 전달·처리 건수 출력 |
| main | 파싱·초기화·서비스 생성·선택 handler 실행·정수 코드 반환 |

`handle_*`와 `main`의 `@handle_errors`는 함수 호출과 실제 순회를 감쌉니다. handler가 처리한 오류는 코드로 반환되어 바깥 main에서 중복 안내하지 않습니다. 초기화·파싱 오류는 main 경계에서 안내합니다. argparse의 help용 SystemExit는 잡지 않아 정상 코드 0을 유지합니다.

### decorators.py와 errors.py

`handle_errors(function)`은 내부 `wrapper(*args, **kwargs)`를 반환합니다. wrapper는 원래 함수를 호출하고 오류 종류에 따라 코드 0~5로 바꿉니다. `functools.wraps`는 함수 이름·문서 같은 메타데이터를 보존합니다. 내부 오류는 DEBUG 로거에 스택 정보를 전달하고 화면에는 짧은 안내만 보여 줍니다.

`AppError.__init__`는 메시지·힌트·코드를 보관합니다. `data_error`는 저장/가져오기 자료 손상을 코드 5와 복구 힌트로 만드는 보조 함수입니다. 같은 검증 오류라도 직접 입력은 2/3, CSV 문맥에서는 5로 다시 분류합니다.

`__main__.py`는 `main()`의 반환 코드를 `SystemExit`에 전달합니다. `__init__.py`는 import만으로 저장 파일을 만들지 않습니다.

## 2. 메서드가 모인 클래스의 역할

- Transaction·Category·Budget: 화면·파일과 분리된 자료 구조.
- CsvRepository: 파일 경로와 CSV 변환·검사·교체·ID 확보.
- BudgetService: 규칙과 저장 순서를 연결하고 검색·집계 수행.
- Parser: argparse 사용법과 오류 형식 조정.
- AppError: 사용자에게 안내할 오류 정보 전달.

`self`는 현재 객체입니다. `BudgetService(repository)`를 만들면 전달한 저장소 객체를 보관해 모든 메서드가 같은 경로를 사용합니다. 거래 전체를 메모리에서 공유한다는 뜻은 아닙니다.

## 3. 클래스·함수가 모인 모듈의 역할

모듈은 Python 파일이고 패키지는 관련 모듈을 묶는 디렉터리입니다. `budget_app` 패키지의 의존성은 `cli → services → repositories → models/validators/errors` 방향입니다. validators도 모델과 오류를 사용합니다. 데코레이터는 CLI 오류 경계만 담당합니다. CSV에서 CLI로 역방향 의존하지 않아 순환 import를 피합니다.

## 4. 실제 호출 흐름

1. `python -m budget_app` → `__main__` → `main`.
2. `create_parser`로 파싱합니다. help는 저장 파일 생성 전에 끝납니다.
3. `CsvRepository`와 파일을 초기화하고 `BudgetService`를 만듭니다.
4. `args.handler(args, service)`로 해당 명령에 인자를 전달합니다.
5. 추가: 입력 → `prepare_transaction` → `reserve_ids` → `add_transaction` → 임시 CSV 교체.
6. 목록/검색: 저장소 yield → 서비스 필터/limit → CLI 출력. 오류는 실제 순회 중 잡습니다.
7. 수정: 조회 → 입력 → `preview_update` → 전후 표시 → 확인 → `update_transaction`.
8. 요약: 전체 순회 성공 → 결과 사전 반환 → 화면 출력. 도중 손상이 있으면 숫자를 표시하지 않습니다.
9. 가져오기: 전체 입력 검증·스풀 → 기존 자료 검사 → ID 확보 → 역순 신규 거래+기존 거래 → 단일 거래 CSV 교체.
10. 반환 코드 → SystemExit → 운영체제 종료 코드.

## 5. 초보자 용어

| 용어 | 뜻 |
|---|---|
| 초기화 | 객체의 시작 상태를 설정하는 일; 파일 초기화는 별도 메서드로 구분 |
| 필드 | 객체가 보관하는 값의 이름 |
| 타입 힌트 | 기대하는 값 종류를 표시하는 주석 성격의 계약 |
| 반환값 | 함수가 호출한 쪽으로 돌려주는 결과 |
| 인자 | 함수 호출 시 전달한 값; **사전은 키별 인자로 펼침 |
| yield | 한 결과를 내주고 다음 요청까지 멈춤 |
| 지연 실행 | 제너레이터를 만들 때가 아니라 next/for에서 실제 읽음 |
| 소진 | 제너레이터를 끝까지 읽어 더 반환할 결과가 없는 상태 |
| with/closing | 정상·오류·중간 종료 때 파일/제너레이터 정리를 돕는 문맥 |
| 클로저 | 내부 함수가 바깥 함수의 function·count·spool 같은 값을 참조하는 구조 |
| *args/**kwargs | 위치/이름 인자를 모으거나 다시 전달하는 문법 |
| 원자적 교체 | 한 파일의 마지막 이름 교체 단계에서 완성본으로 바꾸는 일 |

함수별 테스트를 그대로 복제하기보다 실제 사용 정책과 실패 시 바이트 보존을 검증합니다. [검증 기록](05_VERIFICATION.md)에서 범위를 확인하세요.
