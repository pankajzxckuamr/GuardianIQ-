from enum import Enum
from app.shared.enums.entity_status import EntityStatus
from app.shared.enums.sensitivity_level import SensitivityLevel

class ModelType(str, Enum):
    LLM = "LLM"
    ML = "ML"
    CLASSIFIER = "CLASSIFIER"
    EMBEDDING = "EMBEDDING"
    RULE_BASED = "RULE_BASED"
    FORECASTING = "FORECASTING"
    OPTIMIZATION = "OPTIMIZATION"

class AgentType(str, Enum):
    RECOMMENDATION = "RECOMMENDATION"
    TRIAGE = "TRIAGE"
    EXTRACTION = "EXTRACTION"
    EXECUTION = "EXECUTION"
    MONITORING = "MONITORING"

class AgentExecutionMode(str, Enum):
    READ_ONLY = "READ_ONLY"
    RECOMMEND_ONLY = "RECOMMEND_ONLY"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    LIMITED_EXECUTION = "LIMITED_EXECUTION"
    BLOCKED = "BLOCKED"

class ToolCategory(str, Enum):
    ERP = "ERP"
    CRM = "CRM"
    EMAIL = "EMAIL"
    TICKETING = "TICKETING"
    DATABASE = "DATABASE"
    LLM = "LLM"
    FILE = "FILE"
    WEBHOOK = "WEBHOOK"

class AccessMode(str, Enum):
    READ_ONLY = "READ_ONLY"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    ADMIN = "ADMIN"

class WorkflowType(str, Enum):
    ENQUIRY = "ENQUIRY"
    APPROVAL = "APPROVAL"
    CUSTOMER_SIGNAL = "CUSTOMER_SIGNAL"
    RISK_REVIEW = "RISK_REVIEW"
    OPERATIONAL_ACTION = "OPERATIONAL_ACTION"

class SourceType(str, Enum):
    DATABASE = "DATABASE"
    API = "API"
    FILE = "FILE"
    CRM = "CRM"
    ERP = "ERP"
    DATA_LAKE = "DATA_LAKE"
    EMAIL = "EMAIL"
    WEBFORM = "WEBFORM"

class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"

class RegistryRelationshipType(str, Enum):
    USES = "USES"
    OWNS = "OWNS"
    EXECUTES = "EXECUTES"
    APPROVES = "APPROVES"
    GOVERNED_BY = "GOVERNED_BY"
    CONNECTED_TO = "CONNECTED_TO"
    CONSUMES = "CONSUMES"
    PRODUCES = "PRODUCES"

class RegistryAuditEventType(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    DELETED = "DELETED"
    RELATIONSHIP_ADDED = "RELATIONSHIP_ADDED"
    RELATIONSHIP_REMOVED = "RELATIONSHIP_REMOVED"

class EntityType(str, Enum):
    MODEL = "MODEL"
    AGENT = "AGENT"
    TOOL = "TOOL"
    WORKFLOW = "WORKFLOW"
    DATA_SOURCE = "DATA_SOURCE"
    USER = "USER"
    DEPARTMENT = "DEPARTMENT"
    ROLE = "ROLE"
