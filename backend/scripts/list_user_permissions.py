import sys
import os
from collections import defaultdict

# Add backend directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.auth.models import User

def main():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print("\n=== USER PERMISSIONS REPORT ===\n")
        
        for user in users:
            print(f"User: {user.full_name or user.name} ({user.email})")
            
            roles = [role.role_name for role in user.roles]
            print(f"Roles: {', '.join(roles) if roles else 'None'}")
            
            permissions = set()
            for role in user.roles:
                for perm in role.permissions:
                    permissions.add(perm.permission_code)
                    
            if permissions:
                print("Permissions:")
                for perm in sorted(permissions):
                    print(f"  - {perm}")
            else:
                print("Permissions: None")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
