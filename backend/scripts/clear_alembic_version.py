import os
from sqlalchemy import create_engine, text

# Use DATABASE_URL from .env (already set in env)
from dotenv import load_dotenv
load_dotenv()

# FALLBACK if env var not present
url = os.getenv('DATABASE_URL')
if not url:
    raise RuntimeError('DATABASE_URL not set')

engine = create_engine(url)
with engine.begin() as conn:
    # Remove all rows so Alembic thinks it's uninitialized
    conn.execute(text('DELETE FROM alembic_version'))
    # Insert the latest revision manually (optional)
    conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('2ffed4997630')"))

print('Alembic version table cleared and set to latest.')
