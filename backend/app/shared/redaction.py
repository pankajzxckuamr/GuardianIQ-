"""
Consolidated Payload Redactor Service for GuardianIQ Phase 4 Governance Events & Audits.
WBS Reference: 4.5.2
"""
from typing import Dict, Any, Optional, Set, List
from app.modules.registry.constants import DataClassification

CLASSIFICATION_RANK: Dict[str, int] = {
    DataClassification.PUBLIC.value: 1,
    DataClassification.INTERNAL.value: 2,
    DataClassification.CONFIDENTIAL.value: 3,
    DataClassification.RESTRICTED.value: 4,
}

SECRET_KEY_PATTERNS: Set[str] = {
    "password",
    "token",
    "secret",
    "client_secret",
    "api_key",
    "apikey",
    "access_token",
    "private_key",
    "ssn",
    "credit_card",
    "cvv",
    "pin",
    "authorization"
}

class PayloadRedactorService:
    REDACTED_LABEL: str = "[REDACTED]"
    MASK_LABEL: str = "***"

    @classmethod
    def is_secret_key(cls, key: str) -> bool:
        """Returns True if key name matches known secret key patterns."""
        k = key.lower().replace("-", "_")
        return any(pattern in k for pattern in SECRET_KEY_PATTERNS)

    @classmethod
    def redact_secrets(cls, payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Recursively redacts secret keys (passwords, tokens, api keys) in a JSON payload.
        Extends the audit_service.py sanitize() behavior.
        """
        if not payload or not isinstance(payload, dict):
            return payload

        sanitized: Dict[str, Any] = {}
        for key, value in payload.items():
            if cls.is_secret_key(key):
                sanitized[key] = cls.REDACTED_LABEL
            elif isinstance(value, dict):
                sanitized[key] = cls.redact_secrets(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.redact_secrets(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    @classmethod
    def redact_by_clearance(
        cls,
        payload: Optional[Dict[str, Any]],
        user_clearance: str,
        event_classification: str
    ) -> Optional[Dict[str, Any]]:
        """
        Redacts payload if user's sensitivity clearance level is lower than event classification rank.
        """
        if not payload:
            return payload

        # First run secret redaction
        sanitized = cls.redact_secrets(payload) or {}

        user_rank = CLASSIFICATION_RANK.get(user_clearance.upper(), 2)
        event_rank = CLASSIFICATION_RANK.get(event_classification.upper(), 2)

        if user_rank < event_rank:
            # Mask payload contents for insufficient clearance
            return {
                "_redaction_notice": f"Payload masked: Clearance rank ({user_clearance}) below classification ({event_classification})",
                "masked": True,
                "data": cls.REDACTED_LABEL
            }

        return sanitized
