"""명령 경계에서 오류를 안내하고 종료 코드로 변환한다."""
import logging
import sys
from functools import wraps
from .errors import AppError


def handle_errors(function):
    @wraps(function)
    def wrapper(*args, **kwargs) -> int:
        try:
            return function(*args, **kwargs)
        except AppError as error:
            print(f"[오류] {error}\n[힌트] {error.hint}", file=sys.stderr)
            return error.code
        except OSError as error:
            print(f"[오류] 파일 접근·저장 실패: {error}\n[힌트] 경로·권한·여유 공간을 확인하세요.", file=sys.stderr)
            return 4
        except (EOFError, KeyboardInterrupt):
            print("입력이 취소되었습니다.", file=sys.stderr)
            return 0
        except Exception as error:
            logging.getLogger(__name__).debug("내부 오류", exc_info=True)
            print(f"[오류] 내부 오류: {error}\n[힌트] 개발자에게 오류 내용을 전달하세요.", file=sys.stderr)
            return 1
    return wrapper
