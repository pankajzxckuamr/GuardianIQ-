import json
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.modules.events.service import EventPublisherService
from app.modules.events.schemas import GovernanceEventCreate
from app.modules.events.models import GovernanceEvent


SENSITIVE_KEYS = {"password", "token", "secret", "client_secret", "api_key", "private_key", "access_token", "authorization"}


def sanitize_payload(obj: Any) -> Any:
    """Recursively sanitizes dictionaries and lists to redact raw sensitive tokens."""
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            if any(s in str(k).lower() for s in SENSITIVE_KEYS):
                cleaned[k] = "***"
            else:
                cleaned[k] = sanitize_payload(v)
        return cleaned
    elif isinstance(obj, list):
        return [sanitize_payload(item) for item in obj]
    return obj


class GovernanceEventEmitter:
    """
    Central Governance Event Integration Service for Phase 5 ENFORCE.
    Emits structured, categorized, and correlation-linked audit events across the complete
    enforcement pipeline with zero raw secret leakage.
    """

    EVENT_CATEGORY_MAP = {
        "POLICY_EVALUATED": "ENFORCEMENT",
        "POLICY_TRIGGERED": "ENFORCEMENT",
        "POLICY_RULE_EVALUATED": "ENFORCEMENT",
        "POLICY_CREATED": "POLICY",
        "POLICY_UPDATED": "POLICY",
        "POLICY_VERSION_ACTIVATED": "POLICY",
        "POLICY_BINDING_CREATED": "POLICY_BINDING",
        "AGENT_ACTION_REQUESTED": "AGENT_RUNTIME",
        "AGENT_ACTION_VALIDATED": "AGENT_RUNTIME",
        "AGENT_ACTION_BLOCKED": "AGENT_RUNTIME",
        "AGENT_ACTION_OVERRIDDEN": "AGENT_RUNTIME",
        "TOOL_ACCESS_ATTEMPTED": "TOOL_GOVERNANCE",
        "TOOL_ACCESS_DENIED": "TOOL_GOVERNANCE",
        "TOOL_EXECUTION_EVALUATED": "TOOL_GOVERNANCE",
        "DATA_ACCESS_REQUESTED": "DATA_GOVERNANCE",
        "DATA_ACCESS_DENIED": "DATA_GOVERNANCE",
        "DATA_ACCESS_EVALUATED": "DATA_GOVERNANCE",
        "DATA_TRANSFORMATION_APPLIED": "DATA_GOVERNANCE",
        "MODEL_INVOCATION_BLOCKED": "AGENT_BOUNDARY",
        "ACTION_EXECUTED": "RUNTIME",
        "ACTION_FAILED": "RUNTIME",
        "RUNTIME_AUTHORIZATION_EVALUATED": "ENFORCEMENT",
        "RUNTIME_ENFORCEMENT_APPLIED": "ENFORCEMENT",
    }

    def __init__(self, publisher: Optional[EventPublisherService] = None):
        self.publisher = publisher or EventPublisherService()

    @classmethod
    def ensure_schema_registered(cls, db: Session, event_type: str, category: str) -> None:
        """Ensures the event_type is registered in event_schema_registry with non-null category."""
        schema_json = json.dumps({
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": f"{event_type} Schema",
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "format": "uuid"},
                "tenant_id": {"type": "string", "format": "uuid"},
                "event_type": {"type": "string", "const": event_type},
                "event_category": {"type": "string", "const": category},
                "payload_json": {"type": "object"}
            },
            "required": ["event_id", "tenant_id", "event_type", "event_category", "payload_json"]
        })
        db.execute(text("""
            INSERT INTO event_schema_registry (id, event_type, version, json_schema, is_active, created_at)
            VALUES (gen_random_uuid(), :event_type, '1.0', CAST(:json_schema AS jsonb), TRUE, CURRENT_TIMESTAMP)
            ON CONFLICT (event_type, version) DO UPDATE 
            SET json_schema = EXCLUDED.json_schema, is_active = TRUE;
        """), {"event_type": event_type, "json_schema": schema_json})
        db.flush()

    def emit_event(
        self,
        db: Session,
        tenant_id: UUID,
        event_type: str,
        subject_type: str,
        subject_id: str,
        payload: Dict[str, Any],
        correlation_id: Optional[UUID] = None,
        causation_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        risk_context: Optional[Dict[str, Any]] = None,
        policy_context: Optional[Dict[str, Any]] = None,
        source_service: str = "enforcement-engine",
    ) -> GovernanceEvent:
        """
        Sanitizes payload, resolves category, ensures schema registry presence,
        and publishes the governance event with outbox persistence.
        """
        category = self.EVENT_CATEGORY_MAP.get(event_type, "ENFORCEMENT")
        self.ensure_schema_registered(db, event_type, category)

        cleaned_payload = sanitize_payload(payload)
        now = datetime.now(timezone.utc)

        event_create = GovernanceEventCreate(
            event_type=event_type,
            event_category=category,
            event_version="1.0",
            occurred_at=now,
            source_service=source_service,
            source_system="guardianiq-backend",
            actor_json={
                "user_id": str(actor_id or tenant_id),
                "roles": ["SYSTEM"],
                "ip_address": "127.0.0.1",
            },
            subject_json={
                "entity_type": subject_type,
                "entity_id": str(subject_id),
            },
            correlation_id=correlation_id or uuid4(),
            causation_id=causation_id,
            risk_context_json=risk_context or {},
            policy_context_json=policy_context or {},
            payload_json=cleaned_payload,
            classification="INTERNAL",
            retention_class="STANDARD_90_DAYS",
        )

        return self.publisher.publish_event(
            db=db,
            event_data=event_create,
            tenant_id=tenant_id,
        )

    # -------------------------------------------------------------------------
    # Specialized Event Emitters
    # -------------------------------------------------------------------------

    def emit_policy_evaluated(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        decision: str,
        reason: Optional[str],
        evaluated_policies: List[Dict[str, Any]],
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="POLICY_EVALUATED",
            subject_type="AGENT",
            subject_id=str(agent_id),
            correlation_id=correlation_id,
            payload={
                "decision": decision,
                "reason": reason,
                "evaluated_policies": evaluated_policies,
            },
        )

    def emit_policy_triggered(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        policy_id: str,
        rule_code: str,
        action: str,
        severity: str,
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="POLICY_TRIGGERED",
            subject_type="POLICY",
            subject_id=str(policy_id),
            correlation_id=correlation_id,
            payload={
                "rule_code": rule_code,
                "action": action,
                "severity": severity,
            },
        )

    def emit_agent_action_requested(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="AGENT_ACTION_REQUESTED",
            subject_type="AGENT",
            subject_id=str(agent_id),
            correlation_id=correlation_id,
            payload={
                "operation": operation,
                "parameters": parameters or {},
            },
        )

    def emit_agent_action_validated(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        operation: str,
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="AGENT_ACTION_VALIDATED",
            subject_type="AGENT",
            subject_id=str(agent_id),
            correlation_id=correlation_id,
            payload={
                "operation": operation,
                "validation_status": "PASSED",
            },
        )

    def emit_agent_action_blocked(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        operation: str,
        reason: str,
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="AGENT_ACTION_BLOCKED",
            subject_type="AGENT",
            subject_id=str(agent_id),
            correlation_id=correlation_id,
            payload={
                "operation": operation,
                "reason": reason,
            },
        )

    def emit_tool_access_attempted(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        tool_id: str,
        operation: str,
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="TOOL_ACCESS_ATTEMPTED",
            subject_type="TOOL",
            subject_id=str(tool_id),
            correlation_id=correlation_id,
            payload={
                "agent_id": str(agent_id),
                "operation": operation,
            },
        )

    def emit_tool_access_denied(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        tool_id: str,
        reason: str,
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="TOOL_ACCESS_DENIED",
            subject_type="TOOL",
            subject_id=str(tool_id),
            correlation_id=correlation_id,
            payload={
                "agent_id": str(agent_id),
                "reason": reason,
            },
        )

    def emit_data_access_requested(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        data_source_id: str,
        operation: str,
        columns: Optional[List[str]] = None,
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="DATA_ACCESS_REQUESTED",
            subject_type="DATA_SOURCE",
            subject_id=str(data_source_id),
            correlation_id=correlation_id,
            payload={
                "agent_id": str(agent_id),
                "operation": operation,
                "columns": columns or [],
            },
        )

    def emit_data_access_denied(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        data_source_id: str,
        reason: str,
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="DATA_ACCESS_DENIED",
            subject_type="DATA_SOURCE",
            subject_id=str(data_source_id),
            correlation_id=correlation_id,
            payload={
                "agent_id": str(agent_id),
                "reason": reason,
            },
        )

    def emit_data_transformation_applied(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        data_source_id: str,
        transformation_map: Dict[str, str],
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="DATA_TRANSFORMATION_APPLIED",
            subject_type="DATA_SOURCE",
            subject_id=str(data_source_id),
            correlation_id=correlation_id,
            payload={
                "agent_id": str(agent_id),
                "transformation_map": transformation_map,
            },
        )

    def emit_model_invocation_blocked(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        model_id: str,
        reason: str,
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="MODEL_INVOCATION_BLOCKED",
            subject_type="MODEL",
            subject_id=str(model_id),
            correlation_id=correlation_id,
            payload={
                "agent_id": str(agent_id),
                "reason": reason,
            },
        )

    def emit_action_executed(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        operation: str,
        latency_ms: Optional[float] = None,
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="ACTION_EXECUTED",
            subject_type="AGENT",
            subject_id=str(agent_id),
            correlation_id=correlation_id,
            payload={
                "operation": operation,
                "latency_ms": latency_ms,
                "status": "SUCCESS",
            },
        )

    def emit_action_failed(
        self,
        db: Session,
        tenant_id: UUID,
        correlation_id: UUID,
        agent_id: str,
        operation: str,
        error_message: str,
    ) -> GovernanceEvent:
        return self.emit_event(
            db=db,
            tenant_id=tenant_id,
            event_type="ACTION_FAILED",
            subject_type="AGENT",
            subject_id=str(agent_id),
            correlation_id=correlation_id,
            payload={
                "operation": operation,
                "error_message": error_message,
                "status": "FAILED",
            },
        )
