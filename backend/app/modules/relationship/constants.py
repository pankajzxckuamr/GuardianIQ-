from enum import Enum

class RelationshipType(str, Enum):
    OWNED_BY = "OWNED_BY"
    REVIEWED_BY = "REVIEWED_BY"
    APPROVED_BY = "APPROVED_BY"
    EXECUTED_BY = "EXECUTED_BY"
    USES_MODEL = "USES_MODEL"
    USES_TOOL = "USES_TOOL"
    USES_DATA_SOURCE = "USES_DATA_SOURCE"
    PARTICIPATES_IN_WORKFLOW = "PARTICIPATES_IN_WORKFLOW"
    GOVERNED_BY = "GOVERNED_BY"
    EVALUATED_BY = "EVALUATED_BY"
    SUPPORTED_BY = "SUPPORTED_BY"
    RESULTS_IN = "RESULTS_IN"
    TRIGGERS = "TRIGGERS"
    ESCALATED_TO = "ESCALATED_TO"
    DELEGATED_TO = "DELEGATED_TO"
    BELONGS_TO = "BELONGS_TO"
    MEMBER_OF = "MEMBER_OF"
    HAS_PERMISSION = "HAS_PERMISSION"
    VIOLATES = "VIOLATES"
    REMEDIATED_BY = "REMEDIATED_BY"


class LifecycleState(str, Enum):
    PROPOSED = "PROPOSED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"
    REJECTED = "REJECTED"


class ResponsibilityType(str, Enum):
    OWNER = "OWNER"
    REVIEWER = "REVIEWER"
    APPROVER = "APPROVER"
    EXECUTOR = "EXECUTOR"
    AUDITOR = "AUDITOR"
    ESCALATION_OWNER = "ESCALATION_OWNER"


class ValidationRuleCategory(str, Enum):
    OWNERSHIP = "OWNERSHIP"
    DUPLICATE = "DUPLICATE"
    TEMPORAL = "TEMPORAL"
    LIFECYCLE = "LIFECYCLE"
    CROSS_TENANT = "CROSS_TENANT"
    GRAPH_INTEGRITY = "GRAPH_INTEGRITY"


class EntityType(str, Enum):
    AGENT = "AGENT"
    MODEL = "MODEL"
    TOOL = "TOOL"
    DATA_SOURCE = "DATA_SOURCE"
    WORKFLOW = "WORKFLOW"
    DEPARTMENT = "DEPARTMENT"
    USER = "USER"
    ROLE = "ROLE"


def canonicalize_entity_type(raw_type: str) -> str:
    """Normalizes any entity type string to canonical uppercase singular."""
    if not raw_type:
        return "UNKNOWN"
    norm = str(raw_type).strip().lower()
    if norm in {"agent", "agents", "ai_agent", "ai_agents"}:
        return "AGENT"
    if norm in {"model", "models", "ai_model", "ai_models"}:
        return "MODEL"
    if norm in {"tool", "tools"}:
        return "TOOL"
    if norm in {"workflow", "workflows"}:
        return "WORKFLOW"
    if norm in {"data_source", "data_sources", "datasource", "datasources"}:
        return "DATA_SOURCE"
    if norm in {"department", "departments"}:
        return "DEPARTMENT"
    if norm in {"user", "users"}:
        return "USER"
    if norm in {"role", "roles"}:
        return "ROLE"
    return norm.upper()


def table_for_entity_type(raw_type: str) -> str:
    """Maps canonical entity type to database table name."""
    c_type = canonicalize_entity_type(raw_type)
    mapping = {
        "AGENT": "agents",
        "MODEL": "ai_models",
        "TOOL": "tools",
        "WORKFLOW": "workflows",
        "DATA_SOURCE": "data_sources",
        "DEPARTMENT": "departments",
        "USER": "users",
        "ROLE": "roles"
    }
    return mapping.get(c_type, c_type.lower())


def canonicalize_rel_type(raw_rel: str) -> str:
    """Normalizes relationship type string to uppercase standard."""
    if not raw_rel:
        return "USES"
    norm = str(raw_rel).strip().upper()
    if norm == "USES":
        return "USES"
    return norm

