from sqlalchemy import create_engine, text
from app.core.config import settings

def check_db():
    engine = create_engine(settings.DATABASE_URL, echo=False)
    with engine.connect() as conn:
        # Get Alembic version
        try:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f"--- Current Alembic Version: {version} ---")
        except Exception:
            print("--- Current Alembic Version: None (or table doesn't exist) ---")

        # Get all tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        print("\n--- Existing Tables in Database ---")
        for table in tables:
            print(f"- {table}")

if __name__ == "__main__":
    check_db()
