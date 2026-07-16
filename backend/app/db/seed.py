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
    
    # Phase 2 Actions
    {"permission_code": "CREATE_WORKFLOW_SCHEDULE", "description": "Create workflow schedules"},
    {"permission_code": "UPDATE_WORKFLOW_SCHEDULE", "description": "Update workflow schedules"},
    {"permission_code": "SUBMIT_WORKFLOW_SCHEDULE", "description": "Submit workflow schedules"},
    {"permission_code": "ACTIVATE_WORKFLOW_SCHEDULE", "description": "Activate workflow schedules"},
    {"permission_code": "PAUSE_WORKFLOW_SCHEDULE", "description": "Pause workflow schedules"},
    {"permission_code": "RESUME_WORKFLOW_SCHEDULE", "description": "Resume workflow schedules"},
    {"permission_code": "RETIRE_WORKFLOW_SCHEDULE", "description": "Retire workflow schedules"},
    {"permission_code": "RUN_WORKFLOW_SCHEDULE", "description": "Run workflow schedules now"},
    {"permission_code": "VIEW_WORKFLOW_SCHEDULE", "description": "View workflow schedules"},
    {"permission_code": "VIEW_WORKFLOW_RUN", "description": "View workflow runs"},
    {"permission_code": "ASSIGN_AI_AGENT_TO_WORKFLOW", "description": "Assign AI agent to workflow schedule"},
    {"permission_code": "VIEW_WORKFLOW_RUN_OUTPUT", "description": "View workflow run outputs"},
    {"permission_code": "CANCEL_WORKFLOW_RUN", "description": "Cancel running workflow runs"},
    {"permission_code": "EVALUATE_AUTHORIZATION", "description": "Evaluate authorization decisions"},
    {"permission_code": "OVERRIDE_WORKFLOW_FAILURE", "description": "Override failed workflow runs"},
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
    {
        "role_code": "SYSTEM_ADMIN",
        "role_name": "System Admin",
        "description": "Configure platform scheduler settings, view all runs, manage global seed data",
    },
    {
        "role_code": "AI_ASSET_OWNER",
        "role_name": "AI Asset Owner",
        "description": "Review schedules using model/agent, update boundaries, view related runs",
    },
    {
        "role_code": "AI_REVIEWER",
        "role_name": "AI Reviewer",
        "description": "Review outputs, findings, generated recommendations and run evidence",
    },
    {
        "role_code": "BUSINESS_APPROVER",
        "role_name": "Business Approver",
        "description": "Approve business workflow schedule activation within allowed department/risk scope",
    },
    {
        "role_code": "RISK_MANAGER",
        "role_name": "Risk Manager",
        "description": "Approve or escalate high-risk schedules and high-risk run findings",
    },
    {
        "role_code": "COMPLIANCE_OFFICER",
        "role_name": "Compliance Officer",
        "description": "Review compliance-sensitive schedules and run evidence",
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
        "CREATE_WORKFLOW_SCHEDULE", "UPDATE_WORKFLOW_SCHEDULE", "SUBMIT_WORKFLOW_SCHEDULE",
        "ACTIVATE_WORKFLOW_SCHEDULE", "PAUSE_WORKFLOW_SCHEDULE", "RESUME_WORKFLOW_SCHEDULE",
        "RETIRE_WORKFLOW_SCHEDULE", "RUN_WORKFLOW_SCHEDULE", "VIEW_WORKFLOW_SCHEDULE",
        "VIEW_WORKFLOW_RUN", "ASSIGN_AI_AGENT_TO_WORKFLOW", "VIEW_WORKFLOW_RUN_OUTPUT",
        "CANCEL_WORKFLOW_RUN", "EVALUATE_AUTHORIZATION", "OVERRIDE_WORKFLOW_FAILURE",
    ],
    "GOVERNANCE_ADMIN": [
        "registry.read", "registry.write",
        "policy.read", "policy.write",
        "CREATE_WORKFLOW_SCHEDULE", "UPDATE_WORKFLOW_SCHEDULE", "SUBMIT_WORKFLOW_SCHEDULE",
        "ACTIVATE_WORKFLOW_SCHEDULE", "PAUSE_WORKFLOW_SCHEDULE", "RESUME_WORKFLOW_SCHEDULE",
        "RETIRE_WORKFLOW_SCHEDULE", "RUN_WORKFLOW_SCHEDULE", "VIEW_WORKFLOW_SCHEDULE",
        "VIEW_WORKFLOW_RUN", "ASSIGN_AI_AGENT_TO_WORKFLOW", "VIEW_WORKFLOW_RUN_OUTPUT",
        "CANCEL_WORKFLOW_RUN", "EVALUATE_AUTHORIZATION",
    ],
    "APPROVER": [
        "recommendation.read", "approval.review", "audit.read",
    ],
    "AUDITOR": [
        "registry.read", "policy.read",
        "recommendation.read", "audit.read",
        "VIEW_WORKFLOW_SCHEDULE", "VIEW_WORKFLOW_RUN", "VIEW_WORKFLOW_RUN_OUTPUT",
    ],
    "BUSINESS_USER": [
        "recommendation.read",
    ],
    "DATA_AI_TEAM": [
        "registry.read", "registry.write",
    ],
    "SYSTEM_ADMIN": [
        "registry.read", "registry.write",
        "policy.read", "policy.write",
        "recommendation.read", "approval.review",
        "audit.read", "admin.manage_users",
        "EVALUATE_AUTHORIZATION", "OVERRIDE_WORKFLOW_FAILURE",
    ],
    "AI_ASSET_OWNER": [
        "registry.read", "registry.write",
        "policy.read", "recommendation.read",
        "VIEW_WORKFLOW_SCHEDULE", "VIEW_WORKFLOW_RUN", "ASSIGN_AI_AGENT_TO_WORKFLOW",
    ],
    "AI_REVIEWER": [
        "registry.read", "policy.read", "recommendation.read",
        "VIEW_WORKFLOW_RUN_OUTPUT", "CANCEL_WORKFLOW_RUN",
    ],
    "BUSINESS_APPROVER": [
        "registry.read", "policy.read", "recommendation.read", "approval.review", "audit.read",
        "VIEW_WORKFLOW_SCHEDULE", "VIEW_WORKFLOW_RUN", "ACTIVATE_WORKFLOW_SCHEDULE",
    ],
    "RISK_MANAGER": [
        "registry.read", "policy.read", "recommendation.read", "approval.review", "audit.read",
        "VIEW_WORKFLOW_RUN_OUTPUT", "CANCEL_WORKFLOW_RUN", "OVERRIDE_WORKFLOW_FAILURE",
    ],
    "COMPLIANCE_OFFICER": [
        "registry.read", "policy.read", "recommendation.read", "approval.review", "audit.read",
        "VIEW_WORKFLOW_SCHEDULE", "VIEW_WORKFLOW_RUN", "VIEW_WORKFLOW_RUN_OUTPUT",
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

        # --- Seed Demo Users ---
        print("\n👤 Seeding Demo Users...")
        demo_users = [
            {"email": "admin@guardianiq.com", "name": "Super Admin", "role_code": "SUPER_ADMIN"},
            {"email": "reviewer@guardianiq.com", "name": "Reviewer User", "role_code": "AI_REVIEWER"},
            {"email": "auditor@guardianiq.com", "name": "Auditor User", "role_code": "AUDITOR"},
            
            # Phase 2 Demo users
            {"email": "governance@guardianiq.demo", "name": "Governance Admin", "role_code": "GOVERNANCE_ADMIN"},
            {"email": "risk@guardianiq.demo", "name": "Risk Manager", "role_code": "RISK_MANAGER"},
            {"email": "compliance@guardianiq.demo", "name": "Compliance Officer", "role_code": "COMPLIANCE_OFFICER"},
            {"email": "auditor@guardianiq.demo", "name": "Auditor User", "role_code": "AUDITOR"},
            {"email": "approver@guardianiq.demo", "name": "Business Approver", "role_code": "BUSINESS_APPROVER"},
        ]

        for u in demo_users:
            existing_user = db.query(User).filter(User.email == u["email"]).first()

            if not existing_user:
                existing_user = User(
                    name=u["name"],
                    email=u["email"],
                    hashed_password=hash_password("Admin@1234!")
                )
                db.add(existing_user)
                db.flush()
                print(f"   ✅ Created user: {u['email']}")

            user_role = db.query(Role).filter(Role.role_code == u["role_code"]).first()

            if user_role:
                if user_role not in existing_user.roles:
                    existing_user.roles.append(user_role)
                    print(f"   ✅ Assigned role: {u['role_code']} to {u['email']}")
            else:
                print(f"   ❌ Role {u['role_code']} not found — skipping role assignment for {u['email']}")

        print(f"   ⚠️  Default password for all demo users is 'Admin@1234!'")

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
