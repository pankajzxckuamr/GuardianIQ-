import uuid
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.modules.relationship.schemas import GenericRelationshipCreate, GenericRelationshipUpdate
from app.modules.relationship.models import RelationshipValidationResult
from app.modules.relationship.repository import RelationshipRepository, ResponsibilityRepository
from app.modules.relationship.lifecycle import validate_transition
from app.modules.relationship.constants import ValidationRuleCategory, RelationshipType

def make_serializable(data):
    if isinstance(data, dict):
        return {str(k): make_serializable(v) for k, v in data.items() if not str(k).startswith('_')}
    elif isinstance(data, list):
        return [make_serializable(v) for v in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, uuid.UUID):
        return str(data)
    try:
        import json
        json.dumps(data)
        return data
    except TypeError:
        return str(data)


class ValidationResult:
    def __init__(self, rule_id: str, status: str, message: str, severity: str = "ERROR", resolution_hint: Optional[str] = None):
        self.rule_id = rule_id
        self.status = status
        self.message = message
        self.severity = severity
        self.resolution_hint = resolution_hint

class ValidationEngine:
    def __init__(self, db: Session, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _check_entity_exists(self, entity_type: str, entity_id: str) -> bool:
        normalized = entity_type.lower() if entity_type else ""
        if normalized in {"model", "ai_model", "ai_models"}:
            entity_type = "ai_models"
        elif normalized in {"agent", "ai_agent", "agents"}:
            entity_type = "agents"
        elif normalized in {"tool", "tools"}:
            entity_type = "tools"
        elif normalized in {"workflow", "workflows"}:
            entity_type = "workflows"
        elif normalized in {"datasource", "data_source", "data_sources"}:
            entity_type = "data_sources"
        elif normalized in {"department", "departments"}:
            entity_type = "departments"
        elif normalized in {"user", "users"}:
            entity_type = "users"
        elif normalized in {"role", "roles"}:
            entity_type = "roles"

        valid_tables = {"ai_models", "agents", "tools", "workflows", "data_sources", "departments", "users", "roles"}
        if entity_type not in valid_tables:
            return False
            
        sql = f"SELECT 1 FROM {entity_type} WHERE id = :id"
        params = {"id": entity_id}
        
        # Check tenant_id mapping
        if entity_type not in {"users", "roles"}:
            sql += " AND tenant_id = :tenant_id"
            params["tenant_id"] = self.tenant_id
            
        # Check status mapping
        if entity_type != "roles":
            sql += " AND status != 'ARCHIVED'"
            
        stmt = text(sql)
        res = self.db.execute(stmt, params).scalar()
        return bool(res)

    def validate_payload(self, request_id: str, payload: dict, is_update: bool = False, current_status: Optional[str] = None) -> List[ValidationResult]:
        results = []
        
        # Rule 1: Source object exists
        source_type = payload.get("source_type")
        source_id = payload.get("source_id")
        if not self._check_entity_exists(source_type, source_id):
            results.append(ValidationResult(
                rule_id=f"{ValidationRuleCategory.GRAPH_INTEGRITY.value}-001",
                status="FAIL",
                message=f"Source object {source_type}/{source_id} does not exist or is not active in this tenant.",
                severity="ERROR"
            ))
            
        # Rule 2: Target object exists
        target_type = payload.get("target_type")
        target_id = payload.get("target_id")
        if not self._check_entity_exists(target_type, target_id):
            results.append(ValidationResult(
                rule_id=f"{ValidationRuleCategory.GRAPH_INTEGRITY.value}-002",
                status="FAIL",
                message=f"Target object {target_type}/{target_id} does not exist or is not active in this tenant.",
                severity="ERROR"
            ))
            
        # Rule 3: Tenant match (Implicitly handled by _check_entity_exists and repo filtering)
        # Rule 4: No duplicate active relationship (if create)
        if not is_update:
            existing = RelationshipRepository.find_targets(
                self.db, self.tenant_id, source_type, source_id, payload.get("relationship_type"), scope=payload.get("relationship_scope")
            )
            for rel in existing:
                if rel.target_type == target_type and rel.target_id == target_id:
                    results.append(ValidationResult(
                        rule_id=f"{ValidationRuleCategory.DUPLICATE.value}-001",
                        status="FAIL",
                        message="A duplicate active relationship already exists.",
                        severity="ERROR"
                    ))
                    break
                    
        # Rule 5: effective_to > effective_from
        eff_from = payload.get("effective_from")
        eff_to = payload.get("effective_to")
        if eff_from and eff_to and eff_to <= eff_from:
            results.append(ValidationResult(
                rule_id=f"{ValidationRuleCategory.TEMPORAL.value}-001",
                status="FAIL",
                message="effective_to must be strictly greater than effective_from.",
                severity="ERROR"
            ))
            
        # Rule 6: Valid status transition
        if is_update and current_status:
            req_status = payload.get("status")
            if req_status and req_status != current_status:
                valid, msg = validate_transition(current_status, req_status)
                if not valid:
                    results.append(ValidationResult(
                        rule_id=f"{ValidationRuleCategory.LIFECYCLE.value}-001",
                        status="FAIL",
                        message=msg,
                        severity="ERROR"
                    ))
                    
        # Rule 7: OWNED_BY requires target to have an active owner
        if payload.get("relationship_type") == RelationshipType.OWNED_BY.value:
            owner = ResponsibilityRepository.find_primary_owner(self.db, self.tenant_id, target_type, target_id)
            if not owner:
                results.append(ValidationResult(
                    rule_id=f"{ValidationRuleCategory.OWNERSHIP.value}-001",
                    status="FAIL",
                    message=f"Target object {target_type}/{target_id} does not have an active primary owner.",
                    severity="ERROR",
                    resolution_hint="Assign an owner to the target object first."
                ))
                
        # Persist failures
        for r in results:
            if r.status == "FAIL":
                val_res = RelationshipValidationResult(
                    id=uuid.uuid4(),
                    tenant_id=self.tenant_id,
                    request_id=request_id,
                    relationship_id=payload.get("id") if is_update else None,
                    validation_rule_id=r.rule_id,
                    validation_status=r.status,
                    severity=r.severity,
                    message=r.message,
                    resolution_hint=r.resolution_hint,
                    payload_json=make_serializable(payload)
                )
                self.db.add(val_res)
                
        self.db.flush()
        return results

