import psycopg2

URL = "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq"
conn = psycopg2.connect(URL)
cur = conn.cursor()

# EXPLAIN ANALYZE for ai_models status filter
cur.execute("EXPLAIN ANALYZE SELECT * FROM ai_models WHERE status = 'ACTIVE'")
print('EXPLAIN_AI_MODELS:')
for r in cur.fetchall():
    print(r[0])

# EXPLAIN ANALYZE for audit_events created_at filter
cur.execute("EXPLAIN ANALYZE SELECT * FROM audit_events WHERE created_at > '2026-01-01'")
print('\nEXPLAIN_AUDIT_EVENTS:')
for r in cur.fetchall():
    print(r[0])

# Check indexes for ai_models and audit_events
cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='ai_models'")
print('\nAI_MODELS_INDEXES:')
for i in cur.fetchall():
    print(i[0], i[1])

cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='audit_events'")
print('\nAUDIT_EVENTS_INDEXES:')
for i in cur.fetchall():
    print(i[0], i[1])

# Check presence of index on policies.reference_id if present
cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='policies'")
print('\nPOLICIES_INDEXES:')
for i in cur.fetchall():
    print(i[0], i[1])

conn.close()
