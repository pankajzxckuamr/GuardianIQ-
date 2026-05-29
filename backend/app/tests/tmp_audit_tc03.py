import os
import subprocess
import sys

import alembic.command
import psycopg2
from alembic.config import Config

DB_NAME = "guardianiq_audit_tmp"
ADMIN_URL = "postgresql://guardianiq_user:guardianiq123@localhost:5432/postgres"
TEMP_URL = f"postgresql://guardianiq_user:guardianiq123@localhost:5432/{DB_NAME}"

admin = psycopg2.connect(ADMIN_URL)
admin.autocommit = True
cur = admin.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB_NAME,))
if cur.fetchone():
    cur.execute(f"DROP DATABASE {DB_NAME}")
cur.execute(f"CREATE DATABASE {DB_NAME}")
admin.close()

cfg = Config("alembic.ini")
cfg.set_main_option("sqlalchemy.url", TEMP_URL)
alembic.command.upgrade(cfg, "head")

env = os.environ.copy()
env["DATABASE_URL"] = TEMP_URL
seed = subprocess.run([sys.executable, "-m", "app.db.seed"], cwd=".", env=env, capture_output=True, text=True)
print(f"SEED_RETURNCODE={seed.returncode}")
print(seed.stdout)
if seed.stderr:
    print(seed.stderr)

conn = psycopg2.connect(TEMP_URL)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM roles")
print(f"ROLES={cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM permissions")
print(f"PERMISSIONS={cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM departments")
print(f"DEPARTMENTS={cur.fetchone()[0]}")
cur.execute("SELECT role_code FROM roles ORDER BY role_code")
print("ROLE_CODES=" + ",".join(r[0] for r in cur.fetchall()))
cur.execute("SELECT permission_code FROM permissions ORDER BY permission_code")
print("PERMISSION_CODES=" + ",".join(r[0] for r in cur.fetchall()))

cur.execute("INSERT INTO roles (role_code, role_name, description) VALUES ('TEMP_ROLE', 'Temp Role', 'temp') RETURNING id")
role_id = cur.fetchone()[0]
conn.commit()

try:
    cur.execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (999999, role_id))
    conn.commit()
    print("FK_VIOLATION=NOT_RAISED")
except psycopg2.errors.ForeignKeyViolation:
    conn.rollback()
    print("FK_VIOLATION=RAISED")

cur.execute("EXPLAIN ANALYZE SELECT * FROM ai_models WHERE status = 'ACTIVE'")
print("EXPLAIN_AI_MODELS")
for row in cur.fetchall():
    print(row[0])

cur.execute("EXPLAIN ANALYZE SELECT * FROM audit_events WHERE created_at > '2026-01-01'")
print("EXPLAIN_AUDIT_EVENTS")
for row in cur.fetchall():
    print(row[0])

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='policies' AND column_name='reference_id'")
print("POLICY_REFERENCE_ID_EXISTS=" + str(cur.fetchone() is not None))

cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='ai_models'")
print("AI_MODELS_INDEXES=" + ";".join(f"{i[0]}:{i[1]}" for i in cur.fetchall()))

alembic.command.downgrade(cfg, "base")
alembic.command.upgrade(cfg, "head")
print("DOWNGRADE_UPGRADE_OK")

conn.close()

admin = psycopg2.connect(ADMIN_URL)
admin.autocommit = True
cur = admin.cursor()
cur.execute(f"DROP DATABASE {DB_NAME}")
admin.close()
