import logging
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal
from app.modules.registry.constants import DataClassification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EVENT_CATALOGUE = [
    # Identity
    ("USER_LOGIN", "Identity"),
    ("USER_LOGOUT", "Identity"),
    ("ROLE_ASSIGNED", "Identity"),
    ("PERMISSION_REVOKED", "Identity"),
    # Registry
    ("MODEL_REGISTERED", "Registry"),
    ("MODEL_UPDATED", "Registry"),
    ("AGENT_REGISTERED", "Registry"),
    ("AGENT_UPDATED", "Registry"),
    # Relationship
    ("RELATIONSHIP_CREATED", "Relationship"),
    ("RELATIONSHIP_DELETED", "Relationship"),
    ("OWNERSHIP_TRANSFERRED", "Relationship"),
    # Workflow
    ("WORKFLOW_CREATED", "Workflow"),
    ("WORKFLOW_SCHEDULED", "Workflow"),
    ("WORKFLOW_RUN_STARTED", "Workflow"),
    ("WORKFLOW_RUN_COMPLETED", "Workflow"),
    ("WORKFLOW_RUN_FAILED", "Workflow"),
    # Policy
    ("POLICY_CREATED", "Policy"),
    ("POLICY_UPDATED", "Policy"),
    ("POLICY_EVALUATED", "Policy"),
    ("POLICY_TRIGGERED", "Policy"),
    ("POLICY_VIOLATED", "Policy"),
    # Approval
    ("APPROVAL_REQUESTED", "Approval"),
    ("APPROVAL_GRANTED", "Approval"),
    ("APPROVAL_REJECTED", "Approval"),
    # Agent
    ("AGENT_STEP_STARTED", "Agent"),
    ("AGENT_STEP_COMPLETED", "Agent"),
    ("AGENT_TOOL_CALLED", "Agent"),
    # Audit
    ("AUDIT_TIMELINE_QUERIED", "Audit"),
    ("AUDIT_EXPORT_GENERATED", "Audit"),
    ("DEAD_LETTER_EVENT_RETRIED", "Audit"),
    # Violation
    ("BOUNDARY_BREACH_ATTEMPTED", "Violation"),
    ("UNAUTHORIZED_ACCESS_BLOCKED", "Violation"),
]

CATEGORY_CLASSIFICATIONS = {
    "Identity": DataClassification.CONFIDENTIAL.value,
    "Registry": DataClassification.INTERNAL.value,
    "Relationship": DataClassification.INTERNAL.value,
    "Workflow": DataClassification.INTERNAL.value,
    "Policy": DataClassification.CONFIDENTIAL.value,
    "Approval": DataClassification.CONFIDENTIAL.value,
    "Agent": DataClassification.INTERNAL.value,
    "Audit": DataClassification.RESTRICTED.value,
    "Violation": DataClassification.RESTRICTED.value,
}

def seed_phase4_reference_data():
    db: Session = SessionLocal()
    try:
        logger.info("Seeding Phase 4 Event Schema Registry...")
        for event_type, category in EVENT_CATALOGUE:
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

        logger.info("Successfully seeded event_schema_registry with 30 MVP event types.")

        # Get default user for tenant_id in retention rules
        user_res = db.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        if user_res:
            tenant_id = str(user_res[0])
            logger.info(f"Seeding retention rules for tenant {tenant_id}...")
            
            for category, classification in CATEGORY_CLASSIFICATIONS.items():
                retention_days = 90
                action = "PURGE"
                if classification == DataClassification.INTERNAL.value:
                    retention_days = 365
                elif classification == DataClassification.CONFIDENTIAL.value:
                    retention_days = 1825
                    action = "ARCHIVE_BLOB"
                elif classification == DataClassification.RESTRICTED.value:
                    retention_days = 2555
                    action = "ARCHIVE_BLOB"

                db.execute(text("""
                    INSERT INTO event_retention_rules (id, tenant_id, event_category, retention_days, action, created_at)
                    VALUES (gen_random_uuid(), CAST(:tenant_id AS uuid), :event_category, :retention_days, :action, CURRENT_TIMESTAMP)
                    ON CONFLICT (tenant_id, event_category) DO UPDATE
                    SET retention_days = EXCLUDED.retention_days, action = EXCLUDED.action;
                """), {
                    "tenant_id": tenant_id,
                    "event_category": category,
                    "retention_days": retention_days,
                    "action": action
                })
            logger.info("Successfully seeded event_retention_rules.")
        else:
            logger.warning("No default user found in `users` table; skipped tenant retention rule seeding.")

        db.commit()
        logger.info("Phase 4 reference data seeding complete!")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding Phase 4 reference data: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_phase4_reference_data()
