import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.db.session import engine
from sqlalchemy import text

def test_db():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'id'")).fetchone()
        print("Users ID column type:", result)

if __name__ == "__main__":
    test_db()
