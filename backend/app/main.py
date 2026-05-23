from fastapi import FastAPI
from sqlalchemy import text
from app.db.session import engine
from app.modules.auth.routes import router as auth_router

from app.core.middleware import RequestIDMiddleware, LoggingMiddleware, ResponseStandardizationMiddleware, get_request_id
from app.core.exceptions import add_exception_handlers
from app.shared.responses import StandardResponse
from app.modules.department.routes import router as department_router
from app.modules.audit.routes import router as audit_router
from app.modules.policy.routes import router as policy_router
from app.modules.datasource.routes import router as datasource_router

APP_VERSION = "0.1.0"

app = FastAPI(
    title="GuardianIQ",
    version=APP_VERSION
)

# Add middleware (order matters - innermost will execute first)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ResponseStandardizationMiddleware)
app.add_middleware(RequestIDMiddleware)

add_exception_handlers(app)

app.include_router(auth_router)

app.include_router(department_router)
app.include_router(audit_router)
app.include_router(policy_router)
app.include_router(datasource_router)


@app.get("/api/health", response_model=StandardResponse[dict])
def health_check():
    from app.shared.response_utils import ResponseHelper
    return ResponseHelper.success(
        message="GuardianIQ backend running",
        data={"status": "healthy"}
    )


@app.get("/api/health/db", response_model=StandardResponse[dict])
def db_health_check():
    from app.shared.response_utils import ResponseHelper
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return ResponseHelper.success(
            message="Database connection successful",
            data={"database": "healthy"}
        )

    except Exception as e:
        return ResponseHelper.error(
            message=f"Database connection failed: {str(e)}",
            data=None
        )


@app.get("/api/version", response_model=StandardResponse[dict])
def version():
    """Returns the current API version and application metadata."""
    from app.shared.response_utils import ResponseHelper
    return ResponseHelper.success(
        message="GuardianIQ API version info",
        data={
            "version": APP_VERSION,
            "app": "GuardianIQ",
            "phase": "0"
        }
    )
