from fastapi import FastAPI
from sqlalchemy import text
from app.db.session import engine
from app.modules.auth.routes import router as auth_router


app = FastAPI(
    title="GuardianIQ"
)

app.include_router(auth_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "success",
        "message": "GuardianIQ backend running"
    }


@app.get("/api/health/db")
def db_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "success",
            "message": "Database connection successful"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
