import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DATABASE_URL", "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq")


from sqlalchemy import text
from app.db.session import SessionLocal

def seed_phase4_event_schemas():
    db = SessionLocal()
    try:
        print("[INFO] Seeding Phase 4 Event Schemas into event_schema_registry...")
        
        phase4_events = [
            ("WORKFLOW_RUN_STARTED", "Workflow"),
            ("WORKFLOW_RUN_COMPLETED", "Workflow"),
            ("WORKFLOW_RUN_FAILED", "Workflow"),
            ("POLICY_EVALUATED", "Policy"),
            ("POLICY_TRIGGERED", "Policy"),
            ("RELATIONSHIP_CREATED", "Relationship"),
            ("OWNERSHIP_TRANSFERRED", "Relationship"),
            ("AGENT_STEP_STARTED", "Agent"),
            ("BOUNDARY_CHECK_EXECUTED", "Boundary"),
            ("BOUNDARY_BREACH_ATTEMPTED", "Violation"),
            ("UNAUTHORIZED_ACCESS_BLOCKED", "Violation"),
            ("APPROVAL_REQUESTED", "Approval"),
            ("APPROVAL_GRANTED", "Approval"),
            ("USER_LOGIN", "Identity"),
            ("AUTH_LOGIN_SUCCESS", "Identity"),
            ("ROLE_ASSIGNED", "Identity"),
            ("MODEL_REGISTERED", "Registry"),
            ("AUDIT_EXPORT_GENERATED", "Audit"),
        ]

        for event_type, category in phase4_events:
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

        db.commit()
        print("[SUCCESS] Phase 4 Event Schemas successfully registered!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to seed Phase 4 schemas: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_phase4_event_schemas()
