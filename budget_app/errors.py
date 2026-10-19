"""문맥별 종료 코드를 가진 예상 오류."""

class AppError(ValueError):
    def __init__(self, message: str, hint: str = "입력값과 --help를 확인하세요.", code: int = 2):
        super().__init__(message)
        self.hint = hint
        self.code = code


def data_error(message: str) -> AppError:
    return AppError(message, "원본을 백업한 뒤 해당 CSV를 복구하세요. 임의 초기화하지 마세요.", 5)
