from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timezone
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.modules.ai_model.models import AIModel, AIModelProvider
from app.modules.relationship.repository import RelationshipRepository
from app.modules.policy_engine.enums import Decision, DataClassification


@dataclass
class ModelGuardResult:
    decision: Decision
    is_permitted: bool
    model: Optional[AIModel] = None
    provider: Optional[AIModelProvider] = None
    reason: Optional[str] = None
    violations: List[str] = field(default_factory=list)
    obligations: List[Dict[str, Any]] = field(default_factory=list)


class ModelProviderGuard:
    """
    Enterprise AI Model and Provider Guard.
    Validates USES_MODEL graph relationship prerequisite, model status & approved version,
    deployment environment compatibility, provider data residency & classification compatibility,
    and blocks unauthorized fallback models.
    """

    def __init__(self, db: Session):
        self.db = db

    def evaluate_model_invocation(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        model_id: UUID,
        requested_version: Optional[str] = None,
        environment: Optional[str] = None,
        data_classification: Optional[str] = None,
        is_fallback: bool = False,
        as_of: Optional[datetime] = None,
    ) -> ModelGuardResult:
        now = as_of or datetime.now(timezone.utc)
        violations: List[str] = []
        obligations: List[Dict[str, Any]] = []

        # 1. Prerequisite: Active USES_MODEL / USES Relationship Check
        rels = RelationshipRepository.find_active(
            db=self.db,
            tenant_id=tenant_id,
            source_type="AGENT",
            source_id=str(agent_id),
            as_of=now,
        )
        has_model_rel = any(
            (r.relationship_type in ["USES_MODEL", "USES"])
            and (r.target_type in ["MODEL", "AI_MODEL"] or r.relationship_type == "USES_MODEL")
            and (r.target_id == str(model_id))
            for r in rels
        )

        if not has_model_rel:
            prefix = "Fallback model" if is_fallback else "Model"
            violations.append(
                f"Relationship prerequisite failed: Agent {agent_id} has no active USES_MODEL link to {prefix.lower()} {model_id}"
            )
            return ModelGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                reason=f"Agent is not authorized to invoke this {prefix.lower()} (no active USES_MODEL relationship)",
                violations=violations,
            )

        # 2. Model Existence & Active Status Check
        model = (
            self.db.query(AIModel)
            .filter(AIModel.id == model_id, AIModel.tenant_id == tenant_id)
            .first()
        )
        if not model or model.status != "ACTIVE":
            violations.append(f"Model {model_id} is inactive or does not exist")
            return ModelGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                reason="Model is inactive or not found",
                violations=violations,
            )

        # 3. Model Version Validation (if specified)
        if requested_version and model.version:
            if requested_version.lower() != model.version.lower():
                violations.append(
                    f"Requested model version '{requested_version}' does not match active approved version '{model.version}'"
                )
                return ModelGuardResult(
                    decision=Decision.DENY,
                    is_permitted=False,
                    model=model,
                    reason=f"Model version mismatch: requested '{requested_version}', approved is '{model.version}'",
                    violations=violations,
                )

        # 4. Deployment Environment Compatibility Check
        req_env = (environment or "PRODUCTION").upper()
        model_env = (model.deployment_environment or "PRODUCTION").upper()

        if req_env == "PRODUCTION" and model_env in ["DEVELOPMENT", "DEV", "STAGING", "TEST"]:
            violations.append(
                f"Environment incompatibility: Cannot invoke {model_env} model '{model.model_name}' in PRODUCTION"
            )
            return ModelGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                model=model,
                reason=f"Development/Staging model '{model.model_name}' is not approved for PRODUCTION runtime",
                violations=violations,
            )

        # 5. Provider & Data Classification Compatibility
        provider = model.provider
        if data_classification:
            data_class_norm = data_classification.upper()
            if data_class_norm in ["RESTRICTED", "CONFIDENTIAL"]:
                if provider:
                    hosting = (provider.hosting_type or "").upper()
                    risk = (provider.risk_classification or "").upper()
                    if hosting == "PUBLIC" or risk in ["HIGH", "UNAPPROVED", "PROHIBITED"]:
                        violations.append(
                            f"Provider restriction: {data_class_norm} data cannot be routed to provider '{provider.provider_name}' (hosting: {hosting}, risk: {risk})"
                        )
                        return ModelGuardResult(
                            decision=Decision.DENY,
                            is_permitted=False,
                            model=model,
                            provider=provider,
                            reason=f"Provider '{provider.provider_name}' is not authorized for {data_class_norm} workloads",
                            violations=violations,
                        )

        # 6. Auditing & Obligation Telemetry
        obligations.append({
            "type": "LOG_MODEL_INVOCATION",
            "model_id": str(model.id),
            "model_code": model.model_code,
            "provider_name": provider.provider_name if provider else None,
            "is_fallback": is_fallback,
        })

        return ModelGuardResult(
            decision=Decision.ALLOW,
            is_permitted=True,
            model=model,
            provider=provider,
            reason=f"Model invocation authorized for '{model.model_name}'",
            obligations=obligations,
        )
