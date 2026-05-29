import psycopg2

URL = "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq"
conn = psycopg2.connect(URL)
cur = conn.cursor()
cur.execute("SELECT id FROM roles WHERE role_code = 'SUPER_ADMIN'")
role_id = cur.fetchone()[0]
try:
    cur.execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (999999, role_id))
    conn.commit()
    print("FK_VIOLATION=NOT_RAISED")
except psycopg2.errors.ForeignKeyViolation:
    conn.rollback()
    print("FK_VIOLATION=RAISED")
conn.close()
