from typing import Any, Dict, Optional, Type

from fastapi import status
from fastapi.responses import JSONResponse


class CustomException(Exception):
    """커스텀 Exception 부모 클래스"""

    STATUS_CODE = status.HTTP_400_BAD_REQUEST  # 실제 HTTP Status 코드
    ERROR_CODE = STATUS_CODE  # 커스텀 에러 파트 -> 따로 정의해놓은 에러 없으면, STATUS_CODE 그대로 사용
    DEFAULT_MESSAGE = "오류가 발생했습니다."

    def __init__(
        self,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        self.http_status_code = self.STATUS_CODE
        self.response = {
            "status_code": self.ERROR_CODE,
            "message": detail or self.DEFAULT_MESSAGE,
            "data": error_code if error_code else None,
        }
        self.headers = headers


class UnknownException(CustomException):
    """알 수 없는 에러"""

    STATUS_CODE = status.HTTP_500_INTERNAL_SERVER_ERROR
    DEFAULT_MESSAGE = "알 수 없는 오류가 발생했습니다."


async def exception_handler(_, exc: Exception):
    """CustomException 예외 발생 시 처리"""

    return JSONResponse(
        status_code=exc.http_status_code,
        content=exc.response,
        headers=exc.headers,
    )
