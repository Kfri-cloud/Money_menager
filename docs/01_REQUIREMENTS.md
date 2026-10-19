# 요구사항과 기준

최종 구현 기준은 [Plzz 가이드북](../Plzz/B2-1_가계부_구현_가이드북.md)의 확정 정책입니다. [구현 프롬프트](../Plzz/B2-1_VSCode_Codex_구현_프롬프트.md)와 [학습 구조도](../Plzz/budget-learning-map.html)를 함께 참고했습니다. 구조도의 미정 정책보다 가이드북이 우선합니다. 원본 과제 PDF와의 별도 대조는 하지 않았습니다.

- 표준 라이브러리, Python 3.10 이상, `python -m budget_app`.
- Transaction·Category·Budget, CsvRepository·BudgetService로 책임 분리.
- CSV 4개, metadata 순번 ID, 삭제 후 재사용 금지, 숫자 ID 내림차순.
- 대화형 추가·수정·삭제·카테고리·예산 금액 입력.
- 제너레이터 목록·검색, 조건 AND, 대소문자 정규화.
- 월별 요약·TOP·0원/미설정 예산 구분.
- CSV 일괄 가져오기·범위 내보내기, 실패 시 거래 원본 보존.
- 오류 코드 0~5와 위치·힌트, handle_errors 데코레이터.

세부 정책·스키마·보조 선택·제약은 [README](../README.md)에 실제 동작과 함께 정리했습니다. 기존 평가 PDF는 변경하지 않으므로 현재 구현 설명과 차이가 있을 수 있습니다.
