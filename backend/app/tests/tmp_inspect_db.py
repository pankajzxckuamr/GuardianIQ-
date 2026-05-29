import os
import sys

import psycopg2

URL = "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq"
conn = psycopg2.connect(URL)
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
print("TABLES=" + ",".join(r[0] for r in cur.fetchall()))
for table in ["roles", "permissions", "departments", "users", "user_roles", "role_permissions", "policies", "audit_events", "ai_models", "agents", "recommendations", "approvals", "application_settings", "token_blocklist"]:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"{table}={cur.fetchone()[0]}")
    except Exception as exc:
        print(f"{table}=ERROR:{exc}")
conn.close()
