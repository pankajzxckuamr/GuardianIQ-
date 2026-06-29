import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.modules.auth.models import Role, User
from app.modules.registry.models import GuardianUser

def main():
    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.role_code == 'SUPER_ADMIN').first()
        if not admin_role:
            print("SUPER_ADMIN role not found in legacy table!")
            return

        guardian_users = db.query(GuardianUser).all()
        for gu in guardian_users:
            print(f"Processing GuardianUser: {gu.email}")
            legacy_user = db.query(User).filter(User.email == gu.email).first()
            if not legacy_user:
                print(f"  Creating legacy User for {gu.email}")
                legacy_user = User(
                    email=gu.email,
                    hashed_password="dummy_password",
                    name=gu.full_name or gu.email,
                    full_name=gu.full_name
                )
                db.add(legacy_user)
                db.commit()
                db.refresh(legacy_user)
            
            if admin_role not in legacy_user.roles:
                legacy_user.roles.append(admin_role)
                db.commit()
                print(f"  Added {gu.email} to legacy SUPER_ADMIN role.")
            else:
                print(f"  {gu.email} is already a legacy SUPER_ADMIN.")

        print("Done fixing user permissions!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
