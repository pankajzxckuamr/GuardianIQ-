from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
from app.modules.ai_model.routes import router as ai_model_router
from app.modules.agent.routes import router as agent_router
from app.modules.recommendation.routes import router as recommendation_router
from app.modules.approval.routes import router as approval_router

APP_VERSION = "0.1.0"

app = FastAPI(
    title="GuardianIQ",
    version=APP_VERSION
)

# ── CORS ── Allow frontend dev server + any localhost port ────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Request-Time"],
)

# Add middleware (order matters - innermost will execute first)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ResponseStandardizationMiddleware)
app.add_middleware(RequestIDMiddleware)

add_exception_handlers(app)


from app.modules.foundation.routes import router as foundation_router
from app.modules.registry.routes import router as registry_router

app.include_router(auth_router)
app.include_router(department_router)
app.include_router(audit_router)
app.include_router(policy_router)
app.include_router(datasource_router)
app.include_router(ai_model_router)
app.include_router(agent_router)
app.include_router(recommendation_router)
app.include_router(approval_router)
app.include_router(foundation_router)
app.include_router(registry_router)

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
    import time
    try:
        start_time = time.time()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        latency = (time.time() - start_time) * 1000

        return ResponseHelper.success(
            message="Database connection successful",
            data={
                "status": "healthy",
                "database": "healthy",
                "latency_ms": latency
            }
        )

    except Exception as e:
        from fastapi.responses import JSONResponse
        error_response = ResponseHelper.error(
            message=f"Database connection failed: {str(e)}",
            data={
                "status": "unhealthy",
                "database": "unhealthy"
            }
        )
        return JSONResponse(
            status_code=503,
            content=error_response.model_dump()
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
