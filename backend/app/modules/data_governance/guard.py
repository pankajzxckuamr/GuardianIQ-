import re
import hashlib
from typing import Dict, Any, Optional, List, Union
from uuid import UUID
from datetime import datetime, timezone
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.modules.datasource.models import DataSource
from app.modules.agent_boundary.models import DataSourceField, AgentDataPermission
from app.modules.relationship.repository import RelationshipRepository
from app.modules.data_governance.repository import DataGovernanceRepository
from app.modules.policy_engine.enums import Decision, DataClassification, SensitivityLevel, DataOperation


CLASSIFICATION_RANK = {
    "PUBLIC": 1,
    "INTERNAL": 2,
    "CONFIDENTIAL": 3,
    "RESTRICTED": 4,
}

SENSITIVITY_RANK = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


class DataTransformer:
    """
    Enterprise Data Transformation Pipeline.
    Executes MASK, REDACT, TOKENIZE, and HASH transformations on structured records
    before model or tool exposure.
    """

    @classmethod
    def transform_value(cls, val: Any, strategy: Optional[str]) -> Any:
        if val is None or not strategy:
            return val

        strategy = strategy.upper()
        s_val = str(val)

        if strategy == "REDACT":
            return "[REDACTED]"

        elif strategy == "HASH":
            return hashlib.sha256(s_val.encode("utf-8")).hexdigest()

        elif strategy == "TOKENIZE":
            token_suffix = hashlib.sha256(s_val.encode("utf-8")).hexdigest()[:12]
            return f"tok_{token_suffix}"

        elif strategy == "MASK":
            # 1. Email pattern
            if "@" in s_val:
                parts = s_val.split("@")
                user, domain = parts[0], "@".join(parts[1:])
                if len(user) <= 1:
                    masked_user = "*"
                else:
                    masked_user = user[0] + "***"
                return f"{masked_user}@{domain}"

            # 2. Numeric / Phone / SSN / Card digits
            digits = re.sub(r"\D", "", s_val)
            if len(digits) >= 10:
                last4 = digits[-4:]
                return f"***-***-{last4}"

            # 3. Generic String
            if len(s_val) > 4:
                return s_val[:2] + "***" + s_val[-2:]
            return "***"

        return val

    @classmethod
    def transform_record(
        cls,
        record: Dict[str, Any],
        field_strategies: Dict[str, str],
        allowed_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Transforms a single record: strips denied fields and applies masking strategies."""
        transformed = {}
        for k, v in record.items():
            if allowed_fields is not None and k not in allowed_fields:
                continue  # Denied field stripped

            strategy = field_strategies.get(k)
            if strategy:
                transformed[k] = cls.transform_value(v, strategy)
            else:
                transformed[k] = v
        return transformed

    @classmethod
    def transform_dataset(
        cls,
        records: List[Dict[str, Any]],
        field_strategies: Dict[str, str],
        allowed_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Transforms a list of records."""
        return [cls.transform_record(r, field_strategies, allowed_fields) for r in records]


@dataclass
class DataGuardResult:
    decision: Decision
    is_permitted: bool
    allowed_fields: List[str] = field(default_factory=list)
    denied_fields: List[str] = field(default_factory=list)
    transformation_map: Dict[str, str] = field(default_factory=dict)
    transformed_data: Optional[List[Dict[str, Any]]] = None
    reason: Optional[str] = None
    violations: List[str] = field(default_factory=list)
    obligations: List[Dict[str, Any]] = field(default_factory=list)


class DataPermissionGuard:
    """
    Enterprise Data Permission Guard.
    Enforces active USES_DATA_SOURCE relationship, operation validity,
    classification & sensitivity ceilings, denied field stripping,
    and field-level data transformations.
    """

    def __init__(self, db: Session):
        self.db = db

    def evaluate_data_access(
        self,
        tenant_id: UUID,
        agent_id: UUID,
        data_source_id: UUID,
        operation: str = "READ",
        requested_fields: Optional[List[str]] = None,
        records: Optional[List[Dict[str, Any]]] = None,
        record_count: Optional[int] = None,
        as_of: Optional[datetime] = None,
    ) -> DataGuardResult:
        now = as_of or datetime.now(timezone.utc)
        violations: List[str] = []
        obligations: List[Dict[str, Any]] = []

        # 1. Prerequisite: Active USES_DATA_SOURCE / USES Relationship Check
        rels = RelationshipRepository.find_active(
            db=self.db,
            tenant_id=tenant_id,
            source_type="AGENT",
            source_id=str(agent_id),
            as_of=now,
        )
        has_ds_rel = any(
            (r.relationship_type in ["USES_DATA_SOURCE", "USES"])
            and (r.target_type in ["DATA_SOURCE", "DATASOURCE"] or r.relationship_type == "USES_DATA_SOURCE")
            and (r.target_id == str(data_source_id))
            for r in rels
        )

        if not has_ds_rel:
            violations.append(
                f"Relationship prerequisite failed: Agent {agent_id} has no active USES_DATA_SOURCE link to data source {data_source_id}"
            )
            return DataGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                reason="Agent is not authorized to access this data source (no active relationship)",
                violations=violations,
            )

        # 2. Data Source Existence & Active Check
        ds = self.db.query(DataSource).filter(DataSource.id == data_source_id, DataSource.tenant_id == tenant_id).first()
        if not ds or ds.status != "ACTIVE":
            violations.append(f"Data source {data_source_id} is inactive or does not exist")
            return DataGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                reason="Data source is inactive or not found",
                violations=violations,
            )

        # 3. Agent Data Permission Resolution
        perms = DataGovernanceRepository.list_permissions_by_agent(self.db, agent_id, tenant_id)
        matching_perm: Optional[AgentDataPermission] = None
        for p in perms:
            if p.data_source_id == data_source_id:
                matching_perm = p
                break

        # Max classification & sensitivity ceilings allowed for this agent
        agent_max_class = "CONFIDENTIAL"
        agent_max_sens = "HIGH"
        allowed_ops = ["READ"]

        if matching_perm:
            if not matching_perm.is_active:
                violations.append("Agent data permission for this data source is INACTIVE")
                return DataGuardResult(
                    decision=Decision.DENY,
                    is_permitted=False,
                    reason="Agent data permission is revoked",
                    violations=violations,
                )
            agent_max_class = matching_perm.max_classification or "CONFIDENTIAL"
            agent_max_sens = matching_perm.max_sensitivity or "HIGH"
            allowed_ops = matching_perm.allowed_operations_json or ["READ"]

        # Validate Operation
        op_norm = operation.upper()
        if op_norm not in [o.upper() for o in allowed_ops] and "*" not in allowed_ops:
            violations.append(f"Operation '{operation}' is not in allowed data operations: {allowed_ops}")
            return DataGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                reason=f"Operation '{operation}' is not permitted on this data source",
                violations=violations,
            )

        # 4. Check Data Source Table-Level Classification Ceiling
        ds_class = (ds.classification or "INTERNAL").upper()
        ds_sens = (ds.sensitivity_level or "MEDIUM").upper()

        if CLASSIFICATION_RANK.get(ds_class, 2) > CLASSIFICATION_RANK.get(agent_max_class.upper(), 3):
            violations.append(
                f"Classification ceiling exceeded: Data source is '{ds_class}', but agent max classification is '{agent_max_class}'"
            )
            return DataGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                reason="Data source classification exceeds agent clearance",
                violations=violations,
            )

        # 5. Field-Level Classification, Sensitivity & Masking Strategies
        all_fields = DataGovernanceRepository.list_fields_by_data_source(self.db, data_source_id, tenant_id)
        fields_map: Dict[str, DataSourceField] = {f.field_name.lower(): f for f in all_fields}

        # Resolve requested fields
        if requested_fields is None:
            if records and len(records) > 0:
                fields_to_check = list(records[0].keys())
            else:
                fields_to_check = [f.field_name for f in all_fields]
        else:
            fields_to_check = requested_fields

        allowed_fields: List[str] = []
        denied_fields: List[str] = []
        transformation_map: Dict[str, str] = {}

        for f_name in fields_to_check:
            f_obj = fields_map.get(f_name.lower())
            if not f_obj:
                # Default allow unclassified fields if within DS classification
                allowed_fields.append(f_name)
                continue

            f_class = (f_obj.classification or "INTERNAL").upper()
            f_sens = (f_obj.sensitivity_level or "MEDIUM").upper()

            # Check field classification ceiling
            if CLASSIFICATION_RANK.get(f_class, 2) > CLASSIFICATION_RANK.get(agent_max_class.upper(), 3):
                denied_fields.append(f_name)
                violations.append(
                    f"Field '{f_name}' ({f_class}) exceeds agent classification ceiling ({agent_max_class})"
                )
            elif SENSITIVITY_RANK.get(f_sens, 2) > SENSITIVITY_RANK.get(agent_max_sens.upper(), 3):
                denied_fields.append(f_name)
                violations.append(
                    f"Field '{f_name}' ({f_sens}) exceeds agent sensitivity ceiling ({agent_max_sens})"
                )
            else:
                allowed_fields.append(f_name)
                if f_obj.masking_strategy:
                    transformation_map[f_name] = f_obj.masking_strategy
                    obligations.append({
                        "type": "TRANSFORM_FIELD",
                        "field": f_name,
                        "strategy": f_obj.masking_strategy,
                    })

        # 6. Enforce Bulk Record / Export Limit
        count_to_check = record_count or (len(records) if records is not None else 0)
        if op_norm == "EXPORT" and count_to_check > 5000:
            violations.append(f"Export record count ({count_to_check}) exceeds maximum allowed limit (5000)")
            return DataGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                reason="Bulk export record limit exceeded",
                violations=violations,
            )

        # 7. Apply Data Transformations to Records if provided
        transformed_records = None
        if records is not None:
            transformed_records = DataTransformer.transform_dataset(
                records=records,
                field_strategies=transformation_map,
                allowed_fields=allowed_fields,
            )

        # If any requested fields were explicitly denied
        if requested_fields and any(f in denied_fields for f in requested_fields):
            return DataGuardResult(
                decision=Decision.DENY,
                is_permitted=False,
                allowed_fields=allowed_fields,
                denied_fields=denied_fields,
                transformation_map=transformation_map,
                transformed_data=transformed_records,
                reason=f"Access denied to {len(denied_fields)} classified field(s): {', '.join(denied_fields)}",
                violations=violations,
            )

        decision = Decision.ALLOW_WITH_OBLIGATIONS if transformation_map else Decision.ALLOW
        reason = (
            f"Data access permitted with {len(transformation_map)} field transformation(s)"
            if transformation_map
            else "Data access permitted"
        )

        return DataGuardResult(
            decision=decision,
            is_permitted=True,
            allowed_fields=allowed_fields,
            denied_fields=denied_fields,
            transformation_map=transformation_map,
            transformed_data=transformed_records,
            reason=reason,
            obligations=obligations,
        )
