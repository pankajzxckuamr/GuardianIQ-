import sys
import os
from sqlalchemy import create_engine, text

DB_URL = "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq"

try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("=== ALL WORKFLOW SCHEDULES ===")
        res = conn.execute(text("SELECT id, schedule_code, schedule_name FROM workflow_schedules"))
        for row in res:
            print(f"ID: {row[0]} | Code: {row[1]} | Name: {row[2]}")
except Exception as e:
    print(f"Error querying database: {e}")
