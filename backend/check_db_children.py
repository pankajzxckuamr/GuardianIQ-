import os
from sqlalchemy import create_engine, text
from app.core.config import settings

db_url = getattr(settings, 'DATABASE_URL', getattr(settings, 'SQLALCHEMY_DATABASE_URI', getattr(settings, 'DATABASE_URI', None)))

if not db_url:
    import configparser
    config = configparser.ConfigParser()
    config.read("alembic.ini")
    db_url = config.get("alembic", "sqlalchemy.url")

engine = create_engine(str(db_url))

query = """
SELECT
    tc.table_name AS child_table,
    kcu.column_name AS child_column,
    ccu.table_name AS parent_table,
    ccu.column_name AS parent_column
FROM
    information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
AND ccu.table_name = 'orchestration_workflow_executions';
"""

with engine.begin() as conn:
    try:
        result = conn.execute(text(query))
        print("Child tables of orchestration_workflow_executions:")
        for row in result:
            print(row)
    except Exception as e:
        print("Error:")
        print(e)
