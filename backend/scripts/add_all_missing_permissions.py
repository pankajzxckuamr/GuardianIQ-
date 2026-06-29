import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.auth.models import Role, Permission

PERMISSIONS_TO_ADD = [
    ('CREATE_WORKFLOW_SCHEDULE', 'workflow_schedules', 'CREATE', 'Allows creating new workflow schedules'),
    ('ACTIVATE_WORKFLOW_SCHEDULE', 'workflow_schedules', 'ACTIVATE', 'Allows approving and rejecting schedules'),
    ('READ_WORKFLOW_SCHEDULE', 'workflow_schedules', 'READ', 'Allows viewing workflow schedules'),
    ('UPDATE_WORKFLOW_SCHEDULE', 'workflow_schedules', 'UPDATE', 'Allows modifying workflow schedules'),
    ('DELETE_WORKFLOW_SCHEDULE', 'workflow_schedules', 'DELETE', 'Allows deleting workflow schedules'),
]

def main():
    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.role_code == 'SUPER_ADMIN').first()
        if not admin_role:
            print("SUPER_ADMIN role not found in legacy table!")
            return

        for perm_code, resource, action, desc in PERMISSIONS_TO_ADD:
            perm = db.query(Permission).filter(Permission.permission_code == perm_code).first()
            if not perm:
                print(f"Creating {perm_code} permission...")
                perm = Permission(
                    permission_code=perm_code,
                    resource=resource,
                    action=action,
                    description=desc
                )
                db.add(perm)
                db.commit()
                db.refresh(perm)
            
            if perm not in admin_role.permissions:
                admin_role.permissions.append(perm)
                db.commit()
                print(f"Added {perm_code} to legacy SUPER_ADMIN role.")
            else:
                print(f"SUPER_ADMIN already has {perm_code}.")

        print("Done adding all workflow schedule permissions!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
