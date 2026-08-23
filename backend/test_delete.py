import os
from sqlalchemy import create_engine, text
from app.core.config import settings

# Attempt multiple possible config names
db_url = getattr(settings, 'DATABASE_URL', getattr(settings, 'SQLALCHEMY_DATABASE_URI', getattr(settings, 'DATABASE_URI', None)))

if not db_url:
    # fallback to manual parsing of alembic.ini
    import configparser
    config = configparser.ConfigParser()
    config.read("alembic.ini")
    db_url = config.get("alembic", "sqlalchemy.url")

engine = create_engine(str(db_url))

query = "DELETE FROM orchestration_workflow_executions WHERE workflow_id NOT IN (SELECT id FROM workflows) AND workflow_id IS NOT NULL"

with engine.begin() as conn:
    try:
        conn.execute(text(query))
        print("Success!")
    except Exception as e:
        print("Error:")
        print(e)
