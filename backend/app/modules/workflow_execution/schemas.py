from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.shared.enums import RunStatus, TriggerType, RiskLevel

class WorkflowRunFailureResponse(BaseModel):
    id: UUID
    run_id: UUID
    failure_type: str | None
    failure_code: str | None
    failure_message: str | None
    failed_step_id: UUID | None
    retry_count: int
    max_retries: int
    escalation_required: bool
    escalation_sent_at: datetime | None
    next_retry_at: datetime | None
    version_no: int
    is_deleted: bool
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None
    updated_by: UUID | None

    model_config = ConfigDict(from_attributes=True)


class WorkflowRunOutputResponse(BaseModel):
    id: UUID
    run_id: UUID
    output_type: str | None
    severity: str | None
    risk_score: float | None
    findings_json: list[dict] | None
    recommendations_json: list[dict] | None
    evidence_json: dict | None
    raw_output_json: dict | None
    raw_output: str | None
    parse_status: str
    version_no: int
    is_deleted: bool
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None
    updated_by: UUID | None

    model_config = ConfigDict(from_attributes=True)


class WorkflowRunStepResponse(BaseModel):
    id: UUID
    run_id: UUID
    step_code: str
    step_order: int
    step_type: str | None
    step_status: str
    started_at: datetime | None
    completed_at: datetime | None
    input_json: dict | None
    output_json: dict | None
    error_message: str | None
    error_detail: str | None
    version_no: int
    is_deleted: bool
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None
    updated_by: UUID | None

    model_config = ConfigDict(from_attributes=True)


class WorkflowRunResponse(BaseModel):
    id: UUID
    schedule_id: UUID
    workflow_id: UUID
    run_code: str
    trigger_type: TriggerType
    triggered_by_user_id: UUID | None
    triggered_by_actor_type: str
    run_status: RunStatus
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    risk_level: RiskLevel | None
    summary: str | None
    context_json: dict | None
    result_json: dict | None
    version_no: int
    is_deleted: bool
    metadata_json: dict | None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None
    updated_by: UUID | None
    steps: list[WorkflowRunStepResponse]
    outputs: list[WorkflowRunOutputResponse]
    failures: list[WorkflowRunFailureResponse]

    model_config = ConfigDict(from_attributes=True)

class WorkflowRunDetailResponse(WorkflowRunResponse):
    pass


class WorkflowRunListItem(BaseModel):
    id: UUID
    run_code: str
    schedule_code: str
    workflow_name: str
    trigger_type: TriggerType
    run_status: RunStatus
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    risk_level: RiskLevel | None
    triggered_by_name: str | None

    model_config = ConfigDict(from_attributes=True)
