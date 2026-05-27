from fastapi import APIRouter
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper
from app.shared.enums.source_type import SourceType
from app.shared.enums.risk_level import RiskLevel
from app.shared.enums.recommendation_status import RecommendationStatus
from app.shared.enums.policy_status import PolicyStatus
from app.shared.enums.execution_mode import ExecutionMode
from app.shared.enums.audit_event_type import AuditEventType
from app.shared.enums.approval_status import ApprovalStatus

router = APIRouter(
    prefix="/api/foundation",
    tags=["Foundation"]
)

@router.get("/enums", response_model=StandardResponse[dict])
def get_system_enums():
    """Return all system enums for frontend use."""
    return ResponseHelper.success(
        message="System enums retrieved successfully",
        data={
            "SourceType": [e.value for e in SourceType],
            "RiskLevel": [e.value for e in RiskLevel],
            "RecommendationStatus": [e.value for e in RecommendationStatus],
            "PolicyStatus": [e.value for e in PolicyStatus],
            "ExecutionMode": [e.value for e in ExecutionMode],
            "AuditEventType": [e.value for e in AuditEventType],
            "ApprovalStatus": [e.value for e in ApprovalStatus]
        }
    )
