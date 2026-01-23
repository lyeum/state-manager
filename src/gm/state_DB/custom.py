# src/gm/state_DB/custom.py
# CustomStatus, CommonResponse, WrappedResponse, CustomJSONResponse 정의

from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ====================================================================
# 응답 상태 Enum
# ====================================================================


class CustomStatus(str, Enum):
    """API 응답 상태 코드"""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


# ====================================================================
# 공통 응답 모델
# ====================================================================


class CommonResponse(BaseModel):
    """
    모든 API 응답의 기본 구조

    Examples:
        성공: {"status": "success", "data": {...}, "message": "Operation completed"}
        실패: {"status": "error", "data": null, "message": "Error details"}
    """

    status: CustomStatus = Field(
        default=CustomStatus.SUCCESS, description="응답 상태 (success/error/warning)"
    )
    data: Optional[object] = Field(default=None, description="실제 응답 데이터")
    message: Optional[str] = Field(default=None, description="사용자에게 보여줄 메시지")

    class Config:
        use_enum_values = True  # Enum을 문자열로 직렬화


# ====================================================================
# Swagger 문서화용 제네릭 래퍼
# ====================================================================

T = TypeVar("T")  # 제네릭 타입 변수


class WrappedResponse(BaseModel, Generic[T]):
    """
    Swagger에 표시될 전체 구조 모델
    response_model에서 사용하여 타입 안전성 확보

    Usage:
        @app.get("/users", response_model=WrappedResponse[List[UserSchema]])
        async def get_users():
            ...
    """

    status: CustomStatus = CustomStatus.SUCCESS
    data: T
    message: Optional[str] = None

    class Config:
        use_enum_values = True


# ====================================================================
# 커스텀 JSON 응답 클래스
# ====================================================================


class CustomJSONResponse(JSONResponse):
    """
    모든 API 응답을 표준 포맷으로 래핑하는 커스텀 응답 클래스

    자동으로 응답을 다음 형식으로 변환:
    {
        "status": "success",
        "data": <원본 응답>,
        "message": null
    }
    """

    def render(self, content: Any) -> bytes:
        # 이미 래핑된 응답인지 확인
        if isinstance(content, dict) and "status" in content and "data" in content:
            return super().render(content)

        # 표준 포맷으로 래핑
        wrapped = {
            "status": CustomStatus.SUCCESS.value,
            "data": content,
            "message": None,
        }
        return super().render(wrapped)
