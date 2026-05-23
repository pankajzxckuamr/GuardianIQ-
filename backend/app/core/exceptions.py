from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.shared.responses import StandardResponse
from app.core.middleware import get_request_id
import traceback

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        error_messages = []
        for error in errors:
            field = ".".join(str(loc) for loc in error.get("loc", []))
            error_messages.append(f"{field}: {error.get('msg')}")
        
        message = "Validation Error: " + ", ".join(error_messages)
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=StandardResponse(
                status="error",
                request_id=get_request_id(),
                message=message,
                data=None
            ).model_dump()
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=StandardResponse(
                status="error",
                request_id=get_request_id(),
                message=str(exc.detail),
                data=None
            ).model_dump()
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # In a real app, log the traceback here.
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=StandardResponse(
                status="error",
                request_id=get_request_id(),
                message="An unexpected internal server error occurred.",
                data=None
            ).model_dump()
        )
