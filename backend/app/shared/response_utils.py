"""
Response utilities and helpers for standardized API responses.
"""

from typing import TypeVar, Generic, Optional, Any, List
from app.shared.responses import StandardResponse
from app.core.middleware import get_request_id

T = TypeVar('T')


class ResponseHelper:
    """Helper class for constructing standardized responses."""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = None,
        status_code: int = 200,
        request_id: Optional[str] = None
    ) -> StandardResponse:
        """Create a success response."""
        return StandardResponse(
            status="success",
            request_id=request_id or get_request_id(),
            message=message,
            data=data
        )
    
    @staticmethod
    def error(
        message: str,
        data: Any = None,
        status_code: int = 400,
        request_id: Optional[str] = None
    ) -> StandardResponse:
        """Create an error response."""
        return StandardResponse(
            status="error",
            request_id=request_id or get_request_id(),
            message=message,
            data=data
        )
    
    @staticmethod
    def created(
        data: Any,
        message: str = "Resource created successfully"
    ) -> StandardResponse:
        """Create a created response (201)."""
        return StandardResponse(
            status="success",
            request_id=get_request_id(),
            message=message,
            data=data
        )
    
    @staticmethod
    def paginated(
        items: List[Any],
        total: int,
        page: int = 1,
        page_size: int = 10,
        message: str = None
    ) -> StandardResponse:
        """Create a paginated response."""
        return StandardResponse(
            status="success",
            request_id=get_request_id(),
            message=message,
            data={
                "items": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "pages": (total + page_size - 1) // page_size
                }
            }
        )
    
    @staticmethod
    def list_response(
        items: List[Any],
        message: str = None
    ) -> StandardResponse:
        """Create a list response."""
        return StandardResponse(
            status="success",
            request_id=get_request_id(),
            message=message,
            data=items
        )
