import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.auth.models import Role, Permission

def main():
    db = SessionLocal()
    try:
        # Check if permission exists
        perm = db.query(Permission).filter(Permission.permission_code == 'CREATE_WORKFLOW_SCHEDULE').first()
        if not perm:
            print("Creating CREATE_WORKFLOW_SCHEDULE permission...")
            perm = Permission(
                permission_code='CREATE_WORKFLOW_SCHEDULE',
                resource='workflow_schedules',
                action='CREATE',
                description='Allows creating new workflow schedules'
            )
            db.add(perm)
            db.commit()
            db.refresh(perm)
        else:
            print("Permission already exists in database.")

        admin_role = db.query(Role).filter(Role.role_code == 'SUPER_ADMIN').first()
        if admin_role:
            if perm not in admin_role.permissions:
                admin_role.permissions.append(perm)
                db.commit()
                print("Added CREATE_WORKFLOW_SCHEDULE to SUPER_ADMIN role.")
            else:
                print("SUPER_ADMIN already has this permission.")
        else:
            print("Admin role not found!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
