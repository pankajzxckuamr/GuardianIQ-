from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    status: str
    request_id: str
    message: Optional[str] = None
    data: Optional[T] = None
    error_code: Optional[str] = None
