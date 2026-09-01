from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.modules.policy_engine.enums import (
    AccessMode,
    AutonomyLevel,
    DataClassification,
    DataOperation,
    Decision,
    EnforcementMode,
    SensitivityLevel,
    TargetType,
)


class ActorContext(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentContext(BaseModel):
    agent_id: str
    name: Optional[str] = None
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None
    risk_level: Optional[str] = None
    autonomy_level: Optional[Union[AutonomyLevel, str]] = None
    owner_user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowContext(BaseModel):
    workflow_id: Optional[str] = None
    workflow_run_id: Optional[str] = None
    workflow_name: Optional[str] = None
    step_id: Optional[str] = None
    workflow_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelContext(BaseModel):
    model_id: Optional[str] = None
    name: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    version: Optional[str] = None
    provider: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ToolContext(BaseModel):
    tool_id: Optional[str] = None
    tool_name: Optional[str] = None
    category: Optional[str] = None
    operation: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    access_mode: Optional[AccessMode] = None


class DataRequestContext(BaseModel):
    data_source_id: str
    table_name: Optional[str] = None
    columns: List[str] = Field(default_factory=list)
    operation: DataOperation = DataOperation.READ
    classification: Optional[DataClassification] = None
    sensitivity_level: Optional[SensitivityLevel] = None
    record_count: Optional[int] = None
    query: Optional[str] = None
    filter_criteria: Dict[str, Any] = Field(default_factory=dict)


class GovernedRuntimeRequest(BaseModel):
    """Canonical Governed Runtime Request Envelope used across boundary evaluation, gateway, and UI simulation."""
    request_id: UUID = Field(default_factory=uuid4, description="Unique UUID identifying this runtime evaluation request")
    correlation_id: UUID = Field(default_factory=uuid4, description="Correlation UUID for tracing across execution steps")
    tenant_id: Optional[UUID] = None
    actor: Optional[ActorContext] = None
    agent: Optional[AgentContext] = None
    workflow: Optional[WorkflowContext] = None
    model: Optional[ModelContext] = None
    operation: Optional[str] = Field(default=None, description="Operation name or intent being governed")
    tool: Optional[ToolContext] = None
    data: Optional[DataRequestContext] = None
    data_requests: List[DataRequestContext] = Field(default_factory=list)
    facts: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary evaluation facts & environment attributes")
    idempotency_key: Optional[str] = None
    enforcement_mode: EnforcementMode = EnforcementMode.BLOCKING


class RuleEvaluationDetail(BaseModel):
    rule_id: str
    rule_name: Optional[str] = None
    rule_code: Optional[str] = None
    rule_type: Optional[str] = "GENERAL"
    matched: bool
    decision: Decision
    action: Optional[str] = None
    severity: Optional[str] = None
    reason: Optional[str] = None
    evaluation_order: int = 0
    evaluation_time_ms: Optional[float] = None
    error_message: Optional[str] = None


class PolicyEvaluationResult(BaseModel):
    policy_id: str
    policy_name: Optional[str] = None
    policy_code: Optional[str] = None
    policy_version_id: Optional[str] = None
    version_number: Optional[int] = None
    decision: Decision
    reason: Optional[str] = None
    rule_evaluations: List[RuleEvaluationDetail] = Field(default_factory=list)
    rules_evaluated: List[RuleEvaluationDetail] = Field(default_factory=list)
    violations: List[Union[ViolationDetail, str]] = Field(default_factory=list)
    obligations: List[Dict[str, Any]] = Field(default_factory=list)
    approval_requirements: List[ApprovalRequirement] = Field(default_factory=list)


class ApprovalRequirement(BaseModel):
    approval_type: str = Field(description="e.g. 2_LAYER_APPROVAL, LINE_MANAGER, DPO_OFFICER")
    tier_1_role: Optional[str] = None
    tier_2_role: Optional[str] = None
    required_role: Optional[str] = None
    reason: Optional[str] = None
    timeout_minutes: int = 60
    metadata: Dict[str, Any] = Field(default_factory=dict)
    metadata_json: Optional[Dict[str, Any]] = None


class ViolationDetail(BaseModel):
    policy_id: Optional[str] = None
    rule_id: Optional[str] = None
    rule_code: Optional[str] = None
    violation_code: Optional[str] = None
    message: str
    severity: str = "ERROR"
    target_type: Optional[TargetType] = None
    target_id: Optional[str] = None


class GovernedRuntimeResponse(BaseModel):
    """Canonical Governed Runtime Response Envelope returning deterministic enforcement decisions."""
    request_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    decision: Decision
    reason: Optional[str] = None
    reasons: List[str] = Field(default_factory=list)
    enforced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evaluated_at: Optional[datetime] = None
    modified_payload: Optional[Dict[str, Any]] = None
    approval_requirements: Optional[List[ApprovalRequirement]] = None
    violations: List[Union[ViolationDetail, str]] = Field(default_factory=list)
    obligations: List[Dict[str, Any]] = Field(default_factory=list)
    policy_evaluations: List[PolicyEvaluationResult] = Field(default_factory=list)
    trace: Optional[Dict[str, Any]] = None
    execution_permitted: bool = True
    latency_ms: Optional[float] = None


