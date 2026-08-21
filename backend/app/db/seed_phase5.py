"""
Seed Script for Governance Phase 5 (Policy ENFORCE)
===================================================
Seeds reference master data, pilot governance policies, versioned rules,
data source classified fields, agent runtime boundaries, and executes the
automated tool capabilities backfill from existing registry tools.

Usage:
    cd backend
    python -m app.db.seed_phase5
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.agent.models import Agent
from app.modules.registry.models import Tool, Workflow
from app.modules.datasource.models import DataSource
from app.modules.policy_engine.models import (
    GovernancePolicy,
    PolicyVersion,
    PolicyRule,
    PolicyException,
    PolicyEvaluation,
    PolicyRuleEvaluation,
    EnforcementDecision,
    PolicyApproval,
)
from app.modules.agent_boundary.models import (
    AgentRuntimeBoundary,
    ToolCapability,
    AgentToolPermission,
    DataSourceField,
    AgentDataPermission,
)
from app.modules.relationship.models import PolicyBinding, ObjectResponsibility


def infer_access_mode(operation_name: str) -> str:
    """Infers READ_ONLY vs EXECUTE based on operation name prefix."""
    op_lower = operation_name.lower()
    read_prefixes = ("get_", "read_", "view_", "list_", "fetch_", "search_", "select_", "query_", "find_")
    if any(op_lower.startswith(p) for p in read_prefixes):
        return "READ_ONLY"
    return "EXECUTE"


def backfill_tool_capabilities(db, tenant_id: UUID) -> int:
    """
    Explodes allowed_operations_json on existing tools into granular tool_capabilities rows.
    Tags each row with {"_backfilled": True} in input_schema_json and metadata_json.
    """
    print("[INFO] Backfilling Tool Capabilities from existing Registry Tools...")
    tools = db.query(Tool).all()
    created_count = 0

    for tool in tools:
        ops = tool.allowed_operations_json or []
        if isinstance(ops, str):
            import json
            try:
                ops = json.loads(ops)
            except Exception:
                ops = [ops]

        for op_name in ops:
            if not isinstance(op_name, str) or not op_name.strip():
                continue
            op_name = op_name.strip()

            # Check if capability already exists
            existing = (
                db.query(ToolCapability)
                .filter(
                    ToolCapability.tool_id == tool.id,
                    ToolCapability.capability_name == op_name,
                )
                .first()
            )
            if not existing:
                access_mode = infer_access_mode(op_name)
                cap = ToolCapability(
                    tenant_id=tenant_id,
                    tool_id=tool.id,
                    capability_name=op_name,
                    description=f"Auto-backfilled capability for {op_name}",
                    access_mode=access_mode,
                    requires_approval=(access_mode != "READ_ONLY"),
                    input_schema_json={"_backfilled": True},
                    metadata_json={"_backfilled": True},
                )
                db.add(cap)
                created_count += 1

    db.flush()
    print(f"[SUCCESS] Backfilled {created_count} Tool Capability records.")
    return created_count


def seed_governance_policies_and_rules(db, tenant_id: UUID, admin_user_id: UUID):
    """Seeds master reference policies, active versions, and granular rules."""
    print("[INFO] Seeding Master Governance Policies, Versions, and Rules...")
    now = datetime.now(timezone.utc)

    policies_data = [
        {
            "code": "POL-DLP-001",
            "name": "Enterprise Data Loss Prevention & PII Protection",
            "description": "Enforces automatic masking of sensitive PII (SSN, credit card, salary) and blocks unauthorized data exfiltration.",
            "category": "DATA_ACCESS",
            "enforcement_mode": "BLOCKING",
            "priority": 10,
            "rules": [
                {
                    "rule_code": "RULE-DLP-SSN-REDACT",
                    "name": "Redact Unmasked SSN",
                    "description": "Automatically redacts SSN fields when queried by agents without elevated data permissions.",
                    "rule_type": "DATA_ACCESS",
                    "target_type": "DATA_SOURCE",
                    "target_id": "*",
                    "condition_expression": "data.columns contains 'ssn' and actor.has_elevated_pii_clearance == false",
                    "condition_json": {"field": "columns", "op": "contains", "value": "ssn"},
                    "action": "MODIFY",
                    "severity": "CRITICAL",
                    "execution_order": 1,
                },
                {
                    "rule_code": "RULE-DLP-RESTRICTED-EXPORT-APPROVE",
                    "name": "Require Approval for Restricted Data Export",
                    "description": "Triggers 2-Layer supervisor approval if an agent attempts bulk export of restricted tables.",
                    "rule_type": "DATA_ACCESS",
                    "target_type": "DATA_SOURCE",
                    "target_id": "*",
                    "condition_expression": "operation == 'EXPORT' and data.classification == 'RESTRICTED'",
                    "condition_json": {"field": "classification", "op": "==", "value": "RESTRICTED"},
                    "action": "REQUIRE_APPROVAL",
                    "severity": "HIGH",
                    "execution_order": 2,
                },
                {
                    "rule_code": "RULE-DLP-BLOCK-UNAUTHORIZED-DELETE",
                    "name": "Block Destructive Data Deletions",
                    "description": "Denies all DELETE or DROP operations from AI agents on core databases.",
                    "rule_type": "DATA_ACCESS",
                    "target_type": "DATA_SOURCE",
                    "target_id": "*",
                    "condition_expression": "operation in ['DELETE', 'DROP', 'TRUNCATE']",
                    "condition_json": {"field": "operation", "op": "in", "value": ["DELETE", "DROP", "TRUNCATE"]},
                    "action": "DENY",
                    "severity": "CRITICAL",
                    "execution_order": 3,
                },
            ],
        },
        {
            "code": "POL-TOOL-001",
            "name": "Agent Tool Execution Boundary & Whitelist",
            "description": "Restricts tool capabilities, parameters, and invocation rate limits across autonomous agents.",
            "category": "TOOL_EXECUTION",
            "enforcement_mode": "BLOCKING",
            "priority": 20,
            "rules": [
                {
                    "rule_code": "RULE-TOOL-ADMIN-SUPERVISION",
                    "name": "Supervised Approval for Admin Tools",
                    "description": "Requires human approval before executing any tool capability marked with access_mode='ADMIN'.",
                    "rule_type": "TOOL_BOUNDARY",
                    "target_type": "TOOL",
                    "target_id": "*",
                    "condition_expression": "tool.access_mode == 'ADMIN'",
                    "condition_json": {"field": "access_mode", "op": "==", "value": "ADMIN"},
                    "action": "REQUIRE_APPROVAL",
                    "severity": "HIGH",
                    "execution_order": 1,
                },
                {
                    "rule_code": "RULE-TOOL-SCHEMA-PARAM-VALIDATION",
                    "name": "Enforce Valid Tool Schema Parameters",
                    "description": "Denies execution if parameters violate the declared JSON schema constraints.",
                    "rule_type": "TOOL_BOUNDARY",
                    "target_type": "TOOL",
                    "target_id": "*",
                    "condition_expression": "tool.is_schema_valid == false",
                    "condition_json": {"field": "is_schema_valid", "op": "==", "value": False},
                    "action": "DENY",
                    "severity": "HIGH",
                    "execution_order": 2,
                },
            ],
        },
        {
            "code": "POL-AUTONOMY-001",
            "name": "Agent Autonomy Ceiling & Financial Approval Limit",
            "description": "Caps single-action autonomy and routes high-value operational decisions to compliance review.",
            "category": "AUTONOMY",
            "enforcement_mode": "BLOCKING",
            "priority": 30,
            "rules": [
                {
                    "rule_code": "RULE-AUTONOMY-HIGH-VALUE-TX",
                    "name": "Financial Action Over $10,000 Threshold",
                    "description": "Transactions over $10,000 require 2-tier approval from Line Manager and Risk Officer.",
                    "rule_type": "AUTONOMY",
                    "target_type": "AGENT",
                    "target_id": "*",
                    "condition_expression": "facts.transaction_amount > 10000",
                    "condition_json": {"field": "transaction_amount", "op": ">", "value": 10000},
                    "action": "REQUIRE_APPROVAL",
                    "severity": "CRITICAL",
                    "execution_order": 1,
                },
                {
                    "rule_code": "RULE-AUTONOMY-STRICT-OVERSIGHT",
                    "name": "Enforce Strict Oversight for Unverified Models",
                    "description": "Forces human verification for agents utilizing uncertified LLM providers.",
                    "rule_type": "AUTONOMY",
                    "target_type": "AGENT",
                    "target_id": "*",
                    "condition_expression": "model.is_enterprise_certified == false",
                    "condition_json": {"field": "model.is_enterprise_certified", "op": "==", "value": False},
                    "action": "REQUIRE_APPROVAL",
                    "severity": "MEDIUM",
                    "execution_order": 2,
                },
            ],
        },
    ]

    for p_data in policies_data:
        policy = db.query(GovernancePolicy).filter(GovernancePolicy.policy_code == p_data["code"]).first()
        if not policy:
            policy = GovernancePolicy(
                tenant_id=tenant_id,
                policy_code=p_data["code"],
                name=p_data["name"],
                description=p_data["description"],
                category=p_data["category"],
                enforcement_mode=p_data["enforcement_mode"],
                priority=p_data["priority"],
                effective_from=now,
                owner_user_id=admin_user_id,
                status="ACTIVE",
            )
            db.add(policy)
            db.flush()

            # Synchronize into object_responsibilities
            resp = ObjectResponsibility(
                tenant_id=tenant_id,
                object_type="POLICY",
                object_id=str(policy.id),
                actor_type="USER",
                actor_id=str(admin_user_id),
                responsibility_type="OWNER",
                is_primary=True,
                effective_from=now,
                status="ACTIVE",
            )
            db.add(resp)

            # Create Active Version 1
            ver = PolicyVersion(
                tenant_id=tenant_id,
                policy_id=policy.id,
                version_number=1,
                status="ACTIVE",
                changelog="Initial baseline v1 activation",
                rules_count=len(p_data["rules"]),
                activated_at=now,
                activated_by=admin_user_id,
            )
            db.add(ver)
            db.flush()

            # Create Rules
            for r_data in p_data["rules"]:
                rule = PolicyRule(
                    tenant_id=tenant_id,
                    policy_version_id=ver.id,
                    rule_code=r_data["rule_code"],
                    name=r_data["name"],
                    description=r_data["description"],
                    rule_type=r_data["rule_type"],
                    target_type=r_data["target_type"],
                    target_id=r_data["target_id"],
                    condition_expression=r_data["condition_expression"],
                    condition_json=r_data["condition_json"],
                    action=r_data["action"],
                    severity=r_data["severity"],
                    execution_order=r_data["execution_order"],
                    is_active=True,
                )
                db.add(rule)

    db.flush()
    print("[SUCCESS] Master Governance Policies & Rules seeded.")


def seed_data_source_fields_and_permissions(db, tenant_id: UUID):
    """Seeds classified columns on registered data sources and agent permissions."""
    print("[INFO] Seeding Data Source Fields & Permissions...")
    datasources = db.query(DataSource).all()
    agents = db.query(Agent).all()

    standard_fields = [
        {"name": "customer_id", "type": "STRING", "classification": "PUBLIC", "sensitivity": "LOW", "is_pii": False, "mask": None},
        {"name": "full_name", "type": "STRING", "classification": "INTERNAL", "sensitivity": "MEDIUM", "is_pii": True, "mask": "PARTIAL_MASK"},
        {"name": "email", "type": "STRING", "classification": "INTERNAL", "sensitivity": "MEDIUM", "is_pii": True, "mask": "PARTIAL_MASK"},
        {"name": "annual_income", "type": "NUMERIC", "classification": "CONFIDENTIAL", "sensitivity": "HIGH", "is_pii": False, "mask": "PARTIAL_MASK"},
        {"name": "credit_score", "type": "INTEGER", "classification": "CONFIDENTIAL", "sensitivity": "HIGH", "is_pii": False, "mask": None},
        {"name": "ssn", "type": "STRING", "classification": "RESTRICTED", "sensitivity": "CRITICAL", "is_pii": True, "mask": "REDACT"},
        {"name": "credit_card_number", "type": "STRING", "classification": "RESTRICTED", "sensitivity": "CRITICAL", "is_pii": True, "mask": "REDACT"},
    ]

    for ds in datasources:
        for f_data in standard_fields:
            existing = (
                db.query(DataSourceField)
                .filter(
                    DataSourceField.data_source_id == ds.id,
                    DataSourceField.field_name == f_data["name"],
                )
                .first()
            )
            if not existing:
                field = DataSourceField(
                    tenant_id=tenant_id,
                    data_source_id=ds.id,
                    field_name=f_data["name"],
                    data_type=f_data["type"],
                    classification=f_data["classification"],
                    sensitivity_level=f_data["sensitivity"],
                    is_pii=f_data["is_pii"],
                    masking_strategy=f_data["mask"],
                    is_active=True,
                )
                db.add(field)

    db.flush()

    # Seed Agent Data Permissions
    for agent in agents:
        for ds in datasources:
            existing_perm = (
                db.query(AgentDataPermission)
                .filter(
                    AgentDataPermission.agent_id == agent.id,
                    AgentDataPermission.data_source_id == ds.id,
                )
                .first()
            )
            if not existing_perm:
                perm = AgentDataPermission(
                    tenant_id=tenant_id,
                    agent_id=agent.id,
                    data_source_id=ds.id,
                    allowed_operations_json=["READ", "TRANSFORM"],
                    max_classification="CONFIDENTIAL",
                    max_sensitivity="HIGH",
                    is_active=True,
                )
                db.add(perm)

    db.flush()
    print("[SUCCESS] Data Source Fields & Permissions seeded.")


def seed_agent_runtime_boundaries(db, tenant_id: UUID):
    """Seeds runtime autonomy boundaries and tool permissions for agents."""
    print("[INFO] Seeding Agent Runtime Boundaries & Tool Permissions...")
    agents = db.query(Agent).all()
    tools = db.query(Tool).all()

    for agent in agents:
        existing_bound = db.query(AgentRuntimeBoundary).filter(AgentRuntimeBoundary.agent_id == agent.id).first()
        if not existing_bound:
            boundary = AgentRuntimeBoundary(
                tenant_id=tenant_id,
                agent_id=agent.id,
                max_autonomy_level="HUMAN_SUPERVISED",
                allowed_access_modes_json=["READ_ONLY", "EXECUTE"],
                rate_limit_per_minute=120,
                max_concurrency=10,
                allow_sub_agent_spawn=False,
                require_approval_threshold=10000.00,
                is_active=True,
            )
            db.add(boundary)

        # Seed Tool permissions
        for tool in tools:
            existing_tool_perm = (
                db.query(AgentToolPermission)
                .filter(
                    AgentToolPermission.agent_id == agent.id,
                    AgentToolPermission.tool_id == tool.id,
                )
                .first()
            )
            if not existing_tool_perm:
                tool_perm = AgentToolPermission(
                    tenant_id=tenant_id,
                    agent_id=agent.id,
                    tool_id=tool.id,
                    permission_level="EXECUTE",
                    max_calls_per_run=50,
                    require_approval=(tool.access_mode in ["ADMIN", "WRITE"]),
                    is_active=True,
                )
                db.add(tool_perm)

    db.flush()
    print("[SUCCESS] Agent Runtime Boundaries & Tool Permissions seeded.")


def seed_policy_bindings(db, tenant_id: UUID):
    """Binds active policies to agents and data sources with LATEST version strategy."""
    print("[INFO] Seeding Policy Bindings...")
    policies = db.query(GovernancePolicy).all()
    agents = db.query(Agent).all()
    datasources = db.query(DataSource).all()
    now = datetime.now(timezone.utc)

    for policy in policies:
        # Bind DLP and AUTONOMY to agents
        for agent in agents:
            existing_bind = (
                db.query(PolicyBinding)
                .filter(
                    PolicyBinding.policy_id == policy.id,
                    PolicyBinding.target_type == "AGENT",
                    PolicyBinding.target_id == str(agent.id),
                )
                .first()
            )
            if not existing_bind:
                binding = PolicyBinding(
                    tenant_id=tenant_id,
                    policy_id=policy.id,
                    target_type="AGENT",
                    target_id=str(agent.id),
                    binding_scope="GLOBAL",
                    priority=policy.priority,
                    is_mandatory=True,
                    effective_from=now,
                    status="ACTIVE",
                    version_strategy="LATEST",
                )
                db.add(binding)

        # Bind DATA_ACCESS policies to data sources
        if policy.category == "DATA_ACCESS":
            for ds in datasources:
                existing_ds_bind = (
                    db.query(PolicyBinding)
                    .filter(
                        PolicyBinding.policy_id == policy.id,
                        PolicyBinding.target_type == "DATA_SOURCE",
                        PolicyBinding.target_id == str(ds.id),
                    )
                    .first()
                )
                if not existing_ds_bind:
                    ds_binding = PolicyBinding(
                        tenant_id=tenant_id,
                        policy_id=policy.id,
                        target_type="DATA_SOURCE",
                        target_id=str(ds.id),
                        binding_scope="TENANT",
                        priority=policy.priority,
                        is_mandatory=True,
                        effective_from=now,
                        status="ACTIVE",
                        version_strategy="LATEST",
                    )
                    db.add(ds_binding)

    db.flush()
    print("[SUCCESS] Policy Bindings seeded.")


def seed_phase5_event_schemas(db):
    """Registers Phase 5 audit event schemas in event_schema_registry."""
    import json
    from sqlalchemy import text

    print("[INFO] Seeding Phase 5 Event Schemas into event_schema_registry...")
    phase5_events = [
        ("POLICY_CREATED", "POLICY"),
        ("POLICY_UPDATED", "POLICY"),
        ("POLICY_VERSION_CREATED", "POLICY"),
        ("POLICY_VERSION_ACTIVATED", "POLICY"),
        ("POLICY_SUSPENDED", "POLICY"),
        ("POLICY_RETIRED", "POLICY"),
        ("POLICY_BINDING_CREATED", "POLICY_BINDING"),
        ("POLICY_BINDING_UPDATED", "POLICY_BINDING"),
        ("POLICY_BINDING_DEACTIVATED", "POLICY_BINDING"),
        ("POLICY_EVALUATED", "ENFORCEMENT"),
        ("POLICY_TRIGGERED", "ENFORCEMENT"),
        ("POLICY_RULE_EVALUATED", "ENFORCEMENT"),
        ("POLICY_EXCEPTION_REQUESTED", "POLICY_EXCEPTION"),
        ("POLICY_EXCEPTION_APPROVED", "POLICY_EXCEPTION"),
        ("POLICY_EXCEPTION_REJECTED", "POLICY_EXCEPTION"),
        ("POLICY_EXCEPTION_REVOKED", "POLICY_EXCEPTION"),
        ("AGENT_ACTION_REQUESTED", "AGENT_RUNTIME"),
        ("AGENT_ACTION_VALIDATED", "AGENT_RUNTIME"),
        ("AGENT_ACTION_BLOCKED", "AGENT_RUNTIME"),
        ("AGENT_ACTION_OVERRIDDEN", "AGENT_RUNTIME"),
        ("TOOL_ACCESS_ATTEMPTED", "TOOL_GOVERNANCE"),
        ("TOOL_ACCESS_DENIED", "TOOL_GOVERNANCE"),
        ("TOOL_EXECUTION_EVALUATED", "TOOL_GOVERNANCE"),
        ("DATA_ACCESS_REQUESTED", "DATA_GOVERNANCE"),
        ("DATA_ACCESS_DENIED", "DATA_GOVERNANCE"),
        ("DATA_ACCESS_EVALUATED", "DATA_GOVERNANCE"),
        ("DATA_TRANSFORMATION_APPLIED", "DATA_GOVERNANCE"),
        ("MODEL_INVOCATION_BLOCKED", "AGENT_BOUNDARY"),
        ("ACTION_EXECUTED", "RUNTIME"),
        ("ACTION_FAILED", "RUNTIME"),
        ("RUNTIME_AUTHORIZATION_EVALUATED", "ENFORCEMENT"),
        ("RUNTIME_ENFORCEMENT_APPLIED", "ENFORCEMENT"),
    ]

    for event_type, category in phase5_events:
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

    db.flush()
    print("[SUCCESS] Phase 5 Event Schemas registered.")


def seed_phase5_master():
    """Master entry point for Phase 5 reference seeding and tool capabilities backfill."""
    db = SessionLocal()
    try:
        print("[INFO] Starting Phase 5 Reference Seeding & Capabilities Backfill...")

        # Resolve Tenant & Admin User
        admin_user = db.query(User).filter(User.email == "admin@guardianiq.com").first()
        if not admin_user:
            admin_user = db.query(User).first()

        if not admin_user:
            print("[ERROR] No user found in database. Please run base seed first.")
            return

        tenant_id = admin_user.id
        admin_user_id = admin_user.id

        # 0. Seed Event Schemas
        seed_phase5_event_schemas(db)

        # 1. Backfill tool capabilities
        backfill_tool_capabilities(db, tenant_id)

        # 2. Seed Governance Policies, Versions, Rules
        seed_governance_policies_and_rules(db, tenant_id, admin_user_id)

        # 3. Seed Data Source Fields & Permissions
        seed_data_source_fields_and_permissions(db, tenant_id)

        # 4. Seed Agent Runtime Boundaries & Tool Permissions
        seed_agent_runtime_boundaries(db, tenant_id)

        # 5. Seed Policy Bindings
        seed_policy_bindings(db, tenant_id)

        db.commit()
        print("[ALL SUCCESS] Phase 5 Master Reference Seeding & Backfill Completed Successfully!")
    except Exception as e:
        db.rollback()
        print(f"[FATAL ERROR] Phase 5 Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_phase5_master()

