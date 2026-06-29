import sys
import os
from uuid import uuid4

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.registry.models import GuardianUser, RegistryDepartment, RegistryRole

def main():
    db = SessionLocal()
    try:
        # Get all legacy users
        legacy_users = db.query(User).all()
        
        # We need a fallback department and role for Phase 2 GuardianUser requirements
        default_dept = db.query(RegistryDepartment).first()
        default_role = db.query(RegistryRole).first()
        
        if not default_dept or not default_role:
            print("Error: Could not find any RegistryDepartment or RegistryRole to assign as fallback. Have you run populate_5.py?")
            return
            
        print(f"Using default department: {default_dept.department_name} (ID: {default_dept.id})")
        print(f"Using default role: {default_role.role_name} (ID: {default_role.id})")
        
        added_count = 0
        
        for l_user in legacy_users:
            # Check if user already exists in Phase 2
            existing = db.query(GuardianUser).filter(GuardianUser.email == l_user.email).first()
            if not existing:
                print(f"Syncing legacy user: {l_user.email}...")
                new_g_user = GuardianUser(
                    id=uuid4(),
                    email=l_user.email,
                    full_name=l_user.full_name or l_user.name or l_user.email.split('@')[0],
                    department_id=default_dept.id,
                    role_id=default_role.id,
                    status=l_user.status or 'ACTIVE'
                )
                db.add(new_g_user)
                added_count += 1
            else:
                print(f"Skipping {l_user.email} (already exists in guardian_users)")
                
        db.commit()
        print(f"\nSuccess! Synced {added_count} new legacy users into the Phase 2 GuardianUser table.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
