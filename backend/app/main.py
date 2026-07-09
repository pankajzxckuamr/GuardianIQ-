import os
import time
from datetime import datetime, timezone

START_TIME = time.time()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.db.session import engine
import app.db.base
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

from contextlib import asynccontextmanager

import os
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Apply missing DB columns and triggers on startup
    from sqlalchemy import text
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE workflow_schedule_history ADD COLUMN IF NOT EXISTS changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;"))
            conn.execute(text("ALTER TABLE workflow_run_steps ADD COLUMN IF NOT EXISTS error_detail TEXT;"))
            conn.execute(text("ALTER TABLE workflow_run_outputs ADD COLUMN IF NOT EXISTS raw_output TEXT;"))
            conn.execute(text("ALTER TABLE workflow_run_failures ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMP WITH TIME ZONE;"))
            conn.execute(text("ALTER TABLE workflow_schedule_approvals ADD COLUMN IF NOT EXISTS approver_group_id UUID;"))
            conn.execute(text("ALTER TABLE workflow_notifications ADD COLUMN IF NOT EXISTS related_entity_type VARCHAR(100);"))
            conn.execute(text("ALTER TABLE workflow_notifications ADD COLUMN IF NOT EXISTS related_entity_id UUID;"))
            # Load missing triggers
            trigger_sql_path = os.path.join(os.path.dirname(__file__), "..", "..", "database", "ddl", "V2_FIX_003__missing_triggers.sql")
            if os.path.exists(trigger_sql_path):
                with open(trigger_sql_path, "r") as f:
                    conn.execute(text(f.read()))
    except Exception as e:
        print(f"DB Patch Error: {e}")
    yield

app = FastAPI(
    title="GuardianIQ",
    version=APP_VERSION,
    lifespan=lifespan
)

from app.shared.audit_listeners import setup_audit_listeners
setup_audit_listeners()

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
from app.modules.orchestration.routes import router as orchestration_router
from app.api.phase2_authorization_routes import router as phase2_auth_router
from app.api.phase2_scheduler_routes import router as phase2_scheduler_router
from app.api.phase2_run_routes import router as phase2_run_router
from app.api.phase2_notification_routes import router as phase2_notification_router

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
app.include_router(orchestration_router, prefix="/api/orchestration", tags=["Orchestration"])

# Feature flag for Phase 2 endpoints
if os.getenv("PHASE2_SCHEDULER_ENABLED", "True").lower() == "true":
    app.include_router(phase2_auth_router)
    app.include_router(phase2_scheduler_router)
    app.include_router(phase2_run_router)
    app.include_router(phase2_notification_router)

@app.get("/api/health", response_model=StandardResponse[dict])
def health_check():
    from app.shared.response_utils import ResponseHelper
    uptime = time.time() - START_TIME
    return ResponseHelper.success(
        message="GuardianIQ backend running",
        data={
            "status": "healthy",
            "version": APP_VERSION,
            "uptime": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
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
