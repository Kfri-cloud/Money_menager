# 나만의 용돈 기입장

Python으로 만드는 파일 기반 콘솔 용돈 기입장 과제입니다. 거래를 기록하고 검색하며, 월별 수입·지출과 예산을 확인하는 프로그램을 목표로 합니다.

## 현재 상태

현재 저장소에는 과제 원본과 학습 문서가 있습니다. `Script/main.py`는 아직 비어 있으므로 아래 명령은 **구현 목표를 보여주는 예시**이며 지금은 실행되지 않습니다.

- 과제 원본: [`Plan/my money storage.pdf`](Plan/my%20money%20storage.pdf)
- Python 기본 기능 학습 문서: [`docs/FEATURE_SPEC.md`](docs/FEATURE_SPEC.md)
- 1일차 실습: [`docs/DAY1_LESSON.md`](docs/DAY1_LESSON.md)
- 2일차 실습: [`docs/DAY2_LESSON.md`](docs/DAY2_LESSON.md)
- 3일차 실습: [`docs/DAY3_LESSON.md`](docs/DAY3_LESSON.md)
- 4일차 실습: [`docs/DAY4_LESSON.md`](docs/DAY4_LESSON.md)
- 5일차 실습: [`docs/DAY5_LESSON.md`](docs/DAY5_LESSON.md)
- 5일 진행 지표와 제출 점검표: [`docs/FIVE_DAY_PROGRESS.md`](docs/FIVE_DAY_PROGRESS.md)

3~5일차 학습 자료에는 거래 관리, 월별 계산, CSV 처리의 구현 예시가 문서 안에 있습니다. 예시를 참고해 제출용 `budget_app`을 단계적으로 작성합니다.

## 구현할 기능

| 명령 | 역할 |
| --- | --- |
| `add` | 날짜, 타입, 카테고리, 금액, 메모, 태그를 입력받아 거래 추가 |
| `list` | 거래를 최신순으로 조회하고 `--limit` 적용 |
| `search` | 기간, 카테고리, 타입, 메모, 태그로 거래 검색 |
| `summary` | 월별 총수입, 총지출, 잔액, 지출 카테고리 TOP N 확인 |
| `budget` | 월별 예산 설정 및 요약에서 사용률·초과 여부 확인 |
| `category` | 카테고리 추가, 목록 조회, 삭제 |
| `update` | ID로 거래 수정 |
| `delete` | ID로 거래 삭제 |
| `import` | CSV 거래 가져오기 |
| `export` | 거래를 CSV로 내보내기 |

## 실행 형태(구현 예정)

개발 환경은 Python 3.10 이상이며 외부 패키지는 사용하지 않습니다. 과제에서 권장하는 실행 형태는 다음과 같습니다.

```bash
python -m budget_app <command> [options]
```

명령 예시:

```bash
python -m budget_app add
python -m budget_app list --limit 10
python -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food
python -m budget_app summary --month 2024-01 --top 3
python -m budget_app budget set --month 2024-01 --amount 500000
python -m budget_app category list
python -m budget_app update --id TX-000012 --amount 17000
python -m budget_app delete --id TX-000012
python -m budget_app import --from import.csv
python -m budget_app export --out export.csv --month 2024-01
```

각 명령의 `--help`에서도 사용법을 확인할 수 있도록 구현합니다.

## 저장 형식(구현 예정)

거래, 카테고리, 예산은 프로그램 종료 후에도 남도록 파일을 분리해 저장합니다. 저장 형식은 JSONL 또는 CSV 중 하나를 선택해 일관되게 사용합니다.

```text
data/
├─ transactions.<fmt>
├─ categories.<fmt>
└─ budgets.<fmt>
```

기본 저장 폴더는 `./data`로 두고 `--data-dir` 옵션으로 변경할 수 있게 만드는 것을 권장합니다. 현재는 저장 형식과 파일 위치가 코드로 확정되지 않았습니다.

## CSV 형식(구현 예정)

가져오기와 내보내기에 사용할 최소 열은 아래와 같습니다. UTF-8 인코딩과 헤더 행을 사용합니다.

| 열 | 필수 | 값 |
| --- | --- | --- |
| `date` | 예 | `YYYY-MM-DD` |
| `type` | 예 | `income` 또는 `expense` |
| `category` | 예 | 등록된 카테고리 이름 |
| `amount` | 예 | 양의 정수 |
| `memo` | 아니요 | 메모 문자열 |
| `tags` | 아니요 | 쉼표로 구분한 태그 |

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,점심,"meal,lunch"
```

## 개발 순서

1. 거래 모델과 입력 검증을 만든다.
2. 거래·카테고리·예산을 저장하는 파일 계층을 만든다.
3. 거래 추가·목록·수정·삭제를 구현한다.
4. 검색·월별 요약·예산·카테고리 관리를 구현한다.
5. CSV 가져오기·내보내기와 오류 처리를 구현한다.
6. 명령별 도움말과 테스트를 추가하고 실제 실행법에 맞게 이 README를 갱신한다.

구현에 필요한 Python 함수와 표준 라이브러리는 [학습 문서](docs/FEATURE_SPEC.md)에 예제와 함께 정리되어 있습니다.
