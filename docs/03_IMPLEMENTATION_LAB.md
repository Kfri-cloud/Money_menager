# 구현 확인 실습

아래 명령은 저장소 루트에서 실행합니다. 새 실습 폴더를 쓰고 같은 CSV를 반복 가져오면 중복 거래가 추가된다는 점을 확인하세요.

```powershell
python -m budget_app --data-dir ./practice-data import --file examples/transactions.csv
python -m budget_app --data-dir ./practice-data list
python -m budget_app --data-dir ./practice-data summary --month 2026-10
python -m budget_app --data-dir ./practice-data budget set --month 2026-10
python -m budget_app --data-dir ./practice-data summary --month 2026-10
python -m budget_app --data-dir ./practice-data search --tags MEAL,lunch --q 점심
python -m budget_app --data-dir ./practice-data update --id TX-000003
python -m budget_app --data-dir ./practice-data delete --id TX-000004
python -m budget_app --data-dir ./practice-data export --file october.csv --month 2026-10
```

최초 샘플 1회 가져오기 직후 10월은 수입 20,000원·지출 6,500원·잔액 13,500원입니다. 예산에 5,000원을 입력하면 130%와 초과 경고가 나옵니다. 0원을 입력하면 사용률 계산 불가와 초과 경고가 나옵니다. 수정·삭제는 y/yes로 승인하며 그 외 응답은 취소합니다. 날짜를 바꿔도 목록 위치는 ID 순서로 유지됩니다.

`python` 실행 별칭 문제의 대안은 README를 참고하세요. `practice-data`와 `october.csv`는 사용자가 만든 실습 데이터이며 프로그램이 자동 삭제하지 않습니다.
