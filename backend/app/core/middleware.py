"""
Centralized middleware for request/response handling.
Handles request ID propagation, response standardization, and logging.
"""

import uuid
import contextvars
import json
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.shared.responses import StandardResponse
import logging

logger = logging.getLogger(__name__)

request_id_context = contextvars.ContextVar("request_id", default="unknown")
user_context = contextvars.ContextVar("user", default=None)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and propagate request IDs.
    Sets request ID in context for use throughout the request lifecycle.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extract or generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Set in context
        token = request_id_context.set(request_id)
        
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Request-Time"] = str(time.time())
            return response
        finally:
            request_id_context.reset(token)


class ResponseStandardizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to standardize all responses through StandardResponse.
    Only wraps successful responses; error responses are handled by exception handlers.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip OpenAPI, docs paths, and the login endpoint (OAuth2 spec requires
        # access_token at root level - middleware must not re-wrap it)
        SKIP_PATHS = ["/openapi.json", "/docs", "/redoc", "/api/auth/login"]
        if request.url.path in SKIP_PATHS:
            return await call_next(request)
            
        # Get the original response
        response = await call_next(request)
        
        # Only process JSON responses that aren't already error responses
        if response.status_code >= 200 and response.status_code < 300:
            if "application/json" in response.headers.get("content-type", ""):
                # Read the response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                try:
                    data = json.loads(body) if body else None
                    
                    # Check if already wrapped in StandardResponse
                    if not self._is_already_wrapped(data):
                        # Wrap in StandardResponse
                        standardized = StandardResponse(
                            status="success",
                            request_id=get_request_id(),
                            data=data
                        )
                        
                        response = JSONResponse(
                            status_code=response.status_code,
                            content=standardized.model_dump()
                        )
                        response.headers["X-Request-ID"] = get_request_id()
                    else:
                        # Reconstruct the response since we consumed the iterator
                        headers = dict(response.headers)
                        if "content-length" in headers:
                            del headers["content-length"]
                        response = Response(
                            content=body,
                            status_code=response.status_code,
                            headers=headers,
                            media_type="application/json"
                        )
                except (json.JSONDecodeError, Exception):
                    # If we can't parse, just reconstruct original response
                    headers = dict(response.headers)
                    if "content-length" in headers:
                        del headers["content-length"]
                    response = Response(
                        content=body,
                        status_code=response.status_code,
                        headers=headers,
                        media_type="application/json"
                    )
        
        return response
    
    @staticmethod
    def _is_already_wrapped(data):
        """Check if response is already wrapped in StandardResponse."""
        if isinstance(data, dict):
            return "status" in data and "request_id" in data
        return False


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured logging with request ID propagation.
    """
    
    async def dispatch(self, request: Request, call_next):
        request_id = get_request_id()
        user = user_context.get()
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={"request_id": request_id, "user": user}
        )
        
        # Time the request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"[{request_id}] {response.status_code} {request.method} {request.url.path} ({duration:.2f}s)",
            extra={"request_id": request_id, "duration": duration, "status": response.status_code}
        )
        
        return response


def get_request_id() -> str:
    """Get the current request ID from context."""
    try:
        return request_id_context.get()
    except LookupError:
        return "unknown"


def set_user_context(user_id: str, user_email: str = None):
    """Set user information in context for logging."""
    user_context.set({"user_id": user_id, "email": user_email})


def get_user_context() -> dict:
    """Get user information from context."""
    try:
        return user_context.get()
    except LookupError:
        return None
