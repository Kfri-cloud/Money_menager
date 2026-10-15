"""사용자에게 보여 줄 오류와 CLI 경계의 공통 처리."""
import sys
from functools import wraps
from typing import Callable


class AppError(ValueError):
    def __init__(self, message: str, hint: str = "입력값과 --help의 사용 예시를 확인하세요."):
        super().__init__(message)
        self.hint = hint


def handle_errors(function: Callable) -> Callable:
    @wraps(function)
    def wrapper(*args, **kwargs) -> int:
        try:
            return function(*args, **kwargs)
        except AppError as error:
            print(f"[오류] {error}\n[힌트] {error.hint}", file=sys.stderr)
        except (OSError, UnicodeError) as error:
            print(f"[오류] 파일 처리 실패: {error}\n[힌트] 경로·권한과 UTF-8 인코딩을 확인하세요.", file=sys.stderr)
        except (EOFError, KeyboardInterrupt):
            print("[오류] 입력이 취소되었습니다.\n[힌트] 명령을 다시 실행하세요.", file=sys.stderr)
        return 1
    return wrapper
