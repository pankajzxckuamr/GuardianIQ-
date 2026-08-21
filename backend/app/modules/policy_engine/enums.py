from enum import Enum
from app.modules.registry.constants import DataClassification
from app.shared.enums.sensitivity_level import SensitivityLevel


class PolicyStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"
    RETIRED = "RETIRED"


class VersionStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class BindingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class Decision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    MODIFY = "MODIFY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    ESCALATE = "ESCALATE"
    ALLOW_WITH_OBLIGATIONS = "ALLOW_WITH_OBLIGATIONS"


class TargetType(str, Enum):
    AGENT = "AGENT"
    TOOL = "TOOL"
    DATA_SOURCE = "DATA_SOURCE"
    WORKFLOW = "WORKFLOW"
    MODEL = "MODEL"


class VersionStrategy(str, Enum):
    LATEST = "LATEST"
    PINNED = "PINNED"
    STRICT_LATEST = "STRICT_LATEST"


class AutonomyLevel(str, Enum):
    FULL_AUTONOMY = "FULL_AUTONOMY"
    HUMAN_IN_THE_LOOP = "HUMAN_IN_THE_LOOP"
    HUMAN_SUPERVISED = "HUMAN_SUPERVISED"
    STRICT_OVERSIGHT = "STRICT_OVERSIGHT"


class AccessMode(str, Enum):
    READ_ONLY = "READ_ONLY"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    ADMIN = "ADMIN"
    READ_WRITE = "READ_WRITE"


class DataOperation(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    EXPORT = "EXPORT"
    TRANSFORM = "TRANSFORM"
    DELETE = "DELETE"
    AGGREGATE = "AGGREGATE"


class EnforcementMode(str, Enum):
    BLOCKING = "BLOCKING"
    MONITORING = "MONITORING"
    WARN = "WARN"
    DRY_RUN = "DRY_RUN"


__all__ = [
    "PolicyStatus",
    "VersionStatus",
    "BindingStatus",
    "Decision",
    "TargetType",
    "VersionStrategy",
    "AutonomyLevel",
    "AccessMode",
    "DataOperation",
    "EnforcementMode",
    "DataClassification",
    "SensitivityLevel",
]
