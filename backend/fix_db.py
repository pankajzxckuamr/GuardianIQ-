from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_db():
    engine = create_engine(settings.DATABASE_URL, echo=False)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS governance_events CASCADE;"))
    print("--- Dropped governance_events table ---")
    print("You can now safely run: alembic upgrade head")

if __name__ == "__main__":
    fix_db()
