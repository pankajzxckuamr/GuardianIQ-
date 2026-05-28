from sqlalchemy.orm import Session
from sqlalchemy import select
from app.modules.registry.models import RegistryRole, RegistryDepartment, GuardianUser

def seed_registry_data(db: Session):
    # Idempotent seed: registry_roles
    roles_data = [
        {"role_code": "ADMIN", "role_name": "Admin", "role_type": "SYSTEM"},
        {"role_code": "GOVERNANCE_MANAGER", "role_name": "Governance Manager", "role_type": "BUSINESS"},
        {"role_code": "REVIEWER", "role_name": "Reviewer", "role_type": "BUSINESS"},
        {"role_code": "APPROVER", "role_name": "Approver", "role_type": "BUSINESS"},
        {"role_code": "AUDITOR", "role_name": "Auditor", "role_type": "SYSTEM"},
        {"role_code": "BUSINESS_OWNER", "role_name": "Business Owner", "role_type": "BUSINESS"}
    ]
    for role in roles_data:
        existing = db.execute(select(RegistryRole).filter_by(role_code=role["role_code"])).scalar_one_or_none()
        if not existing:
            new_role = RegistryRole(**role)
            db.add(new_role)
    db.commit()

    # Idempotent seed: registry_departments
    depts_data = [
        {"department_code": "SALES", "department_name": "Sales"},
        {"department_code": "RISK", "department_name": "Risk"},
        {"department_code": "COMPLIANCE", "department_name": "Compliance"},
        {"department_code": "FINANCE", "department_name": "Finance"},
        {"department_code": "DATA_AI", "department_name": "Data & AI"},
        {"department_code": "OPERATIONS", "department_name": "Operations"}
    ]
    for dept in depts_data:
        existing = db.execute(select(RegistryDepartment).filter_by(department_code=dept["department_code"])).scalar_one_or_none()
        if not existing:
            new_dept = RegistryDepartment(**dept)
            db.add(new_dept)
    db.commit()

    # Idempotent seed: guardian_users
    users_data = [
        {"email": "admin@guardianiq.com", "full_name": "Admin User", "role_code": "ADMIN"},
        {"email": "reviewer@guardianiq.com", "full_name": "Reviewer User", "role_code": "REVIEWER"},
        {"email": "auditor@guardianiq.com", "full_name": "Auditor User", "role_code": "AUDITOR"}
    ]
    for user_info in users_data:
        existing = db.execute(select(GuardianUser).filter_by(email=user_info["email"])).scalar_one_or_none()
        if not existing:
            role = db.execute(select(RegistryRole).filter_by(role_code=user_info["role_code"])).scalar_one_or_none()
            if role:
                new_user = GuardianUser(
                    email=user_info["email"],
                    full_name=user_info["full_name"],
                    role_id=role.id
                )
                db.add(new_user)
    db.commit()
