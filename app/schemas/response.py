from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel
from fastapi import status

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    """Standard response model for successful API responses."""

    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    status_code: int = status.HTTP_200_OK


class ErrorDetail(BaseModel):
    """Model for detailed error information."""

    field: Optional[str] = None
    code: Optional[str] = "error"
    message: str


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = False
    error: Optional[ErrorDetail] = None
    errors: Optional[list[ErrorDetail]] = []
    status_code: int = status.HTTP_400_BAD_REQUEST
    data: Optional[dict[str, Any]] = None
