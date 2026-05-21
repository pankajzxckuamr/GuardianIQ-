from fastapi import FastAPI
from sqlalchemy import text
from app.db.session import engine
from app.modules.auth.routes import router as auth_router

from app.core.logging import RequestIDMiddleware
from app.core.exceptions import add_exception_handlers, get_request_id
from app.shared.responses import StandardResponse


app = FastAPI(
    title="GuardianIQ"
)

app.add_middleware(RequestIDMiddleware)
add_exception_handlers(app)

app.include_router(auth_router)


@app.get("/api/health", response_model=StandardResponse[dict])
def health_check():
    return StandardResponse(
        status="success",
        request_id=get_request_id(),
        message="GuardianIQ backend running",
        data=None
    )


@app.get("/api/health/db", response_model=StandardResponse[dict])
def db_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return StandardResponse(
            status="success",
            request_id=get_request_id(),
            message="Database connection successful",
            data=None
        )

    except Exception as e:
        return StandardResponse(
            status="error",
            request_id=get_request_id(),
            message=str(e),
            data=None
        )
