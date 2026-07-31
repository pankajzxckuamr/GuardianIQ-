"""
Event Security Service for GuardianIQ Phase 4 Governance Events.
WBS Reference: 4.5.2
Enforces tenant isolation, ABAC clearance checks, and payload redaction.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.registry.constants import DataClassification
from app.shared.redaction import PayloadRedactorService, CLASSIFICATION_RANK
from app.modules.authorization.abac_service import check_node_read_clearance

ROLE_CLEARANCE: Dict[str, str] = {
    "SUPER_ADMIN": DataClassification.RESTRICTED.value,
    "SYSTEM_ADMIN": DataClassification.RESTRICTED.value,
    "GOVERNANCE_ADMIN": DataClassification.RESTRICTED.value,
    "RISK_MANAGER": DataClassification.RESTRICTED.value,
    "COMPLIANCE_OFFICER": DataClassification.CONFIDENTIAL.value,
    "AI_REVIEWER": DataClassification.CONFIDENTIAL.value,
    "AI_ASSET_OWNER": DataClassification.CONFIDENTIAL.value,
    "BUSINESS_APPROVER": DataClassification.CONFIDENTIAL.value,
    "AUDITOR": DataClassification.CONFIDENTIAL.value,
    "BUSINESS_USER": DataClassification.INTERNAL.value,
    "USER": DataClassification.INTERNAL.value,
}

class EventSecurityService:
    @classmethod
    def get_user_clearance(cls, user: Any) -> str:
        """Resolves highest DataClassification clearance for a user based on roles."""
        user_roles = []
        if hasattr(user, "roles") and user.roles:
            user_roles = [r.role_code for r in user.roles if hasattr(r, "role_code")]
        elif hasattr(user, "role") and user.role:
            user_roles = [str(user.role)]

        if "ADMIN" in user_roles or "SUPER_ADMIN" in user_roles or "GOVERNANCE_ADMIN" in user_roles:
            return DataClassification.RESTRICTED.value

        max_rank = 1
        max_clearance = DataClassification.PUBLIC.value
        for r in user_roles:
            clearance = ROLE_CLEARANCE.get(r.upper(), DataClassification.INTERNAL.value)
            rank = CLASSIFICATION_RANK.get(clearance, 2)
            if rank > max_rank:
                max_rank = rank
                max_clearance = clearance

        return max_clearance

    @classmethod
    def can_view_event(cls, user: Any, event: Any, db: Optional[Session] = None) -> bool:
        """
        Returns True if user has tenant access and sufficient classification clearance to view event.
        """
        user_tenant_id = getattr(user, "tenant_id", None) or getattr(user, "id", None)
        event_tenant_id = getattr(event, "tenant_id", None)

        # 1. Tenant Isolation Check
        if user_tenant_id and event_tenant_id and str(user_tenant_id) != str(event_tenant_id):
            return False

        # 2. Classification Clearance Check
        user_clearance = cls.get_user_clearance(user)
        event_classification = getattr(event, "classification", DataClassification.INTERNAL.value)

        user_rank = CLASSIFICATION_RANK.get(user_clearance.upper(), 2)
        event_rank = CLASSIFICATION_RANK.get(event_classification.upper(), 2)

        return user_rank >= event_rank

    @classmethod
    def mask_payload(cls, user: Any, event: Any, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """
        Returns payload_json with secrets and clearance-restricted fields masked appropriately.
        """
        raw_payload = getattr(event, "payload_json", {})
        event_classification = getattr(event, "classification", DataClassification.INTERNAL.value)
        user_clearance = cls.get_user_clearance(user)

        return PayloadRedactorService.redact_by_clearance(
            raw_payload,
            user_clearance=user_clearance,
            event_classification=event_classification
        )

    @classmethod
    def filter_events_by_scope(
        cls,
        user: Any,
        events: List[Any],
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Filters list of events to user's scope and masks payloads.
        """
        scoped_events = []
        for event in events:
            if cls.can_view_event(user, event, db):
                masked_payload = cls.mask_payload(user, event, db)
                if hasattr(event, "model_dump"):
                    event_dict = event.model_dump()
                elif hasattr(event, "__dict__"):
                    event_dict = {k: v for k, v in event.__dict__.items() if not k.startswith("_")}
                else:
                    event_dict = dict(event)
                
                event_dict["payload_json"] = masked_payload
                scoped_events.append(event_dict)

        return scoped_events
