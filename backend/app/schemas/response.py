from typing import Any
from pydantic import BaseModel


class SuccessResponse(BaseModel):
    success: bool = True
    status: int
    message: str
    data: Any
    metadata: dict = {}


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    error_code: str
    metadata: dict = {}
