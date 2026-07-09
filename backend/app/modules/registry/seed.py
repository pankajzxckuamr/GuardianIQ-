from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.modules.auth.models import Role, User
from app.modules.department.models import Department
from app.core.security import hash_password

def seed_registry_data(db: Session):
    # Seed default tenant admin user first (so departments can reference it for tenant_id)
    admin_user = db.execute(select(User).filter_by(email="admin@guardianiq.com")).scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            id=uuid4(),
            email="admin@guardianiq.com",
            name="Super Admin",
            full_name="Admin User",
            hashed_password=hash_password("Admin@1234!"),
            status="ACTIVE"
        )
        db.add(admin_user)
        db.flush()

    # Seed departments
    depts_data = [
        {"department_code": "SALES", "department_name": "Sales"},
        {"department_code": "RISK", "department_name": "Risk"},
        {"department_code": "COMPLIANCE", "department_name": "Compliance"},
        {"department_code": "FINANCE", "department_name": "Finance"},
        {"department_code": "DATA_AI", "department_name": "Data & AI"},
        {"department_code": "OPERATIONS", "department_name": "Operations"}
    ]
    for dept in depts_data:
        existing = db.execute(select(Department).filter_by(department_code=dept["department_code"])).scalar_one_or_none()
        if not existing:
            new_dept = Department(
                id=uuid4(),
                tenant_id=admin_user.id,
                department_code=dept["department_code"],
                department_name=dept["department_name"],
                status="ACTIVE"
            )
            db.add(new_dept)
    db.commit()

    # Seed roles
    roles_data = [
        {"role_code": "SYSTEM_ADMIN", "role_name": "System Admin"},
        {"role_code": "GOVERNANCE_ADMIN", "role_name": "Governance Admin"},
        {"role_code": "AI_ASSET_OWNER", "role_name": "AI Asset Owner"},
        {"role_code": "AI_REVIEWER", "role_name": "AI Reviewer"},
        {"role_code": "BUSINESS_APPROVER", "role_name": "Business Approver"},
        {"role_code": "RISK_MANAGER", "role_name": "Risk Manager"},
        {"role_code": "COMPLIANCE_OFFICER", "role_name": "Compliance Officer"},
        {"role_code": "AUDITOR", "role_name": "Auditor"}
    ]
    for r in roles_data:
        existing = db.execute(select(Role).filter_by(role_code=r["role_code"])).scalar_one_or_none()
        if not existing:
            new_role = Role(
                id=uuid4(),
                role_code=r["role_code"],
                role_name=r["role_name"]
            )
            db.add(new_role)
    db.commit()

    # Seed users
    users_data = [
        {"email": "admin@guardianiq.com", "full_name": "Admin User", "name": "Super Admin", "role_code": "SYSTEM_ADMIN"},
        {"email": "reviewer@guardianiq.com", "full_name": "Reviewer User", "name": "Reviewer User", "role_code": "AI_REVIEWER"},
        {"email": "auditor@guardianiq.com", "full_name": "Auditor User", "name": "Auditor User", "role_code": "AUDITOR"}
    ]
    for user_info in users_data:
        existing = db.execute(select(User).filter_by(email=user_info["email"])).scalar_one_or_none()
        role = db.execute(select(Role).filter_by(role_code=user_info["role_code"])).scalar_one_or_none()
        dept = db.execute(select(Department).filter_by(department_code="COMPLIANCE")).scalar_one_or_none()
        if not dept:
            dept = db.execute(select(Department)).scalars().first()
        
        if existing:
            if dept:
                existing.department_id = dept.id
            if role and role not in existing.roles:
                existing.roles.append(role)
        else:
            new_user = User(
                id=uuid4(),
                email=user_info["email"],
                name=user_info["name"],
                full_name=user_info["full_name"],
                hashed_password=hash_password("Admin@1234!"),
                department_id=dept.id if dept else None,
                status="ACTIVE"
            )
            if role:
                new_user.roles.append(role)
            db.add(new_user)
    db.commit()
