import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('No DATABASE_URL found in .env')
    exit(1)

# Ensure we use sync driver
db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

print(f"Connecting to database to reset schema...")
try:
    engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text('DROP SCHEMA public CASCADE;'))
        conn.execute(text('CREATE SCHEMA public;'))
        conn.execute(text('GRANT ALL ON SCHEMA public TO public;'))
    print("✅ Schema 'public' dropped and recreated successfully.")
except Exception as e:
    print(f"❌ Error resetting database: {e}")
