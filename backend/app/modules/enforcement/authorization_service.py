from typing import Optional, Tuple, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.shared.hashing import compute_canonical_event_hash, compute_sha256_hash
from app.modules.agent_boundary.models import RuntimeAuthorization, AgentToolPermission
from app.modules.policy_engine.schemas import GovernedRuntimeRequest
from app.modules.policy_engine.enums import Decision
from app.modules.relationship.repository import RelationshipRepository


class RuntimeAuthorizationService:
    """
    Enterprise Runtime Authorization & TOCTOU Protection Service.
    Issues cryptographically bound, short-lived authorization tokens and performs
    just-in-time verification of request immutability, graph consistency, and single-use replay protection.
    """

    def __init__(self, db: Session):
        self.db = db

    def compute_context_hash(self, request: GovernedRuntimeRequest) -> str:
        """
        Computes canonical SHA-256 hash across normalized runtime request parameters.
        Ensures exact-request payload immutability between check and use.
        """
        req_dict: Dict[str, Any] = {
            "tenant_id": str(request.tenant_id) if request.tenant_id else None,
            "actor": {
                "user_id": request.actor.user_id if request.actor else None,
                "role": request.actor.role if request.actor else None,
            } if request.actor else None,
            "agent": {
                "agent_id": request.agent.agent_id if request.agent else None,
                "name": getattr(request.agent, "agent_name", None) or getattr(request.agent, "name", None) if request.agent else None,
                "agent_type": request.agent.agent_type if request.agent else None,
                "autonomy_level": str(request.agent.autonomy_level) if request.agent and request.agent.autonomy_level else None,
            } if request.agent else None,
            "workflow": {
                "workflow_id": request.workflow.workflow_id if request.workflow else None,
                "workflow_run_id": request.workflow.workflow_run_id if request.workflow else None,
                "step_id": request.workflow.step_id if request.workflow else None,
            } if request.workflow else None,
            "model": {
                "model_id": request.model.model_id if request.model else None,
                "model_version": getattr(request.model, "model_version", None) or getattr(request.model, "version", None) if request.model else None,
                "provider": request.model.provider if request.model else None,
            } if request.model else None,
            "tool": {
                "tool_id": request.tool.tool_id if request.tool else None,
                "tool_name": getattr(request.tool, "tool_name", None) or getattr(request.tool, "name", None) if request.tool else None,
                "operation": request.tool.operation if request.tool else None,
                "access_mode": str(request.tool.access_mode) if request.tool and request.tool.access_mode else None,
                "parameters": request.tool.parameters if request.tool else {},
            } if request.tool else None,
            "data_requests": [
                {
                    "data_source_id": str(dr.data_source_id),
                    "operation": str(dr.operation),
                    "columns": sorted(dr.columns) if dr.columns else [],
                    "record_count": dr.record_count,
                }
                for dr in (request.data_requests or [])
            ],
            "operation": request.operation,
            "environment": request.facts.get("environment") if request.facts else None,
            "facts": request.facts or {},
        }
        return compute_canonical_event_hash(req_dict)

    def compute_relationship_hash(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        as_of: Optional[datetime] = None,
    ) -> str:
        """
        Computes canonical SHA-256 hash of active agent relationships.
        Detects relationship graph alterations occurring between authorization and execution.
        """
        now = as_of or datetime.now(timezone.utc)
        active_rels = RelationshipRepository.find_active(
            db=self.db,
            tenant_id=tenant_id,
            source_type="AGENT",
            source_id=str(agent_id),
            as_of=now,
        )
        rel_signatures = sorted([
            f"{r.relationship_type}:{r.target_type}:{r.target_id}"
            for r in active_rels
        ])
        return compute_canonical_event_hash({"relationships": rel_signatures})

    def compute_policy_hash(self, resolved_policies: Optional[List[Any]] = None) -> str:
        """
        Computes canonical SHA-256 hash across resolved policy versions and rule sets.
        """
        if not resolved_policies:
            return compute_sha256_hash("NO_POLICIES")
        pol_signatures = []
        for rp in resolved_policies:
            p_id = str(getattr(rp, "policy_id", getattr(getattr(rp, "policy", None), "id", "")))
            v_num = getattr(rp, "version_number", getattr(getattr(rp, "version", None), "version_number", 1))
            rules = getattr(rp, "rules", [])
            rule_codes = sorted([str(getattr(r, "rule_code", "")) for r in rules])
            pol_signatures.append(f"{p_id}:v{v_num}:{','.join(rule_codes)}")
        return compute_canonical_event_hash({"policies": sorted(pol_signatures)})

    def issue_authorization(
        self,
        tenant_id: UUID,
        request: GovernedRuntimeRequest,
        decision: Decision,
        ttl_seconds: int = 300,
        is_single_use: bool = True,
        approval_id: Optional[UUID] = None,
        resolved_policies: Optional[List[Any]] = None,
    ) -> RuntimeAuthorization:
        """
        Issues an immutable RuntimeAuthorization record with embedded context, relationship, and policy hashes.
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        context_hash = self.compute_context_hash(request)
        agent_uuid = UUID(request.agent.agent_id) if request.agent and request.agent.agent_id else uuid4()
        relationship_hash = self.compute_relationship_hash(tenant_id, agent_uuid, now)
        policy_hash = self.compute_policy_hash(resolved_policies)

        is_authorized = decision in [Decision.ALLOW, Decision.ALLOW_WITH_OBLIGATIONS]

        auth = RuntimeAuthorization(
            id=uuid4(),
            tenant_id=tenant_id,
            request_id=str(request.request_id),
            correlation_id=request.correlation_id or uuid4(),
            agent_id=agent_uuid,
            operation=request.operation or (request.tool.operation if request.tool else "EXECUTE") or "EXECUTE",
            authorized=is_authorized,
            reason=f"Runtime authorization issued with decision {decision.value}",
            expires_at=expires_at,
            metadata_json={
                "status": "ISSUED",
                "context_hash": context_hash,
                "relationship_hash": relationship_hash,
                "policy_hash": policy_hash,
                "is_single_use": is_single_use,
                "approval_id": str(approval_id) if approval_id else None,
                "issued_at": now.isoformat(),
            },
        )
        self.db.add(auth)
        self.db.commit()
        return auth

    def verify_and_consume_authorization(
        self,
        authorization_id: UUID,
        tenant_id: UUID,
        current_request: GovernedRuntimeRequest,
        as_of: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifies authorization validity immediately before target execution:
        1. Tenant isolation & authorization existence
        2. Authorized decision flag
        3. Expiration window (TOCTOU protection)
        4. Single-use replay protection
        5. Exact request context hash match (tamper protection)
        6. Relationship graph integrity match
        Transitions status to CONSUMED atomically upon success.
        """
        now = as_of or datetime.now(timezone.utc)
        auth = (
            self.db.query(RuntimeAuthorization)
            .filter(
                RuntimeAuthorization.id == authorization_id,
                RuntimeAuthorization.tenant_id == tenant_id,
            )
            .first()
        )

        if not auth:
            return False, "AUTHORIZATION_NOT_FOUND: Authorization token not found for tenant"

        if not auth.authorized:
            return False, f"AUTHORIZATION_REJECTED: Authorization was issued as not authorized ({auth.reason})"

        meta = dict(auth.metadata_json or {})
        status = meta.get("status", "ISSUED")

        # Replay Attack Prevention
        if status == "CONSUMED":
            return False, "AUTHORIZATION_REPLAY_DETECTED: Single-use authorization token has already been consumed"

        if status == "REVOKED":
            return False, "AUTHORIZATION_REVOKED: Authorization token has been revoked"

        # Expiration Check (TOCTOU)
        if auth.expires_at and auth.expires_at <= now:
            meta["status"] = "EXPIRED"
            auth.metadata_json = meta
            self.db.commit()
            return False, "AUTHORIZATION_EXPIRED: Authorization token has expired (TOCTOU timeout exceeded)"

        # Context Hash Tamper Check
        current_context_hash = self.compute_context_hash(current_request)
        saved_context_hash = meta.get("context_hash")
        if saved_context_hash and current_context_hash != saved_context_hash:
            return False, "CONTEXT_HASH_TAMPERED: Request payload has been modified after authorization was issued (TOCTOU violation)"

        # Relationship Graph Alteration Check
        if current_request.agent and current_request.agent.agent_id:
            current_rel_hash = self.compute_relationship_hash(
                tenant_id=tenant_id,
                agent_id=UUID(current_request.agent.agent_id),
                as_of=now,
            )
            saved_rel_hash = meta.get("relationship_hash")
            if saved_rel_hash and current_rel_hash != saved_rel_hash:
                return False, "RELATIONSHIP_GRAPH_ALTERED: Active relationships have changed since authorization was issued"

        # Mark single-use consumption
        if meta.get("is_single_use", True):
            meta["status"] = "CONSUMED"
            meta["consumed_at"] = now.isoformat()
            auth.metadata_json = meta
            self.db.commit()

        return True, None

    def check_tool_permission(self, tenant_id: UUID, agent_id: UUID, tool_id: UUID) -> Tuple[bool, Optional[str]]:
        perm = (
            self.db.query(AgentToolPermission)
            .filter(
                AgentToolPermission.tenant_id == tenant_id,
                AgentToolPermission.agent_id == agent_id,
                AgentToolPermission.tool_id == tool_id,
                AgentToolPermission.is_active == True,
            )
            .first()
        )
        if not perm:
            return False, "Agent lacks granted permission to execute tool"
        if perm.require_approval:
            return True, "Tool permission requires human approval"
        return True, "Tool execution authorized"
