import psycopg2

URL = "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq"
conn = psycopg2.connect(URL)
cur = conn.cursor()
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
cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='audit_events'")
print("AUDIT_EVENTS_INDEXES=" + ";".join(f"{i[0]}:{i[1]}" for i in cur.fetchall()))
conn.close()
