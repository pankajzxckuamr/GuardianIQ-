import re
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from app.shared.enums import (
    ScheduleStatus,
    ScheduleType,
    ExecutionMode,
    AssignmentRole,
    RiskLevel,
    ConcurrencyPolicy,
)

class BoundaryRules(BaseModel):
    max_records: int
    allow_write_tools: bool
    requires_human_approval_for_high_risk: bool

    model_config = ConfigDict(from_attributes=True)


class RetryPolicy(BaseModel):
    max_retries: int = 1
    retry_delay_seconds: int = 300

    model_config = ConfigDict(from_attributes=True)


class AgentAssignmentCreate(BaseModel):
    agent_id: UUID
    model_id: UUID | None = None
    assignment_role: AssignmentRole = AssignmentRole.PRIMARY
    execution_mode: ExecutionMode = ExecutionMode.RECOMMEND_ONLY
    confidence_threshold: float | None = None
    allowed_tools: list[str] = Field(default_factory=list)
    allowed_data_sources: list[str] = Field(default_factory=list)
    blocked_operations: list[str] = Field(default_factory=list)
    boundary_rules: BoundaryRules

    @field_validator('confidence_threshold')
    @classmethod
    def validate_confidence(cls, v: float | None) -> float | None:
        if v is not None and (v < 0.0 or v > 100.0):
            raise ValueError('confidence_threshold must be between 0 and 100')
        return v

    model_config = ConfigDict(from_attributes=True)

class AgentAssignmentCreateRequest(AgentAssignmentCreate):
    pass


class AgentAssignmentResponse(BaseModel):
    id: UUID
    schedule_id: UUID
    agent_id: UUID
    agent_name: str | None = None
    model_id: UUID | None
    model_name: str | None = None
    assignment_role: AssignmentRole
    execution_mode: ExecutionMode
    confidence_threshold: float | None
    allowed_tools_json: list[str] | None
    allowed_data_sources_json: list[str] | None
    blocked_operations_json: list[str] | None
    boundary_rules_json: BoundaryRules | None
    status: str
    version_no: int
    is_deleted: bool
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None
    updated_by: UUID | None

    model_config = ConfigDict(from_attributes=True)


class WorkflowScheduleCreate(BaseModel):
    workflow_id: UUID
    schedule_code: str
    schedule_name: str
    schedule_type: ScheduleType
    cron_expression: str | None = None
    timezone: str = "Asia/Kolkata"
    start_at: datetime | None = None
    end_at: datetime | None = None
    concurrency_policy: ConcurrencyPolicy = ConcurrencyPolicy.SKIP_IF_RUNNING
    max_runtime_seconds: int = 1800
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    owner_user_id: UUID
    owner_department_id: UUID | None = None
    approval_required: bool = False
    approval_group_id: UUID | None = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    schedule_status: ScheduleStatus = ScheduleStatus.DRAFT
    metadata_json: dict | None = None
    agent_assignments: list[AgentAssignmentCreate] = Field(default_factory=list)

    @field_validator('schedule_code')
    @classmethod
    def validate_schedule_code(cls, v: str) -> str:
        if not re.match(r'^[A-Z0-9_]+$', v):
            raise ValueError('schedule_code must match pattern ^[A-Z0-9_]+$')
        return v

    @model_validator(mode='after')
    def validate_schedule(self) -> 'WorkflowScheduleCreate':
        if self.schedule_type == ScheduleType.CRON and not self.cron_expression:
            raise ValueError('cron_expression must be present when schedule_type is CRON')
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValueError('end_at must be greater than start_at')
        return self

    model_config = ConfigDict(from_attributes=True)

class WorkflowScheduleCreateRequest(WorkflowScheduleCreate):
    pass


class WorkflowScheduleUpdate(BaseModel):
    workflow_id: UUID | None = None
    schedule_code: str | None = None
    schedule_name: str | None = None
    schedule_type: ScheduleType | None = None
    cron_expression: str | None = None
    timezone: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    concurrency_policy: ConcurrencyPolicy | None = None
    max_runtime_seconds: int | None = None
    retry_policy: RetryPolicy | None = None
    owner_user_id: UUID | None = None
    owner_department_id: UUID | None = None
    approval_required: bool | None = None
    approval_group_id: UUID | None = None
    risk_level: RiskLevel | None = None
    schedule_status: ScheduleStatus | None = None
    metadata_json: dict | None = None
    agent_assignments: list[AgentAssignmentCreate] | None = None

    @model_validator(mode='after')
    def validate_schedule_update(self) -> 'WorkflowScheduleUpdate':
        if self.schedule_type == ScheduleType.CRON and not self.cron_expression:
            raise ValueError('cron_expression must be present when schedule_type is CRON')
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValueError('end_at must be greater than start_at')
        return self

    model_config = ConfigDict(from_attributes=True)


class WorkflowScheduleResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    schedule_code: str
    schedule_name: str
    schedule_type: ScheduleType
    cron_expression: str | None
    timezone: str
    start_at: datetime | None
    end_at: datetime | None
    next_run_at: datetime | None
    last_run_at: datetime | None
    concurrency_policy: ConcurrencyPolicy
    max_runtime_seconds: int
    retry_policy_json: dict | None
    owner_user_id: UUID
    owner_department_id: UUID | None
    approval_required: bool
    approval_group_id: UUID | None
    approval_status: str | None = None
    risk_level: RiskLevel
    schedule_status: ScheduleStatus
    version_no: int
    is_deleted: bool
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None
    updated_by: UUID | None
    agent_assignments: list[AgentAssignmentResponse]
    health_status: str
    is_overdue: bool

    model_config = ConfigDict(from_attributes=True)


class WorkflowScheduleListItem(BaseModel):
    id: UUID
    schedule_code: str
    schedule_name: str
    workflow_name: str
    schedule_type: ScheduleType
    schedule_status: ScheduleStatus
    risk_level: RiskLevel
    owner_name: str
    next_run_at: datetime | None
    last_run_at: datetime | None
    approval_required: bool
    health_status: str

    model_config = ConfigDict(from_attributes=True)
