from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Any
from datetime import datetime

T = TypeVar('T')

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    status: str
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: Optional[str] = None
    data: Optional[T] = None
    error_code: Optional[str] = None
    error: Optional[ErrorDetail] = None

class PaginatedResponse(StandardResponse[T], Generic[T]):
    total: int
    page: int
    page_size: int
    items: list[T]
