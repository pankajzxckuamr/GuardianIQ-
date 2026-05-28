from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.modules.registry.constants import (
    EntityStatus, ModelType, AgentType, AgentExecutionMode,
    ToolCategory, AccessMode, WorkflowType, SourceType,
    DataClassification, SensitivityLevel
)

# ---------------------------------------------------------
# AI Model Schemas
# ---------------------------------------------------------

class AIModelBase(BaseModel):
    model_name: str
    model_type: ModelType
    provider: Optional[str] = None
    version: Optional[str] = None
    purpose: str
    owner_user_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    risk_level: str
    deployment_environment: Optional[str] = None
    status: EntityStatus = EntityStatus.DRAFT
    metadata_json: Optional[dict] = None

class AIModelCreate(AIModelBase):
    model_code: str = Field(..., min_length=1)

class AIModelUpdate(BaseModel):
    model_name: Optional[str] = None
    model_type: Optional[ModelType] = None
    provider: Optional[str] = None
    version: Optional[str] = None
    purpose: Optional[str] = None
    owner_user_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    risk_level: Optional[str] = None
    deployment_environment: Optional[str] = None
    status: Optional[EntityStatus] = None
    metadata_json: Optional[dict] = None

class AIModelResponse(AIModelBase):
    id: UUID
    model_code: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True

class AIModelListResponse(BaseModel):
    items: List[AIModelResponse]
    total: int
    page: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ---------------------------------------------------------
# AI Agent Schemas
# ---------------------------------------------------------

class AIAgentBase(BaseModel):
    agent_name: str
    agent_type: AgentType
    description: Optional[str] = None
    owner_user_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    execution_mode: AgentExecutionMode
    risk_level: str
    confidence_threshold: Optional[float] = None
    status: EntityStatus = EntityStatus.DRAFT
    capabilities_json: Optional[dict] = None
    metadata_json: Optional[dict] = None

class AIAgentCreate(AIAgentBase):
    agent_code: str = Field(..., min_length=1)

class AIAgentUpdate(BaseModel):
    agent_name: Optional[str] = None
    agent_type: Optional[AgentType] = None
    description: Optional[str] = None
    owner_user_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    execution_mode: Optional[AgentExecutionMode] = None
    risk_level: Optional[str] = None
    confidence_threshold: Optional[float] = None
    status: Optional[EntityStatus] = None
    capabilities_json: Optional[dict] = None
    metadata_json: Optional[dict] = None

class AIAgentResponse(AIAgentBase):
    id: UUID
    agent_code: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True

