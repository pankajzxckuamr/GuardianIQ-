"""
RBAC Seed Script
================
Seeds the database with initial roles, permissions, and their mappings.

Usage:
    cd backend
    python -m app.db.seed
"""

from app.db.session import SessionLocal
from app.modules.auth.models import Role, Permission, User, user_roles, role_permissions
from app.core.security import hash_password


# ──────────────────────────────────────────────
# 1. Define Permissions (from spec section 7.2)
# ──────────────────────────────────────────────
PERMISSIONS = [
    {"permission_code": "registry.read",        "description": "View registry records"},
    {"permission_code": "registry.write",       "description": "Create or update registry records"},
    {"permission_code": "policy.read",          "description": "View policies"},
    {"permission_code": "policy.write",         "description": "Create/update policies"},
    {"permission_code": "recommendation.read",  "description": "View recommendations"},
    {"permission_code": "approval.review",      "description": "Approve/reject/request changes"},
    {"permission_code": "audit.read",           "description": "View audit events"},
    {"permission_code": "admin.manage_users",   "description": "Manage users and roles"},
]


# ──────────────────────────────────────────────
# 2. Define Roles (from spec section 7.1)
# ──────────────────────────────────────────────
ROLES = [
    {
        "role_code": "SUPER_ADMIN",
        "role_name": "Super Admin",
        "description": "Platform-level administrator",
    },
    {
        "role_code": "GOVERNANCE_ADMIN",
        "role_name": "Governance Admin",
        "description": "Owns governance setup and policies",
    },
    {
        "role_code": "APPROVER",
        "role_name": "Approver",
        "description": "Reviews and approves AI recommendations/actions",
    },
    {
        "role_code": "AUDITOR",
        "role_name": "Auditor",
        "description": "Reviews logs, evidence and compliance history",
    },
    {
        "role_code": "BUSINESS_USER",
        "role_name": "Business User",
        "description": "Submits or views recommendations/actions",
    },
    {
        "role_code": "DATA_AI_TEAM",
        "role_name": "Data / AI Team",
        "description": "Registers models, agents and tools",
    },
]


# ──────────────────────────────────────────────
# 3. Role -> Permission Mapping
# ──────────────────────────────────────────────
ROLE_PERMISSION_MAP = {
    "SUPER_ADMIN": [
        "registry.read", "registry.write",
        "policy.read", "policy.write",
        "recommendation.read", "approval.review",
        "audit.read", "admin.manage_users",
    ],
    "GOVERNANCE_ADMIN": [
        "registry.read", "registry.write",
        "policy.read", "policy.write",
    ],
    "APPROVER": [
        "recommendation.read", "approval.review", "audit.read",
    ],
    "AUDITOR": [
        "registry.read", "policy.read",
        "recommendation.read", "audit.read",
    ],
    "BUSINESS_USER": [
        "recommendation.read",
    ],
    "DATA_AI_TEAM": [
        "registry.read", "registry.write",
    ],
}


# ──────────────────────────────────────────────
# 4. Seed Logic
# ──────────────────────────────────────────────
def seed():
    db = SessionLocal()
    try:
        # --- Seed Permissions ---
        print("\n🔐 Seeding Permissions...")
        for perm_data in PERMISSIONS:
            existing = db.query(Permission).filter(
                Permission.permission_code == perm_data["permission_code"]
            ).first()
            if not existing:
                db.add(Permission(**perm_data))
                print(f"   ✅ Created permission: {perm_data['permission_code']}")
            else:
                print(f"   ⏭️  Already exists: {perm_data['permission_code']}")

        db.commit()

        # --- Seed Roles ---
        print("\n👥 Seeding Roles...")
        for role_data in ROLES:
            existing = db.query(Role).filter(
                Role.role_code == role_data["role_code"]
            ).first()
            if not existing:
                db.add(Role(**role_data))
                print(f"   ✅ Created role: {role_data['role_code']}")
            else:
                print(f"   ⏭️  Already exists: {role_data['role_code']}")

        db.commit()

        # --- Seed Role-Permission Mappings ---
        print("\n🔗 Seeding Role-Permission Mappings...")
        for role_code, perm_codes in ROLE_PERMISSION_MAP.items():
            role = db.query(Role).filter(Role.role_code == role_code).first()
            if not role:
                print(f"   ❌ Role not found: {role_code}")
                continue

            existing_perm_codes = {p.permission_code for p in role.permissions}

            for perm_code in perm_codes:
                if perm_code in existing_perm_codes:
                    print(f"   ⏭️  {role_code} already has {perm_code}")
                    continue

                perm = db.query(Permission).filter(
                    Permission.permission_code == perm_code
                ).first()

                if perm:
                    role.permissions.append(perm)
                    print(f"   ✅ Mapped {role_code} → {perm_code}")
                else:
                    print(f"   ❌ Permission not found: {perm_code}")

        db.commit()

        # --- Seed Default Admin User ---
        print("\n👤 Seeding Default Admin User...")
        admin_email = "admin@guardianiq.com"
        existing_admin = db.query(User).filter(User.email == admin_email).first()

        if not existing_admin:
            admin_user = User(
                name="Super Admin",
                email=admin_email,
                hashed_password=hash_password("Admin@1234!")
            )
            db.add(admin_user)
            db.flush()  # Get admin_user.id before assigning roles

            super_admin_role = db.query(Role).filter(
                Role.role_code == "SUPER_ADMIN"
            ).first()

            if super_admin_role:
                admin_user.roles.append(super_admin_role)
                print(f"   ✅ Created admin user: {admin_email}")
                print(f"   ✅ Assigned role: SUPER_ADMIN")
                print(f"   ⚠️  Default password is 'Admin@1234!' — change after first login!")
            else:
                print("   ❌ SUPER_ADMIN role not found — skipping role assignment")
        else:
            print(f"   ⏭️  Already exists: {admin_email}")

        db.commit()
        print("\n🎉 Seeding complete!\n")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
