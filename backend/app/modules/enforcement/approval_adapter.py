from typing import Optional, Tuple, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.modules.policy_engine.models import PolicyApproval, PolicyException, GovernancePolicy
from app.modules.policy_engine.schemas import GovernedRuntimeRequest
from app.modules.enforcement.authorization_service import RuntimeAuthorizationService
from app.modules.workflow_scheduler.models import Phase2WorkflowSchedule
from app.modules.agent.models import Agent


class ApprovalExceptionAdapter:
    """
    Stable Adapter Contract for Policy Approvals, Exceptions, and Security Escalations.
    Isolates Phase 5 approval records from legacy recommendation approvals while ensuring
    post-approval TOCTOU immutability and active exception lookups.
    """

    def __init__(self, db: Session):
        self.db = db
        self.auth_service = RuntimeAuthorizationService(db)

    def request_approval(
        self,
        tenant_id: UUID,
        request: GovernedRuntimeRequest,
        policy_id: UUID,
        required_role: str,
        timeout_minutes: int = 60,
        tier: int = 1,
        evaluation_id: Optional[UUID] = None,
        context_hash: Optional[str] = None,
    ) -> PolicyApproval:
        """
        Creates a dedicated PolicyApproval record linked to the request context hash.
        """
        now = datetime.now(timezone.utc)
        computed_hash = context_hash or self.auth_service.compute_context_hash(request)

        approval = PolicyApproval(
            id=uuid4(),
            tenant_id=tenant_id,
            request_id=str(request.request_id),
            correlation_id=request.correlation_id or uuid4(),
            policy_id=policy_id,
            evaluation_id=evaluation_id,
            approval_tier=tier,
            required_role=required_role,
            status="PENDING",
            timeout_at=now + timedelta(minutes=timeout_minutes),
            metadata_json={
                "context_hash": computed_hash,
                "created_at": now.isoformat(),
            },
        )
        self.db.add(approval)
        self.db.commit()
        return approval

    def record_approval_decision(
        self,
        approval_id: UUID,
        tenant_id: UUID,
        approver_id: UUID,
        decision: str,  # APPROVED or REJECTED
        reason: Optional[str] = None,
    ) -> Optional[PolicyApproval]:
        """
        Records human reviewer decision for a pending policy approval.
        """
        approval = (
            self.db.query(PolicyApproval)
            .filter(
                PolicyApproval.id == approval_id,
                PolicyApproval.tenant_id == tenant_id,
            )
            .first()
        )
        if not approval:
            return None

        status = decision.upper()
        if status not in ["APPROVED", "REJECTED"]:
            status = "REJECTED"

        approval.status = status
        approval.approver_id = approver_id
        approval.decision_reason = reason
        self.db.commit()
        return approval

    def check_approval_status(
        self,
        request_id: str,
        tenant_id: UUID,
        current_request: Optional[GovernedRuntimeRequest] = None,
        as_of: Optional[datetime] = None,
    ) -> Tuple[bool, str, Optional[PolicyApproval]]:
        """
        Validates approval state and verifies that the post-approval request payload has not been tampered with.
        """
        now = as_of or datetime.now(timezone.utc)
        approval = (
            self.db.query(PolicyApproval)
            .filter(
                PolicyApproval.request_id == request_id,
                PolicyApproval.tenant_id == tenant_id,
            )
            .first()
        )

        if not approval:
            return False, "NO_APPROVAL_RECORD", None

        # Expiration Check
        if approval.status == "PENDING" and approval.timeout_at and approval.timeout_at <= now:
            approval.status = "EXPIRED"
            self.db.commit()
            return False, "APPROVAL_EXPIRED", approval

        if approval.status == "PENDING":
            return False, "APPROVAL_PENDING", approval

        if approval.status == "REJECTED":
            return False, "APPROVAL_REJECTED", approval

        if approval.status == "EXPIRED":
            return False, "APPROVAL_EXPIRED", approval

        if approval.status == "APPROVED":
            # TOCTOU Immutability Check: verify current payload matches approved payload
            if current_request:
                current_hash = self.auth_service.compute_context_hash(current_request)
                saved_hash = (approval.metadata_json or {}).get("context_hash")
                if saved_hash and current_hash != saved_hash:
                    return False, "CONTEXT_TAMPERED_POST_APPROVAL", approval

            return True, "APPROVED", approval

        return False, f"UNKNOWN_STATUS_{approval.status}", approval

    def lookup_active_exception(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        target_type: str,
        target_id: str,
        as_of: Optional[datetime] = None,
    ) -> Optional[PolicyException]:
        """
        Looks up time-bounded, active policy exceptions granting valid execution override.
        """
        now = as_of or datetime.now(timezone.utc)
        exception = (
            self.db.query(PolicyException)
            .filter(
                PolicyException.tenant_id == tenant_id,
                PolicyException.policy_id == policy_id,
                PolicyException.target_type == target_type,
                PolicyException.target_id == str(target_id),
                PolicyException.status == "ACTIVE",
                PolicyException.valid_from <= now,
                PolicyException.valid_to >= now,
            )
            .first()
        )
        return exception

    def resolve_escalation_owner(
        self,
        tenant_id: UUID,
        schedule_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
    ) -> Optional[UUID]:
        """
        Resolves notification recipient user ID for ESCALATE security decisions.
        """
        if schedule_id:
            sched = (
                self.db.query(Phase2WorkflowSchedule)
                .filter(
                    Phase2WorkflowSchedule.id == schedule_id,
                    Phase2WorkflowSchedule.tenant_id == tenant_id,
                )
                .first()
            )
            if sched and sched.owner_user_id:
                return sched.owner_user_id

        if agent_id:
            agt = (
                self.db.query(Agent)
                .filter(
                    Agent.id == agent_id,
                    Agent.tenant_id == tenant_id,
                )
                .first()
            )
            if agt and getattr(agt, "owner_user_id", None):
                return agt.owner_user_id

        return None
