from contextlib import asynccontextmanager
from app.db.session import SessionLocal

@asynccontextmanager
async def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
