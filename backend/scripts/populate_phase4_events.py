import os
import sys
import uuid
import json
import logging
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DATABASE_URL", "postgresql://guardianiq_user:guardianiq123@localhost:5432/guardianiq")
os.environ.setdefault("SECRET_KEY", "secretkey123")

from sqlalchemy import text
from app.db.session import SessionLocal
from app.modules.events.models import GovernanceEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_payload(data_dict):
    import hashlib
    json_str = json.dumps(data_dict, sort_keys=True)
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

def populate_events():
    db = SessionLocal()
    try:
        # Get active user for tenant_id
        user = db.execute(text("SELECT id FROM users LIMIT 1")).fetchone()
        if not user:
            logger.error("No user found in database. Seed user first.")
            return
        
        tenant_id = user[0]
        logger.info(f"Populating governance events for tenant {tenant_id}...")

        # Clear existing events for clean testing if desired, or append
        now = datetime.now(timezone.utc)

        # Primary Correlation ID 1 (Matches user screenshot: 5c3c5751-3232-4a3f-85ec-247d55077c03)
        corr_id_1 = uuid.UUID("5c3c5751-3232-4a3f-85ec-247d55077c03")
        # Target Agent ID (Matches user screenshot: d6a3cb9e-11a8-4004-b82f-a38e33790df0)
        agent_id_1 = "d6a3cb9e-11a8-4004-b82f-a38e33790df0"
        
        # Primary Correlation ID 2 (High Risk Breach Trace)
        corr_id_2 = uuid.UUID("a1b2c3d4-e5f6-4789-8012-3456789abcde")
        agent_id_2 = "agent_sec_auditor"

        # Primary Correlation ID 3 (Identity & Approval Governance Trace)
        corr_id_3 = uuid.UUID("b2c3d4e5-f6a7-4890-9123-456789abcdef")
        model_id_1 = "mdl_gpt4_gov"

        events_to_create = []

        # =========================================================================
        # STREAM 1: Governed Agent Execution (Correlation: 5c3c5751-3232-4a3f-85ec-247d55077c03)
        # Subject: agents : d6a3cb9e-11a8-4004-b82f-a38e33790df0 (7 Sequential Steps)
        # =========================================================================
        c1_steps = [
            {
                "type": "WORKFLOW_RUN_STARTED",
                "category": "Workflow",
                "classification": "INTERNAL",
                "service": "workflow_scheduler",
                "subject": {"entity_type": "agents", "entity_id": agent_id_1},
                "risk": {"risk_level": "LOW", "risk_score": 10},
                "policy": {"rules_evaluated": ["SCHEDULE_ACTIVE", "TENANT_VALID"]},
                "payload": {"action": "RUN_INITIATED", "run_code": "RUN-2026-0801", "execution_mode": "GOVERNED"},
                "delay": 0
            },
            {
                "type": "POLICY_EVALUATED",
                "category": "Policy",
                "classification": "CONFIDENTIAL",
                "service": "policy_engine",
                "subject": {"entity_type": "policies", "entity_id": "pol_strict_data"},
                "risk": {"risk_level": "LOW", "risk_score": 15},
                "policy": {"compliance_check": "PASSED", "rules_matched": 3},
                "payload": {"policy_code": "POL-DATA-PRIVACY", "status": "APPROVED", "evaluated_by": "abac_service"},
                "delay": 120
            },
            {
                "type": "RELATIONSHIP_CREATED",
                "category": "Relationship",
                "classification": "INTERNAL",
                "service": "relationship_service",
                "subject": {"entity_type": "agents", "entity_id": agent_id_1},
                "risk": {"risk_level": "LOW", "risk_score": 5},
                "policy": {"binding_id": "pb_agent_model_01"},
                "payload": {"relationship_type": "USES_MODEL", "target_type": "ai_models", "target_id": "mdl_gpt4_gov"},
                "delay": 240
            },
            {
                "type": "AGENT_STEP_STARTED",
                "category": "Agent",
                "classification": "INTERNAL",
                "service": "agent_runtime",
                "subject": {"entity_type": "agents", "entity_id": agent_id_1},
                "risk": {"risk_level": "LOW", "risk_score": 20},
                "policy": {"agent_mode": "SIMULATION"},
                "payload": {"step_number": 1, "step_name": "DATA_INGEST", "input_tokens": 450},
                "delay": 360
            },
            {
                "type": "BOUNDARY_CHECK_EXECUTED",
                "category": "Boundary",
                "classification": "RESTRICTED",
                "service": "boundary_checker",
                "subject": {"entity_type": "agents", "entity_id": agent_id_1},
                "risk": {"risk_level": "MEDIUM", "risk_score": 35},
                "policy": {"max_output_tokens": 4096, "tool_quota": "UNLIMITED"},
                "payload": {"boundary_result": "ALLOWED", "risk_threshold": 80, "current_score": 35},
                "delay": 480
            },
            {
                "type": "APPROVAL_GRANTED",
                "category": "Approval",
                "classification": "CONFIDENTIAL",
                "service": "approval_engine",
                "subject": {"entity_type": "agents", "entity_id": agent_id_1},
                "risk": {"risk_level": "LOW", "risk_score": 10},
                "policy": {"approver_role": "COMPLIANCE_OFFICER"},
                "payload": {"approval_id": "appr_99881", "decision": "APPROVED", "approver": "sarah_j@guardianiq.demo"},
                "delay": 600
            },
            {
                "type": "WORKFLOW_RUN_COMPLETED",
                "category": "Workflow",
                "classification": "INTERNAL",
                "service": "workflow_execution",
                "subject": {"entity_type": "workflows", "entity_id": "wf_98765"},
                "risk": {"risk_level": "LOW", "risk_score": 5},
                "policy": {"status": "SUCCESS"},
                "payload": {"duration_ms": 12400, "status": "COMPLETED", "output_hash": "sha256_mock_out_99"},
                "delay": 720
            }
        ]

        for step in c1_steps:
            occurred = now - timedelta(seconds=(3600 - step["delay"]))
            p_hash = hash_payload(step["payload"])
            events_to_create.append({
                "tenant_id": tenant_id,
                "event_type": step["type"],
                "event_category": step["category"],
                "event_version": "1.0",
                "occurred_at": occurred,
                "recorded_at": occurred,
                "source_service": step["service"],
                "actor_json": {"user_id": str(tenant_id), "actor_type": "USER", "roles": ["ADMIN", "COMPLIANCE_OFFICER"]},
                "subject_json": step["subject"],
                "correlation_id": corr_id_1,
                "risk_context_json": step["risk"],
                "policy_context_json": step["policy"],
                "payload_json": step["payload"],
                "classification": step["classification"],
                "retention_class": "STANDARD_90_DAYS",
                "event_hash": p_hash
            })

        # =========================================================================
        # STREAM 2: High-Risk Violation Stream (Correlation: a1b2c3d4-e5f6-4789-8012-3456789abcde)
        # Categories: Workflow, Policy, Boundary, Violation, Agent (6 Sequential Steps)
        # =========================================================================
        c2_steps = [
            {
                "type": "WORKFLOW_RUN_STARTED",
                "category": "Workflow",
                "classification": "INTERNAL",
                "service": "workflow_scheduler",
                "subject": {"entity_type": "agents", "entity_id": agent_id_2},
                "risk": {"risk_level": "MEDIUM", "risk_score": 45},
                "policy": {"mode": "AUTONOMOUS"},
                "payload": {"run_code": "RUN-SEC-AUDIT-99"},
                "delay": 0
            },
            {
                "type": "AGENT_STEP_STARTED",
                "category": "Agent",
                "classification": "INTERNAL",
                "service": "agent_runtime",
                "subject": {"entity_type": "agents", "entity_id": agent_id_2},
                "risk": {"risk_level": "MEDIUM", "risk_score": 50},
                "policy": {"mode": "AUTONOMOUS"},
                "payload": {"target_resource": "database_prod_users"},
                "delay": 60
            },
            {
                "type": "POLICY_TRIGGERED",
                "category": "Policy",
                "classification": "CONFIDENTIAL",
                "service": "policy_engine",
                "subject": {"entity_type": "policies", "entity_id": "pol_no_pii_export"},
                "risk": {"risk_level": "HIGH", "risk_score": 85},
                "policy": {"violated_rule": "NO_PII_EXFILTRATION"},
                "payload": {"triggered_by": "unmasked_ssn_query"},
                "delay": 120
            },
            {
                "type": "BOUNDARY_BREACH_ATTEMPTED",
                "category": "Violation",
                "classification": "RESTRICTED",
                "service": "boundary_checker",
                "subject": {"entity_type": "agents", "entity_id": agent_id_2},
                "risk": {"risk_level": "CRITICAL", "risk_score": 95},
                "policy": {"restriction": "RESTRICTED_DATA_BLOCK"},
                "payload": {"breach_type": "QUERY_CLEARANCE_EXCEEDED", "clearance": "PUBLIC", "data_rank": "CONFIDENTIAL"},
                "delay": 180
            },
            {
                "type": "UNAUTHORIZED_ACCESS_BLOCKED",
                "category": "Violation",
                "classification": "RESTRICTED",
                "service": "boundary_checker",
                "subject": {"entity_type": "agents", "entity_id": agent_id_2},
                "risk": {"risk_level": "CRITICAL", "risk_score": 98},
                "policy": {"action": "TERMINATE_SESSION"},
                "payload": {"blocked_operation": "DB_EXPORT", "enforcement": "FAIL_CLOSED"},
                "delay": 240
            },
            {
                "type": "WORKFLOW_RUN_FAILED",
                "category": "Workflow",
                "classification": "INTERNAL",
                "service": "workflow_execution",
                "subject": {"entity_type": "workflows", "entity_id": "wf_secure_export"},
                "risk": {"risk_level": "HIGH", "risk_score": 90},
                "policy": {"failure_reason": "SECURITY_VIOLATION"},
                "payload": {"error": "Terminated by Security Boundary Checker"},
                "delay": 300
            }
        ]

        for step in c2_steps:
            occurred = now - timedelta(seconds=(1800 - step["delay"]))
            p_hash = hash_payload(step["payload"])
            events_to_create.append({
                "tenant_id": tenant_id,
                "event_type": step["type"],
                "event_category": step["category"],
                "event_version": "1.0",
                "occurred_at": occurred,
                "recorded_at": occurred,
                "source_service": step["service"],
                "actor_json": {"user_id": agent_id_2, "actor_type": "AGENT", "roles": ["AUTONOMOUS_AGENT"]},
                "subject_json": step["subject"],
                "correlation_id": corr_id_2,
                "risk_context_json": step["risk"],
                "policy_context_json": step["policy"],
                "payload_json": step["payload"],
                "classification": step["classification"],
                "retention_class": "FINANCIAL_7_YEARS",
                "event_hash": p_hash
            })

        # =========================================================================
        # STREAM 3: Identity & Registry Governance (Correlation: b2c3d4e5-f6a7-4890-9123-456789abcdef)
        # Categories: Identity, Registry, Relationship, Approval, Audit (6 Sequential Steps)
        # =========================================================================
        c3_steps = [
            {
                "type": "USER_LOGIN",
                "category": "Identity",
                "classification": "PUBLIC",
                "service": "auth_service",
                "subject": {"entity_type": "users", "entity_id": "usr_admin_01"},
                "risk": {"risk_level": "LOW", "risk_score": 0},
                "policy": {"mfa": "PASSED"},
                "payload": {"ip_address": "192.168.1.50", "login_method": "OAUTH_SSO"},
                "delay": 0
            },
            {
                "type": "ROLE_ASSIGNED",
                "category": "Identity",
                "classification": "CONFIDENTIAL",
                "service": "auth_service",
                "subject": {"entity_type": "users", "entity_id": "usr_admin_01"},
                "risk": {"risk_level": "LOW", "risk_score": 10},
                "policy": {"role": "GOVERNANCE_ADMIN"},
                "payload": {"assigned_role": "GOVERNANCE_ADMIN", "granted_by": "super_admin"},
                "delay": 60
            },
            {
                "type": "MODEL_REGISTERED",
                "category": "Registry",
                "classification": "PUBLIC",
                "service": "registry_service",
                "subject": {"entity_type": "models", "entity_id": model_id_1},
                "risk": {"risk_level": "LOW", "risk_score": 5},
                "policy": {"vendor": "OpenAI"},
                "payload": {"model_name": "GPT-4o Enterprise", "version": "v2026.1"},
                "delay": 120
            },
            {
                "type": "OWNERSHIP_TRANSFERRED",
                "category": "Relationship",
                "classification": "INTERNAL",
                "service": "relationship_service",
                "subject": {"entity_type": "models", "entity_id": model_id_1},
                "risk": {"risk_level": "LOW", "risk_score": 10},
                "policy": {"owner_type": "PRIMARY_OWNER"},
                "payload": {"new_owner_id": str(tenant_id), "previous_owner": "unassigned"},
                "delay": 180
            },
            {
                "type": "APPROVAL_REQUESTED",
                "category": "Approval",
                "classification": "CONFIDENTIAL",
                "service": "approval_engine",
                "subject": {"entity_type": "models", "entity_id": model_id_1},
                "risk": {"risk_level": "LOW", "risk_score": 15},
                "policy": {"required_signatures": 2},
                "payload": {"approval_type": "MODEL_ACTIVATION", "target_env": "PRODUCTION"},
                "delay": 240
            },
            {
                "type": "AUDIT_EXPORT_GENERATED",
                "category": "Audit",
                "classification": "RESTRICTED",
                "service": "audit_export_service",
                "subject": {"entity_type": "users", "entity_id": "usr_admin_01"},
                "risk": {"risk_level": "LOW", "risk_score": 5},
                "policy": {"export_scope": "FULL_PACKAGE"},
                "payload": {"export_format": "JSON", "manifest_sha256": "sha256_package_manifest_99"},
                "delay": 300
            }
        ]

        for step in c3_steps:
            occurred = now - timedelta(seconds=(900 - step["delay"]))
            p_hash = hash_payload(step["payload"])
            events_to_create.append({
                "tenant_id": tenant_id,
                "event_type": step["type"],
                "event_category": step["category"],
                "event_version": "1.0",
                "occurred_at": occurred,
                "recorded_at": occurred,
                "source_service": step["service"],
                "actor_json": {"user_id": str(tenant_id), "actor_type": "USER", "roles": ["ADMIN"]},
                "subject_json": step["subject"],
                "correlation_id": corr_id_3,
                "risk_context_json": step["risk"],
                "policy_context_json": step["policy"],
                "payload_json": step["payload"],
                "classification": step["classification"],
                "retention_class": "STANDARD_90_DAYS",
                "event_hash": p_hash
            })

        # Insert all into governance_events table via raw SQL to ensure immutability / clean insert
        insert_stmt = text("""
            INSERT INTO governance_events (
                event_id, tenant_id, event_type, event_category, event_version,
                occurred_at, recorded_at, source_service, source_system,
                actor_json, subject_json, correlation_id, risk_context_json,
                policy_context_json, payload_json, classification, retention_class, event_hash
            ) VALUES (
                gen_random_uuid(), :tenant_id, :event_type, :event_category, :event_version,
                :occurred_at, :recorded_at, :source_service, 'guardianiq-backend',
                CAST(:actor_json AS jsonb), CAST(:subject_json AS jsonb), :correlation_id, CAST(:risk_context_json AS jsonb),
                CAST(:policy_context_json AS jsonb), CAST(:payload_json AS jsonb), :classification, :retention_class, :event_hash
            );
        """)

        for e in events_to_create:
            db.execute(insert_stmt, {
                "tenant_id": str(e["tenant_id"]),
                "event_type": e["event_type"],
                "event_category": e["event_category"],
                "event_version": e["event_version"],
                "occurred_at": e["occurred_at"],
                "recorded_at": e["recorded_at"],
                "source_service": e["source_service"],
                "actor_json": json.dumps(e["actor_json"]),
                "subject_json": json.dumps(e["subject_json"]),
                "correlation_id": str(e["correlation_id"]),
                "risk_context_json": json.dumps(e["risk_context_json"]),
                "policy_context_json": json.dumps(e["policy_context_json"]),
                "payload_json": json.dumps(e["payload_json"]),
                "classification": e["classification"],
                "retention_class": e["retention_class"],
                "event_hash": e["event_hash"]
            })

        db.commit()
        logger.info(f"Successfully populated {len(events_to_create)} governance events across ALL 10 categories and ALL 4 classifications!")

    except Exception as ex:
        db.rollback()
        logger.error(f"Failed to populate governance events: {ex}")
        raise ex
    finally:
        db.close()

if __name__ == "__main__":
    populate_events()
