import os
import sys

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.modules.auth.models import User

from app.db.session import SessionLocal

def test_user_roles():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("No users in the database.")
            return

        print(f"User: {user.name} ({user.email})")
        print(f"Roles:")
        for role in user.roles:
            print(f"  - {role.role_code}")
            print(f"    Permissions:")
            for perm in role.permissions:
                print(f"      - {perm.permission_code}")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_user_roles()
