import sys
import os

# Add backend directory to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.auth.models import Role, Permission

def main():
    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.role_code == 'SUPER_ADMIN').first()
        if not admin_role:
            print("Admin role not found!")
            return

        all_permissions = db.query(Permission).all()
        
        added = 0
        for p in all_permissions:
            if p not in admin_role.permissions:
                admin_role.permissions.append(p)
                added += 1
                
        db.commit()
        print(f"Successfully added {added} new permissions to the Admin role.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
