from uuid import UUID, uuid4
import pytest
from pydantic import ValidationError

from app.modules.policy_engine.enums import (
    AccessMode,
    AutonomyLevel,
    BindingStatus,
    DataClassification,
    DataOperation,
    Decision,
    EnforcementMode,
    PolicyStatus,
    SensitivityLevel,
    TargetType,
    VersionStatus,
    VersionStrategy,
)
from app.modules.policy_engine.schemas import (
    ActorContext,
    AgentContext,
    DataRequestContext,
    GovernedRuntimeRequest,
    GovernedRuntimeResponse,
    PolicyEvaluationResult,
    ToolContext,
)


def test_frozen_enums_values():
    assert Decision.ALLOW == "ALLOW"
    assert Decision.DENY == "DENY"
    assert Decision.MODIFY == "MODIFY"
    assert Decision.REQUIRE_APPROVAL == "REQUIRE_APPROVAL"

    assert PolicyStatus.ACTIVE == "ACTIVE"
    assert PolicyStatus.DRAFT == "DRAFT"
    assert VersionStatus.ACTIVE == "ACTIVE"
    assert BindingStatus.ACTIVE == "ACTIVE"

    assert TargetType.AGENT == "AGENT"
    assert TargetType.TOOL == "TOOL"
    assert TargetType.DATA_SOURCE == "DATA_SOURCE"

    assert VersionStrategy.LATEST == "LATEST"
    assert VersionStrategy.PINNED == "PINNED"

    assert AutonomyLevel.FULL_AUTONOMY == "FULL_AUTONOMY"
    assert AccessMode.READ_ONLY == "READ_ONLY"
    assert DataOperation.READ == "READ"
    assert EnforcementMode.BLOCKING == "BLOCKING"

    # Reused enums
    assert DataClassification.CONFIDENTIAL == "CONFIDENTIAL"
    assert SensitivityLevel.CRITICAL == "CRITICAL"


def test_governed_runtime_request_parsing():
    req_id = uuid4()
    corr_id = uuid4()

    req = GovernedRuntimeRequest(
        request_id=req_id,
        correlation_id=corr_id,
        actor=ActorContext(user_id="user_123", role="Analyst"),
        agent=AgentContext(agent_id="agent_007", autonomy_level=AutonomyLevel.HUMAN_SUPERVISED),
        tool=ToolContext(tool_id="tool_crm", tool_name="CustomerCRM", access_mode=AccessMode.READ_WRITE),
        data_requests=[
            DataRequestContext(
                data_source_id="ds_sql_1",
                table_name="customers",
                columns=["id", "name", "ssn"],
                operation=DataOperation.READ,
                classification=DataClassification.CONFIDENTIAL,
                sensitivity_level=SensitivityLevel.HIGH,
            )
        ],
        facts={"time_of_day": "14:00", "is_weekend": False},
        enforcement_mode=EnforcementMode.BLOCKING,
    )

    assert req.request_id == req_id
    assert req.correlation_id == corr_id
    assert req.agent.autonomy_level == AutonomyLevel.HUMAN_SUPERVISED
    assert req.data_requests[0].classification == DataClassification.CONFIDENTIAL

    # Check JSON export / import roundtrip
    dumped = req.model_dump_json()
    reloaded = GovernedRuntimeRequest.model_validate_json(dumped)
    assert reloaded.request_id == req_id
    assert reloaded.tool.access_mode == AccessMode.READ_WRITE


def test_governed_runtime_request_invalid_uuid():
    with pytest.raises(ValidationError):
        GovernedRuntimeRequest(request_id="invalid-uuid-string", correlation_id=uuid4())


def test_governed_runtime_response_construction():
    req_id = uuid4()
    corr_id = uuid4()

    resp = GovernedRuntimeResponse(
        request_id=req_id,
        correlation_id=corr_id,
        decision=Decision.REQUIRE_APPROVAL,
        reasons=["Sensitive column access requires two-layer supervisor approval"],
        policy_evaluations=[
            PolicyEvaluationResult(
                policy_id="pol_001",
                policy_name="DLP Policy",
                decision=Decision.REQUIRE_APPROVAL,
                reason="SSN column detected in read request",
            )
        ],
        execution_permitted=False,
    )

    assert resp.decision == Decision.REQUIRE_APPROVAL
    assert resp.execution_permitted is False
    assert len(resp.policy_evaluations) == 1
