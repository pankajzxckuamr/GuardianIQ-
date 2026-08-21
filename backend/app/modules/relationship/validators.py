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
        from app.modules.relationship.constants import canonicalize_entity_type, table_for_entity_type
        table_name = table_for_entity_type(entity_type)

        valid_tables = {"ai_models", "agents", "tools", "workflows", "data_sources", "departments", "users", "roles"}
        if table_name not in valid_tables:
            return False
            
        sql = f"SELECT 1 FROM {table_name} WHERE id = :id"
        params = {"id": str(entity_id)}
        
        # Check tenant_id mapping
        if table_name not in {"users", "roles"}:
            sql += " AND tenant_id = :tenant_id"
            params["tenant_id"] = self.tenant_id
            
        # Check status mapping
        if table_name != "roles":
            sql += " AND status != 'ARCHIVED'"
            
        stmt = text(sql)
        res = self.db.execute(stmt, params).scalar()
        return bool(res)

    def _get_object_risk(self, entity_type: str, entity_id: str) -> str:
        from app.modules.relationship.constants import canonicalize_entity_type, table_for_entity_type
        c_type = canonicalize_entity_type(entity_type)
        table_name = table_for_entity_type(entity_type)
        
        column_map = {
            "MODEL": "risk_level",
            "AGENT": "risk_level",
            "TOOL": "sensitivity_level",
            "WORKFLOW": "business_criticality",
            "DATA_SOURCE": "sensitivity_level"
        }
        column_name = column_map.get(c_type)
        if not column_name:
            return "LOW"

        sql = f"SELECT {column_name} FROM {table_name} WHERE id = :id AND tenant_id = :tenant_id"
        try:
            res = self.db.execute(text(sql), {"id": str(entity_id), "tenant_id": self.tenant_id}).scalar()
            return str(res).upper() if res else "LOW"
        except Exception:
            return "LOW"

    def _has_owner_and_approver(self, object_type: str, object_id: str) -> bool:
        from app.modules.relationship.constants import canonicalize_entity_type
        c_type = canonicalize_entity_type(object_type)
        # Check OWNER
        sql_owner = """
            SELECT 1 FROM object_responsibilities 
            WHERE tenant_id = :tenant_id 
              AND (object_type = :c_type OR lower(object_type) = :lower_type)
              AND object_id = :object_id 
              AND responsibility_type = 'OWNER' 
              AND status = 'ACTIVE'
        """
        has_owner = bool(self.db.execute(text(sql_owner), {
            "tenant_id": self.tenant_id,
            "c_type": c_type,
            "lower_type": object_type.lower(),
            "object_id": str(object_id)
        }).scalar())

        # Check APPROVER
        sql_approver = """
            SELECT 1 FROM object_responsibilities 
            WHERE tenant_id = :tenant_id 
              AND (object_type = :c_type OR lower(object_type) = :lower_type)
              AND object_id = :object_id 
              AND responsibility_type = 'APPROVER' 
              AND status = 'ACTIVE'
        """
        has_approver = bool(self.db.execute(text(sql_approver), {
            "tenant_id": self.tenant_id,
            "c_type": c_type,
            "lower_type": object_type.lower(),
            "object_id": str(object_id)
        }).scalar())

        return has_owner and has_approver

    def _check_circular_ownership(self, source_type: str, source_id: str, target_type: str, target_id: str) -> bool:
        visited = set()
        to_visit = [(target_type, target_id)]

        while to_visit:
            curr_type, curr_id = to_visit.pop(0)
            if (curr_type, curr_id) in visited:
                continue
            visited.add((curr_type, curr_id))

            if curr_type == source_type and str(curr_id) == str(source_id):
                return True

            sql = """
                SELECT target_type, target_id FROM generic_relationships 
                WHERE tenant_id = :tenant_id 
                  AND source_type = :source_type 
                  AND source_id = :source_id 
                  AND relationship_type = 'OWNED_BY' 
                  AND status = 'ACTIVE'
            """
            try:
                res = self.db.execute(text(sql), {
                    "tenant_id": self.tenant_id,
                    "source_type": curr_type,
                    "source_id": curr_id
                }).all()
                for row in res:
                    to_visit.append((row[0], row[1]))
            except Exception:
                pass
        return False

    def _check_cross_tenant(self, entity_type: str, entity_id: str) -> bool:
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
        else:
            return False

        sql = f"SELECT tenant_id FROM {entity_type} WHERE id = :id"
        try:
            res = self.db.execute(text(sql), {"id": entity_id}).scalar()
            if res and str(res) != str(self.tenant_id):
                return True
        except Exception:
            pass
        return False

    def validate_payload(self, request_id: str, payload: dict, is_update: bool = False, current_status: Optional[str] = None) -> List[ValidationResult]:
        from app.modules.relationship.constants import canonicalize_entity_type, canonicalize_rel_type
        results = []
        source_type = canonicalize_entity_type(payload.get("source_type"))
        source_id = str(payload.get("source_id"))
        target_type = canonicalize_entity_type(payload.get("target_type"))
        target_id = str(payload.get("target_id"))
        relationship_type = canonicalize_rel_type(payload.get("relationship_type"))
        status = payload.get("status", "PROPOSED")

        # Rule: REL-VAL-032 - Cross-tenant relationship is blocked
        if self._check_cross_tenant(source_type, source_id) or self._check_cross_tenant(target_type, target_id):
            results.append(ValidationResult(
                rule_id="REL-VAL-032",
                status="FAIL",
                message="Cross-tenant relationship is blocked.",
                severity="ERROR"
            ))

        # Rule: REL-VAL-031 - Orphan relationship target/source must be blocked
        if not self._check_entity_exists(source_type, source_id):
            results.append(ValidationResult(
                rule_id="REL-VAL-031",
                status="FAIL",
                message=f"Source object {source_type}/{source_id} does not exist or is not active in this tenant.",
                severity="ERROR"
            ))
            
        if not self._check_entity_exists(target_type, target_id):
            results.append(ValidationResult(
                rule_id="REL-VAL-031",
                status="FAIL",
                message=f"Target object {target_type}/{target_id} does not exist or is not active in this tenant.",
                severity="ERROR"
            ))

        # Rule: REL-VAL-006 - No duplicate active relationship
        if not is_update:
            existing = RelationshipRepository.find_targets(
                self.db, self.tenant_id, source_type, source_id, relationship_type, scope=payload.get("relationship_scope")
            )
            for rel in existing:
                if canonicalize_entity_type(rel.target_type) == target_type and str(rel.target_id) == target_id:
                    results.append(ValidationResult(
                        rule_id="REL-VAL-006",
                        status="FAIL",
                        message="A duplicate active relationship already exists.",
                        severity="ERROR"
                    ))
                    break
                    
        # Rule: REL-VAL-009 - effective_to > effective_from
        eff_from = payload.get("effective_from")
        eff_to = payload.get("effective_to")
        # Ensure we parse strings to datetime if needed
        if isinstance(eff_from, str):
            try: eff_from = datetime.fromisoformat(eff_from.replace("Z", "+00:00"))
            except Exception: pass
        if isinstance(eff_to, str):
            try: eff_to = datetime.fromisoformat(eff_to.replace("Z", "+00:00"))
            except Exception: pass

        if eff_from and eff_to and eff_to <= eff_from:
            results.append(ValidationResult(
                rule_id="REL-VAL-009",
                status="FAIL",
                message="effective_to must be strictly greater than effective_from.",
                severity="ERROR"
            ))
            
        # Rule: REL-VAL-011 - Future-dated relationship cannot be used until effective_from
        if status == "ACTIVE" and eff_from:
            curr_time = datetime.now(timezone.utc) if eff_from.tzinfo else datetime.utcnow()
            if eff_from > curr_time:
                results.append(ValidationResult(
                    rule_id="REL-VAL-011",
                    status="FAIL",
                    message="Future-dated relationship cannot be activated until effective_from.",
                    severity="ERROR"
                ))

        # Rule: REL-VAL-027 - Valid status transition
        if is_update and current_status:
            req_status = payload.get("status")
            if req_status and req_status != current_status:
                valid, msg = validate_transition(current_status, req_status)
                if not valid:
                    results.append(ValidationResult(
                        rule_id="REL-VAL-027",
                        status="FAIL",
                        message=msg,
                        severity="ERROR"
                    ))
                    
        # Rule: REL-VAL-001 / REL-VAL-005 - OWNED_BY requires target to have an active owner
        if relationship_type == RelationshipType.OWNED_BY.value:
            owner = ResponsibilityRepository.find_primary_owner(self.db, self.tenant_id, target_type, target_id)
            if not owner:
                results.append(ValidationResult(
                    rule_id="REL-VAL-001",
                    status="FAIL",
                    message=f"Target object {target_type}/{target_id} does not have an active primary owner.",
                    severity="ERROR",
                    resolution_hint="Assign an owner to the target object first."
                ))

        # Rule: REL-VAL-002 - High-risk object must have OWNER and APPROVER
        source_risk = self._get_object_risk(source_type, source_id)
        target_risk = self._get_object_risk(target_type, target_id)
        if source_risk in {"HIGH", "CRITICAL", "CONFIDENTIAL", "RESTRICTED"}:
            if not self._has_owner_and_approver(source_type, source_id):
                results.append(ValidationResult(
                    rule_id="REL-VAL-002",
                    status="FAIL",
                    message=f"High-risk source object {source_type}/{source_id} must have both an OWNER and an APPROVER assigned.",
                    severity="ERROR",
                    resolution_hint="Assign an owner and an approver to the source object first."
                ))
        if target_risk in {"HIGH", "CRITICAL", "CONFIDENTIAL", "RESTRICTED"}:
            if not self._has_owner_and_approver(target_type, target_id):
                results.append(ValidationResult(
                    rule_id="REL-VAL-002",
                    status="FAIL",
                    message=f"High-risk target object {target_type}/{target_id} must have both an OWNER and an APPROVER assigned.",
                    severity="ERROR",
                    resolution_hint="Assign an owner and an approver to the target object first."
                ))

        # Rule: REL-VAL-017 - Agent cannot use tool without active USES_TOOL
        normalized_source = source_type.lower() if source_type else ""
        normalized_target = target_type.lower() if target_type else ""
        rel_type_upper = (relationship_type or "").upper()
        if normalized_source in {"agent", "ai_agent", "agents"} and normalized_target in {"tool", "tools"}:
            if rel_type_upper not in {"USES_TOOL", "USES"}:
                results.append(ValidationResult(
                    rule_id="REL-VAL-017",
                    status="FAIL",
                    message="AI Agent to Tool relationship must be of type USES_TOOL.",
                    severity="ERROR"
                ))

        # Rule: REL-VAL-030 - Circular ownership must be blocked
        if relationship_type == "OWNED_BY":
            if self._check_circular_ownership(source_type, source_id, target_type, target_id):
                results.append(ValidationResult(
                    rule_id="REL-VAL-030",
                    status="FAIL",
                    message="Circular ownership detected and blocked.",
                    severity="ERROR"
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

