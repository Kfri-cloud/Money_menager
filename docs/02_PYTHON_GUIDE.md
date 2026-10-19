# Python 학습 안내

[코드 흐름 설명](06_CODE_FLOW.md)을 함수 → 클래스 → 모듈 → 호출 순서로 읽으세요. [Plzz 학습 구조도](../Plzz/budget-learning-map.html)는 개념 참고 자료이며 미정 정책은 구현 가이드북과 README를 따릅니다.

1. `models.py`: dataclass, 필드, date·int·list, default_factory.
2. `validators.py`: 변환, 조건문, raise, 순수 함수.
3. `repositories.py`: CSV 문자열과 객체 변환, yield, with, 임시 파일, os.replace.
4. `services.py`: self, 저장소 객체 공유, 필터링·집계, 디스크 기반 역순 읽기.
5. `cli.py`: argparse, 함수 인자, 대화형 입력, 확인 후 저장.
6. `decorators.py`: 내부 함수, 클로저, *args/**kwargs, wraps, try/except.

타입 힌트는 설명·도구 지원용 계약이고 런타임 검증은 validators가 수행합니다. 제너레이터 오류는 생성할 때가 아니라 순회할 때 발생할 수 있으므로 handler가 순회 전체를 오류 경계 안에서 실행합니다.
