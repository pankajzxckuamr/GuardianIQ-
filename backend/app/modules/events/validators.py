"""
Event Validation Rules Implementation for Phase 4 Governance Event Store
WBS Reference: 4.3.4
Envelope Field Validation, Active Schema Registry Lookup & Secret Key Rejection
"""
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

SENSITIVE_KEYS = {"password", "token", "secret", "client_secret", "api_key", "private_key", "access_token"}
MAX_PAYLOAD_BYTES = 500 * 1024  # 500 KB limit

class EventValidator:
    """
    Validates governance events prior to persistence.
    Guarantees fail-fast rejection before any database write occurs.
    """

    @staticmethod
    def validate_required_fields(data: Dict[str, Any]) -> None:
        """Validates presence of all mandatory canonical envelope fields."""
        required_fields = [
            "tenant_id", "event_type", "event_version", "actor_json", 
            "subject_json", "classification", "retention_class"
        ]
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Event validation failed: Missing mandatory field '{field}'")

        actor = data.get("actor_json", {})
        if not isinstance(actor, dict) or "user_id" not in actor or not actor["user_id"]:
            raise ValueError("Event validation failed: actor_json must contain non-null user_id")

        subject = data.get("subject_json", {})
        if not isinstance(subject, dict) or "entity_type" not in subject or "entity_id" not in subject:
            raise ValueError("Event validation failed: subject_json must contain entity_type and entity_id")

    @staticmethod
    def validate_active_schema_registry(db: Session, event_type: str, version: str = "1.0") -> None:
        """Verifies event_type exists and is ACTIVE in event_schema_registry."""
        if not db:
            return  # Skip DB registry lookup if session unsupplied

        res = db.execute(
            text("SELECT is_active FROM event_schema_registry WHERE event_type = :type AND version = :ver LIMIT 1"),
            {"type": event_type, "ver": version}
        ).fetchone()

        if not res:
            raise ValueError(f"Event validation failed: Event type '{event_type}' (ver {version}) is not registered in event_schema_registry")
        if not res[0]:
            raise ValueError(f"Event validation failed: Event type '{event_type}' is INACTIVE in event_schema_registry")

    @staticmethod
    def detect_unredacted_secrets(obj: Any, path: str = "payload_json") -> None:
        """Recursively checks payload dictionary for unredacted sensitive keys."""
        if isinstance(obj, dict):
            for key, val in obj.items():
                lowered_key = str(key).lower()
                current_path = f"{path}.{key}"
                if lowered_key in SENSITIVE_KEYS:
                    if isinstance(val, str) and val != "***" and not val.startswith("REDACTED"):
                        raise ValueError(f"Event validation failed: Unredacted sensitive key '{key}' detected at {current_path}")
                EventValidator.detect_unredacted_secrets(val, current_path)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                EventValidator.detect_unredacted_secrets(item, f"{path}[{idx}]")

    @staticmethod
    def validate_payload_size(payload: Dict[str, Any]) -> None:
        """Enforces maximum payload size limit."""
        if payload is not None:
            serialized_len = len(json.dumps(payload).encode("utf-8"))
            if serialized_len > MAX_PAYLOAD_BYTES:
                raise ValueError(f"Event validation failed: Payload size ({serialized_len} bytes) exceeds maximum limit of {MAX_PAYLOAD_BYTES} bytes")

    @classmethod
    def validate_event(cls, db: Optional[Session], data: Dict[str, Any]) -> bool:
        """Master validation method executing all checks before persistence."""
        cls.validate_required_fields(data)
        
        event_type = data["event_type"]
        version = data.get("event_version", "1.0")
        if db:
            cls.validate_active_schema_registry(db, event_type, version)

        payload = data.get("payload_json", {})
        cls.validate_payload_size(payload)
        cls.detect_unredacted_secrets(payload)

        return True
