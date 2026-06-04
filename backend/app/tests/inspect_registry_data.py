import psycopg2

URL = "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq"
conn = psycopg2.connect(URL)
cur = conn.cursor()

tables = [
    "registry_departments",
    "registry_roles",
    "guardian_users",
    "registry_ai_model_providers",
    "registry_ai_models",
    "registry_ai_agents",
    "registry_tools",
    "registry_workflows",
    "registry_data_sources",
    "registry_relationships"
]

for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    count = cur.fetchone()[0]
    print(f"Table {t}: {count} records")
    if count > 0:
        cur.execute(f"SELECT * FROM {t} LIMIT 2")
        cols = [desc[0] for desc in cur.description]
        print(f"Columns: {cols}")
        for r in cur.fetchall():
            print(r)
    print("-" * 50)

conn.close()
