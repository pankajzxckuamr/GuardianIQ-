INITIAL_ROLES = [
    {
        "role_code": "SUPER_ADMIN",
        "role_name": "Super Admin",
        "purpose": "Platform-level administrator",
        "typical_access": "All modules, configuration and seed data",
    },
    {
        "role_code": "GOVERNANCE_ADMIN",
        "role_name": "Governance Admin",
        "purpose": "Owns governance setup and policies",
        "typical_access": "Registry, policies, workflow configuration",
    },
    {
        "role_code": "APPROVER",
        "role_name": "Approver",
        "purpose": "Reviews and approves AI recommendations/actions",
        "typical_access": "Approval queues, recommendation detail, audit trail",
    },
    {
        "role_code": "AUDITOR",
        "role_name": "Auditor",
        "purpose": "Reviews logs, evidence and compliance history",
        "typical_access": "Read-only audit and reports",
    },
    {
        "role_code": "BUSINESS_USER",
        "role_name": "Business User",
        "purpose": "Submits or views recommendations/actions",
        "typical_access": "Limited business views",
    },
    {
        "role_code": "DATA_AI_TEAM",
        "role_name": "Data AI Team",
        "purpose": "Registers models, agents and tools",
        "typical_access": "Model/agent registry and technical metadata",
    },
]


INITIAL_PERMISSIONS = [
    {"permission_code": "registry.read", "description": "View registry records"},
    {"permission_code": "registry.write", "description": "Create or update registry records"},
    {"permission_code": "policy.read", "description": "View policies"},
    {"permission_code": "policy.write", "description": "Create/update policies"},
    {"permission_code": "recommendation.read", "description": "View recommendations"},
    {"permission_code": "approval.review", "description": "Approve/reject/request changes"},
    {"permission_code": "audit.read", "description": "View audit events"},
    {"permission_code": "admin.manage_users", "description": "Manage users and roles"},
]

ROLE_PERMISSION_MATRIX = {
    "SUPER_ADMIN": [
        "registry.read",
        "registry.write",
        "policy.read",
        "policy.write",
        "recommendation.read",
        "approval.review",
        "audit.read",
        "admin.manage_users",
    ],
    "GOVERNANCE_ADMIN": [
        "registry.read",
        "registry.write",
        "policy.read",
        "policy.write",
        "recommendation.read",
        "audit.read",
    ],
    "APPROVER": [
        "registry.read",
        "policy.read",
        "recommendation.read",
        "approval.review",
        "audit.read",
    ],
    "AUDITOR": [
        "registry.read",
        "policy.read",
        "recommendation.read",
        "audit.read",
    ],
    "BUSINESS_USER": [
        "recommendation.read",
    ],
    "DATA_AI_TEAM": [
        "registry.read",
        "registry.write",
    ],
}