class AIAgentListResponse(BaseModel):
    items: List[AIAgentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ---------------------------------------------------------
# Shared Schemas
# ---------------------------------------------------------

class StatusChangeRequest(BaseModel):
    status: EntityStatus
    reason: Optional[str] = None

# ---------------------------------------------------------
# Tool Schemas
# ---------------------------------------------------------

class ToolBase(BaseModel):
    tool_name: str
    tool_category: ToolCategory
    access_mode: AccessMode
    owner_user_id: UUID
    sensitivity_level: str
    allowed_operations_json: list = Field(default_factory=list)
    endpoint_reference: Optional[str] = None
    status: EntityStatus = EntityStatus.ACTIVE
    metadata_json: Optional[dict] = None

class ToolCreate(ToolBase):
    tool_code: str = Field(..., min_length=1)

class ToolUpdate(BaseModel):
    tool_name: Optional[str] = None
    tool_category: Optional[ToolCategory] = None
    access_mode: Optional[AccessMode] = None
    owner_user_id: Optional[UUID] = None
    sensitivity_level: Optional[str] = None
    allowed_operations_json: Optional[list] = None
    endpoint_reference: Optional[str] = None
    status: Optional[EntityStatus] = None
    metadata_json: Optional[dict] = None

class ToolResponse(ToolBase):
    id: UUID
    tool_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ToolListResponse(BaseModel):
    items: List[ToolResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ---------------------------------------------------------
# Workflow Schemas
# ---------------------------------------------------------

class WorkflowBase(BaseModel):
    workflow_name: str
    workflow_type: WorkflowType
    department_id: UUID
    owner_user_id: UUID
    description: Optional[str] = None
    approval_required: bool = False
    business_criticality: str
    status: EntityStatus = EntityStatus.DRAFT
    steps_json: Optional[list] = None
    metadata_json: Optional[dict] = None

class WorkflowCreate(WorkflowBase):
    workflow_code: str = Field(..., min_length=1)

class WorkflowUpdate(BaseModel):
    workflow_name: Optional[str] = None
    workflow_type: Optional[WorkflowType] = None
    department_id: Optional[UUID] = None
    owner_user_id: Optional[UUID] = None
    description: Optional[str] = None
    approval_required: Optional[bool] = None
    business_criticality: Optional[str] = None
    status: Optional[EntityStatus] = None
    steps_json: Optional[list] = None
    metadata_json: Optional[dict] = None

class WorkflowResponse(WorkflowBase):
    id: UUID
    workflow_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WorkflowListResponse(BaseModel):
    items: List[WorkflowResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ---------------------------------------------------------
# Department Schemas
# ---------------------------------------------------------

class DepartmentBase(BaseModel):
    department_name: str
    parent_department_id: Optional[UUID] = None
    business_owner_user_id: Optional[UUID] = None
    escalation_owner_user_id: Optional[UUID] = None
    status: EntityStatus = EntityStatus.ACTIVE
    metadata_json: Optional[dict] = None

class DepartmentCreate(DepartmentBase):
    department_code: str = Field(..., min_length=1)

class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = None
    parent_department_id: Optional[UUID] = None
    business_owner_user_id: Optional[UUID] = None
    escalation_owner_user_id: Optional[UUID] = None
    status: Optional[EntityStatus] = None
    metadata_json: Optional[dict] = None

class DepartmentResponse(DepartmentBase):
    id: UUID
    department_code: str
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

class DepartmentListResponse(BaseModel):
    items: List[DepartmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class DepartmentLookup(BaseModel):
    id: UUID
    department_name: str
    department_code: str
    class Config: from_attributes = True

# ---------------------------------------------------------
# Role Schemas
# ---------------------------------------------------------

class RoleBase(BaseModel):
    role_name: str
    role_type: str
    permissions_json: dict = Field(default_factory=dict)
    status: EntityStatus = EntityStatus.ACTIVE

class RoleCreate(RoleBase):
    role_code: str = Field(..., min_length=1)

class RoleUpdate(BaseModel):
    role_name: Optional[str] = None
    role_type: Optional[str] = None
    permissions_json: Optional[dict] = None
    status: Optional[EntityStatus] = None

class RoleResponse(RoleBase):
    id: UUID
    role_code: str
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

class RoleListResponse(BaseModel):
    items: List[RoleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class RoleLookup(BaseModel):
    id: UUID
    role_name: str
    role_code: str
    class Config: from_attributes = True

# ---------------------------------------------------------
# GuardianUser Schemas
# ---------------------------------------------------------

class GuardianUserBase(BaseModel):
    full_name: str
    department_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    approval_limit_level: Optional[str] = None
    status: EntityStatus = EntityStatus.ACTIVE

class GuardianUserCreate(GuardianUserBase):
    email: str = Field(..., min_length=5)

class GuardianUserUpdate(BaseModel):
    full_name: Optional[str] = None
    department_id: Optional[UUID] = None
    role_id: Optional[UUID] = None
    approval_limit_level: Optional[str] = None
    status: Optional[EntityStatus] = None

class GuardianUserResponse(GuardianUserBase):
    id: UUID
    email: str
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

class GuardianUserListResponse(BaseModel):
    items: List[GuardianUserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class GuardianUserLookup(BaseModel):
    id: UUID
    full_name: str
    email: str
    class Config: from_attributes = True

# ---------------------------------------------------------
# DataSource Schemas
# ---------------------------------------------------------

class DataSourceBase(BaseModel):
    source_name: str
    source_type: SourceType
    owner_user_id: UUID
    department_id: Optional[UUID] = None
    classification: DataClassification
    sensitivity_level: SensitivityLevel
    region: Optional[str] = None
    contains_pii: bool = False
    retention_policy: Optional[str] = None
    connection_reference: Optional[str] = None
    status: EntityStatus = EntityStatus.ACTIVE
    metadata_json: Optional[dict] = None

class DataSourceCreate(DataSourceBase):
    source_code: str = Field(..., min_length=1)

class DataSourceUpdate(BaseModel):
    source_name: Optional[str] = None
    source_type: Optional[SourceType] = None
    owner_user_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    classification: Optional[DataClassification] = None
    sensitivity_level: Optional[SensitivityLevel] = None
    region: Optional[str] = None
    contains_pii: Optional[bool] = None
    retention_policy: Optional[str] = None
    connection_reference: Optional[str] = None
    status: Optional[EntityStatus] = None
    metadata_json: Optional[dict] = None

class DataSourceResponse(DataSourceBase):
    id: UUID
    source_code: str
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

class DataSourceListResponse(BaseModel):
    items: List[DataSourceResponse]
    total: int
    page: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ---------------------------------------------------------
# Relationship Schemas
# ---------------------------------------------------------

class RelationshipCreate(BaseModel):
    source_entity_type: str
    source_entity_id: UUID
    target_entity_type: str
    target_entity_id: UUID
    relationship_type: str
    metadata_json: Optional[dict] = None

class RelationshipResponse(BaseModel):
    id: UUID
    source_entity_type: str
    source_entity_id: UUID
    target_entity_type: str
    target_entity_id: UUID
    relationship_type: str
    status: EntityStatus
    metadata_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

class RelationshipDetailItem(BaseModel):
    id: UUID
    relationship_type: str
    other_entity_type: str
    other_entity_id: UUID
    other_entity_name: str
    status: EntityStatus

class RelationshipGroupedResponse(BaseModel):
    outgoing: List[RelationshipDetailItem]
    incoming: List[RelationshipDetailItem]

# ---------------------------------------------------------
# Audit Schemas
# ---------------------------------------------------------

class AuditResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    event_type: str
    changed_by: UUID
    changed_by_name: Optional[str] = None
    changed_by_email: Optional[str] = None
    before_json: Optional[dict] = None
    after_json: Optional[dict] = None
    change_summary: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True

class AuditListResponse(BaseModel):
    items: List[AuditResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ---------------------------------------------------------
# Search Schemas
# ---------------------------------------------------------

class SearchResultItem(BaseModel):
    id: UUID
    name: str
    code: str
    entity_type: str
    status: str

class GlobalSearchResponse(BaseModel):
    models: List[SearchResultItem]
    agents: List[SearchResultItem]
    tools: List[SearchResultItem]
    workflows: List[SearchResultItem]
    users: List[SearchResultItem]
    data_sources: List[SearchResultItem]

