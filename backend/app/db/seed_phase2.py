"""
Seed Script for Governance Phase 2
==================================
Seeds the database with realistic sample data for Phase 2 Orchestration and Configuration modules:
- Workflow Schedules
- Agent Assignments
- Schedule Approvals
- Run History
- Notifications
- Authorization Decisions & Delegations

Usage:
    cd backend
    python -m app.db.seed_phase2
"""

import sys
import os
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
import pytz

# Add current directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal
from app.modules.registry.models import (
    RegistryDepartment, GuardianUser, RegistryRole, RegistryDataSource,
    RegistryAIModel, RegistryAIAgent, RegistryTool, RegistryWorkflow
)
from app.modules.workflow_scheduler.models import (
    ApprovalGroup, Phase2WorkflowSchedule, WorkflowScheduleAgentAssignment,
    WorkflowScheduleApproval, WorkflowScheduleHistory, ApprovalGroupMember
)
from app.modules.workflow_execution.models import (
    WorkflowRun, WorkflowRunStep, WorkflowRunOutput, WorkflowRunFailure
)
from app.modules.workflow_notifications.models import (
    WorkflowNotification
)
from app.modules.authorization.models import (
    WorkflowAuthorizationDecision, WorkflowDelegation
)

def seed_phase2_data():
    db = SessionLocal()
    try:
        print("[INFO] Starting Phase 2 Seeding...")

        # 1. Fetch required registry elements
        admin_user = db.query(GuardianUser).filter(GuardianUser.email == "admin@guardianiq.com").first()
        reviewer_user = db.query(GuardianUser).filter(GuardianUser.email == "reviewer@guardianiq.com").first()
        auditor_user = db.query(GuardianUser).filter(GuardianUser.email == "auditor@guardianiq.com").first()
        sjenkins = db.query(GuardianUser).filter(GuardianUser.email == "sjenkins@guardianiq.com").first()
        mchang = db.query(GuardianUser).filter(GuardianUser.email == "mchang@guardianiq.com").first()
        erodriguez = db.query(GuardianUser).filter(GuardianUser.email == "erodriguez@guardianiq.com").first()

        if not all([admin_user, reviewer_user, sjenkins, mchang, erodriguez]):
            print("[ERROR] Some required registry users are missing. Please run compliance scenario seeds first!")
            return

        # Fetch workflows
        wf_onboarding = db.query(RegistryWorkflow).filter(RegistryWorkflow.workflow_code == "WF-ONBOARDING-PIPELINE").first()
        wf_refund = db.query(RegistryWorkflow).filter(RegistryWorkflow.workflow_code == "WF-AUTO-REFUND").first()
        wf_fraud = db.query(RegistryWorkflow).filter(RegistryWorkflow.workflow_code == "WF-FRAUD-FREEZE").first()

        # Fetch agents
        agent_onboard = db.query(RegistryAIAgent).filter(RegistryAIAgent.agent_code == "AGENT-ONBOARD-01").first()
        agent_refund = db.query(RegistryAIAgent).filter(RegistryAIAgent.agent_code == "AGENT-REFUND-BOT").first()
        agent_fraud = db.query(RegistryAIAgent).filter(RegistryAIAgent.agent_code == "AGENT-FRAUD-SENTINEL").first()

        # Fetch models
        model_onboard = db.query(RegistryAIModel).filter(RegistryAIModel.model_code == "LLM-COMPLIANCE-DOCS").first()
        model_refund = db.query(RegistryAIModel).filter(RegistryAIModel.model_code == "LLM-SUPPORT-001").first()
        model_fraud = db.query(RegistryAIModel).filter(RegistryAIModel.model_code == "ML-FRAUD-DETECT-V4").first()

        # Fetch tools
        tool_refund = db.query(RegistryTool).filter(RegistryTool.tool_code == "API-REFUND-STRIPE").first()
        tool_fraud = db.query(RegistryTool).filter(RegistryTool.tool_code == "API-ACCOUNT-FREEZE").first()

        # Fetch data sources
        ds_onboard = db.query(RegistryDataSource).filter(RegistryDataSource.source_code == "DS-HR-WORKDAY").first()
        ds_fraud = db.query(RegistryDataSource).filter(RegistryDataSource.source_code == "DS-FIN-LEDGER").first()

        # 2. Cleanup Phase 2 tables
        print("[INFO] Cleaning up old Phase 2 data...")
        db.query(WorkflowNotification).delete()
        db.query(WorkflowScheduleApproval).delete()
        db.query(WorkflowScheduleHistory).delete()
        db.query(WorkflowScheduleAgentAssignment).delete()
        db.query(WorkflowRunFailure).delete()
        db.query(WorkflowRunOutput).delete()
        db.query(WorkflowRunStep).delete()
        db.query(WorkflowRun).delete()
        db.query(Phase2WorkflowSchedule).delete()
        db.query(ApprovalGroupMember).delete()
        db.query(ApprovalGroup).delete()
        db.query(WorkflowAuthorizationDecision).delete()
        db.query(WorkflowDelegation).delete()
        db.commit()

        # 3. Create Approval Groups & Members
        print("[INFO] Creating Approval Groups...")
        group_gov = ApprovalGroup(
            id=uuid4(),
            name="Security and Governance Committee",
            tenant_id=admin_user.id
        )
        group_risk = ApprovalGroup(
            id=uuid4(),
            name="Finance Risk Oversight Board",
            tenant_id=admin_user.id
        )
        db.add_all([group_gov, group_risk])
        db.flush()

        # Add members
        members = [
            ApprovalGroupMember(approval_group_id=group_gov.id, user_id=admin_user.id),
            ApprovalGroupMember(approval_group_id=group_gov.id, user_id=reviewer_user.id),
            ApprovalGroupMember(approval_group_id=group_risk.id, user_id=admin_user.id)
        ]
        db.add_all(members)
        db.flush()
        print(f"   Created Groups: '{group_gov.name}' and '{group_risk.name}'")

        # 4. Create Workflow Schedules
        print("[INFO] Creating Schedules...")
        now = datetime.now(timezone.utc)
        
        # Schedule 1: NDA Auto Setup (ACTIVE)
        sched_nda = Phase2WorkflowSchedule(
            id=uuid4(),
            tenant_id=admin_user.id,
            workflow_id=wf_onboarding.id,
            schedule_code="SCH-NDA-AUTO",
            schedule_name="Daily Onboarding Document Scanner",
            schedule_type="DAILY",
            timezone="Asia/Kolkata",
            start_at=now - timedelta(days=30),
            next_run_at=now + timedelta(hours=12),
            last_run_at=now - timedelta(hours=12),
            concurrency_policy="SKIP_IF_RUNNING",
            max_runtime_seconds=600,
            retry_policy_json={"max_retries": 2, "retry_delay_seconds": 120},
            owner_user_id=sjenkins.id,
            owner_department_id=sjenkins.department_id,
            approval_required=False,
            risk_level="LOW",
            schedule_status="ACTIVE"
        )

        # Schedule 2: Support Refund Scanner (PENDING_APPROVAL)
        sched_refund = Phase2WorkflowSchedule(
            id=uuid4(),
            tenant_id=admin_user.id,
            workflow_id=wf_refund.id,
            schedule_code="SCH-REFUND-PROD",
            schedule_name="High-Frequency Refund Monitor",
            schedule_type="CRON",
            cron_expression="*/15 * * * *",
            timezone="Asia/Kolkata",
            start_at=now - timedelta(days=2),
            owner_user_id=mchang.id,
            owner_department_id=mchang.department_id,
            approval_required=True,
            approval_group_id=group_gov.id,
            risk_level="HIGH",
            schedule_status="PENDING_APPROVAL"
        )

        # Schedule 3: Zero-Day Fraud Freeze Protocol (ACTIVE)
        sched_fraud = Phase2WorkflowSchedule(
            id=uuid4(),
            tenant_id=admin_user.id,
            workflow_id=wf_fraud.id,
            schedule_code="SCH-FRAUD-FREEZE",
            schedule_name="Continuous Transaction Fraud Sentinel",
            schedule_type="INTERVAL",
            cron_expression="5",  # representing 5 minute intervals
            timezone="Asia/Kolkata",
            start_at=now - timedelta(days=5),
            next_run_at=now + timedelta(minutes=4),
            last_run_at=now - timedelta(minutes=1),
            owner_user_id=erodriguez.id,
            owner_department_id=erodriguez.department_id,
            approval_required=True,
            approval_group_id=group_risk.id,
            risk_level="CRITICAL",
            schedule_status="ACTIVE"
        )

        # Schedule 4: Legacy Compliance Scan (PAUSED)
        sched_legacy = Phase2WorkflowSchedule(
            id=uuid4(),
            tenant_id=admin_user.id,
            workflow_id=wf_onboarding.id,
            schedule_code="SCH-LEGACY-COMP",
            schedule_name="Weekly Legacy HR Registry Audit",
            schedule_type="WEEKLY",
            timezone="Asia/Kolkata",
            start_at=now - timedelta(days=45),
            owner_user_id=sjenkins.id,
            owner_department_id=sjenkins.department_id,
            approval_required=False,
            risk_level="MEDIUM",
            schedule_status="PAUSED"
        )

        # Schedule 5: On-Demand Onboarding Audit (DRAFT)
        sched_draft = Phase2WorkflowSchedule(
            id=uuid4(),
            tenant_id=admin_user.id,
            workflow_id=wf_onboarding.id,
            schedule_code="SCH-ONBOARD-AUDIT",
            schedule_name="On-Demand HR NDA Verification Checklist",
            schedule_type="MANUAL",
            timezone="Asia/Kolkata",
            owner_user_id=sjenkins.id,
            owner_department_id=sjenkins.department_id,
            approval_required=False,
            risk_level="LOW",
            schedule_status="DRAFT"
        )

        # Schedule 6: Retired Security Check (RETIRED)
        sched_retired = Phase2WorkflowSchedule(
            id=uuid4(),
            tenant_id=admin_user.id,
            workflow_id=wf_onboarding.id,
            schedule_code="SCH-RETIRED-CHECK",
            schedule_name="Deprecated System Log Clearance",
            schedule_type="MANUAL",
            timezone="Asia/Kolkata",
            owner_user_id=sjenkins.id,
            owner_department_id=sjenkins.department_id,
            approval_required=False,
            risk_level="LOW",
            schedule_status="RETIRED"
        )

        db.add_all([sched_nda, sched_refund, sched_fraud, sched_legacy, sched_draft, sched_retired])
        db.flush()
        print("   Seeded 6 Schedules across different statuses.")

        # 5. Agent Assignments
        print("[INFO] Creating Agent Assignments...")
        assignments = [
            # Schedule 1 Assignment
            WorkflowScheduleAgentAssignment(
                id=uuid4(),
                tenant_id=admin_user.id,
                schedule_id=sched_nda.id,
                agent_id=agent_onboard.id,
                model_id=model_onboard.id,
                assignment_role="PRIMARY",
                execution_mode="RECOMMEND_ONLY",
                confidence_threshold=95.0,
                allowed_data_sources_json=[str(ds_onboard.id)] if ds_onboard else [],
                boundary_rules_json={"max_records": 100, "allow_write_tools": False},
                status="ACTIVE"
            ),
            # Schedule 2 Assignment
            WorkflowScheduleAgentAssignment(
                id=uuid4(),
                tenant_id=admin_user.id,
                schedule_id=sched_refund.id,
                agent_id=agent_refund.id,
                model_id=model_refund.id,
                assignment_role="PRIMARY",
                execution_mode="APPROVAL_REQUIRED",
                confidence_threshold=90.0,
                allowed_tools_json=[str(tool_refund.id)] if tool_refund else [],
                boundary_rules_json={"refund_limit_usd": 500.0, "requires_supervisor": True},
                status="ACTIVE"
            ),
            # Schedule 3 Assignment
            WorkflowScheduleAgentAssignment(
                id=uuid4(),
                tenant_id=admin_user.id,
                schedule_id=sched_fraud.id,
                agent_id=agent_fraud.id,
                model_id=model_fraud.id,
                assignment_role="PRIMARY",
                execution_mode="LIMITED_EXECUTION",
                confidence_threshold=99.0,
                allowed_tools_json=[str(tool_fraud.id)] if tool_fraud else [],
                allowed_data_sources_json=[str(ds_fraud.id)] if ds_fraud else [],
                blocked_operations_json=["fully_lock_database"],
                boundary_rules_json={"max_freeze_duration_hours": 24, "immediate_escalation": True},
                status="ACTIVE"
            )
        ]
        db.add_all(assignments)
        db.flush()
        print("   Seeded Agent Mappings and Boundary Rules.")

        # 6. Schedule Approvals
        print("[INFO] Seeding Approvals...")
        approvals = [
            # Schedule 2 (PENDING_APPROVAL) -> Pending Approval Record
            WorkflowScheduleApproval(
                id=uuid4(),
                tenant_id=admin_user.id,
                schedule_id=sched_refund.id,
                approval_type="ACTIVATION",
                approval_group_id=group_gov.id,
                approval_status="PENDING",
                submitted_by=mchang.id,
                created_at=now - timedelta(hours=4)
            ),
            # Schedule 3 (ACTIVE) -> Approved Record
            WorkflowScheduleApproval(
                id=uuid4(),
                tenant_id=admin_user.id,
                schedule_id=sched_fraud.id,
                approval_type="ACTIVATION",
                approval_group_id=group_risk.id,
                approval_status="APPROVED",
                approver_user_id=admin_user.id,
                decision_reason="Policy checklists verified. Stripe API bounds check confirms safety limits under L3 rules.",
                decided_at=now - timedelta(days=4),
                submitted_by=erodriguez.id,
                created_at=now - timedelta(days=5)
            )
        ]
        db.add_all(approvals)
        db.flush()

        # 7. Schedule Histories
        histories = [
            WorkflowScheduleHistory(
                id=uuid4(),
                tenant_id=admin_user.id,
                schedule_id=sched_refund.id,
                change_type="SUBMIT",
                change_summary="Schedule submitted for review by Owner",
                before_json={"schedule_status": "DRAFT"},
                after_json={"schedule_status": "PENDING_APPROVAL"},
                changed_by=mchang.id,
                created_at=now - timedelta(hours=4)
            ),
            WorkflowScheduleHistory(
                id=uuid4(),
                tenant_id=admin_user.id,
                schedule_id=sched_fraud.id,
                change_type="ACTIVATE",
                change_summary="Schedule approved and activated by Super Admin",
                before_json={"schedule_status": "PENDING_APPROVAL"},
                after_json={"schedule_status": "ACTIVE"},
                changed_by=admin_user.id,
                created_at=now - timedelta(days=4)
            )
        ]
        db.add_all(histories)
        db.flush()

        # 8. Workflow Runs & Details
        print("[INFO] Seeding Workflow Execution Runs...")
        
        # Run 1: Fraud Freeze (COMPLETED, Critical risk, highly compliant)
        run1_id = uuid4()
        run1 = WorkflowRun(
            id=run1_id,
            tenant_id=admin_user.id,
            schedule_id=sched_fraud.id,
            workflow_id=wf_fraud.id,
            run_code="RUN-FRD-20260623-001",
            trigger_type="SCHEDULED",
            triggered_by_actor_type="SYSTEM",
            run_status="COMPLETED",
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=2) + timedelta(seconds=23),
            duration_ms=23000,
            risk_level="CRITICAL",
            summary="Zero-Day Fraud freeze executed successfully on suspicious Mongo ledger transaction.",
            context_json={"ledger_partition": "eu-partition-4", "eval_mode": "strict"},
            result_json={"accounts_scanned": 12040, "anomalies_detected": 1, "action_taken": "FREEZE_API_CALL"}
        )

        # Run 2: Fraud Freeze (FAILED, Gateway timeout)
        run2_id = uuid4()
        run2 = WorkflowRun(
            id=run2_id,
            tenant_id=admin_user.id,
            schedule_id=sched_fraud.id,
            workflow_id=wf_fraud.id,
            run_code="RUN-FRD-20260623-002",
            trigger_type="SCHEDULED",
            triggered_by_actor_type="SYSTEM",
            run_status="FAILED",
            started_at=now - timedelta(hours=1),
            completed_at=now - timedelta(hours=1) + timedelta(seconds=4),
            duration_ms=4500,
            risk_level="CRITICAL",
            summary="Failed due to downstream webhook gateway timeout during account freeze tool call.",
            context_json={"ledger_partition": "eu-partition-4"},
            result_json={"error_step": "Execute Account Freeze", "retry_state": "exhausted"}
        )

        # Run 3: Fraud Freeze (RUNNING, active right now)
        run3_id = uuid4()
        run3 = WorkflowRun(
            id=run3_id,
            tenant_id=admin_user.id,
            schedule_id=sched_fraud.id,
            workflow_id=wf_fraud.id,
            run_code="RUN-FRD-20260623-003",
            trigger_type="MANUAL",
            triggered_by_user_id=admin_user.id,
            triggered_by_actor_type="USER",
            run_status="RUNNING",
            started_at=now - timedelta(minutes=3),
            risk_level="CRITICAL",
            summary="Manual check triggered by security officer Sarah Jenkins.",
            context_json={"forced_triage": True}
        )

        # Run 4: NDA Scanner (COMPLETED)
        run4_id = uuid4()
        run4 = WorkflowRun(
            id=run4_id,
            tenant_id=admin_user.id,
            schedule_id=sched_nda.id,
            workflow_id=wf_onboarding.id,
            run_code="RUN-NDA-20260623-001",
            trigger_type="SCHEDULED",
            triggered_by_actor_type="SYSTEM",
            run_status="COMPLETED",
            started_at=now - timedelta(days=1),
            completed_at=now - timedelta(days=1) + timedelta(seconds=6),
            duration_ms=6200,
            risk_level="LOW",
            summary="Daily NDA scanner finished successfully with 0 policy compliance violations.",
            context_json={"scan_directory": "/tmp/onboard_signatures"}
        )

        db.add_all([run1, run2, run3, run4])
        db.flush()

        # Seed steps for Run 1
        steps_run1 = [
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run1_id, step_code="Ingest Ledger Stream", step_order=1, step_type="START", step_status="COMPLETED", started_at=run1.started_at, completed_at=run1.started_at + timedelta(seconds=2), input_json={}, output_json={"records_ingested": 105}),
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run1_id, step_code="Evaluate Anomaly", step_order=2, step_type="EVALUATION", step_status="COMPLETED", started_at=run1.started_at + timedelta(seconds=3), completed_at=run1.started_at + timedelta(seconds=7), input_json={"records_count": 105}, output_json={"anomaly_risk": 0.992, "account_id": "ACC-891901"}),
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run1_id, step_code="Execute Account Freeze", step_order=3, step_type="TOOL", step_status="COMPLETED", started_at=run1.started_at + timedelta(seconds=8), completed_at=run1.started_at + timedelta(seconds=15), input_json={"action": "freeze", "account_id": "ACC-891901"}, output_json={"freeze_status": "SUCCESS", "reference_id": "REF-STR-010"}),
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run1_id, step_code="Alert Risk Team", step_order=4, step_type="END", step_status="COMPLETED", started_at=run1.started_at + timedelta(seconds=16), completed_at=run1.started_at + timedelta(seconds=23), input_json={"alert_message": "Account ACC-891901 frozen due to high risk"}, output_json={"alert_sent": True})
        ]

        # Seed steps for Run 2
        steps_run2 = [
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run2_id, step_code="Ingest Ledger Stream", step_order=1, step_type="START", step_status="COMPLETED", started_at=run2.started_at, completed_at=run2.started_at + timedelta(seconds=1), input_json={}, output_json={"records_ingested": 42}),
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run2_id, step_code="Evaluate Anomaly", step_order=2, step_type="EVALUATION", step_status="COMPLETED", started_at=run2.started_at + timedelta(seconds=2), completed_at=run2.started_at + timedelta(seconds=3), input_json={"records_count": 42}, output_json={"anomaly_risk": 0.985, "account_id": "ACC-904031"}),
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run2_id, step_code="Execute Account Freeze", step_order=3, step_type="TOOL", step_status="FAILED", started_at=run2.started_at + timedelta(seconds=4), completed_at=run2.started_at + timedelta(seconds=4), input_json={"action": "freeze", "account_id": "ACC-904031"}, error_message="Stripe API Gateway Timeout (504). Downstream node core.banking.internal: freeze API endpoint timed out.")
        ]

        # Seed steps for Run 3
        steps_run3 = [
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run3_id, step_code="Ingest Ledger Stream", step_order=1, step_type="START", step_status="COMPLETED", started_at=run3.started_at, completed_at=run3.started_at + timedelta(seconds=2), input_json={}, output_json={"records_ingested": 12}),
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run3_id, step_code="Evaluate Anomaly", step_order=2, step_type="EVALUATION", step_status="RUNNING", started_at=run3.started_at + timedelta(seconds=3))
        ]

        # Seed steps for Run 4
        steps_run4 = [
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run4_id, step_code="START", step_order=1, step_type="START", step_status="COMPLETED", started_at=run4.started_at, completed_at=run4.started_at + timedelta(seconds=1)),
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run4_id, step_code="Fetch Employee Record", step_order=2, step_type="STEP", step_status="COMPLETED", started_at=run4.started_at + timedelta(seconds=1), completed_at=run4.started_at + timedelta(seconds=2)),
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run4_id, step_code="Scan Signed NDA", step_order=3, step_type="STEP", step_status="COMPLETED", started_at=run4.started_at + timedelta(seconds=2), completed_at=run4.started_at + timedelta(seconds=5)),
            WorkflowRunStep(id=uuid4(), tenant_id=admin_user.id, run_id=run4_id, step_code="END", step_order=4, step_type="END", step_status="COMPLETED", started_at=run4.started_at + timedelta(seconds=5), completed_at=run4.started_at + timedelta(seconds=6))
        ]

        db.add_all(steps_run1 + steps_run2 + steps_run3 + steps_run4)
        db.flush()

        # Seed Outputs for Run 1
        output1 = WorkflowRunOutput(
            id=uuid4(),
            tenant_id=admin_user.id,
            run_id=run1_id,
            output_type="COMPLIANCE_FINDING",
            severity="CRITICAL",
            risk_score=9.82,
            findings_json=[
                {"code": "HIGH_VALUE_PII_EXPOSURE", "message": "High value account transaction metadata includes plaintext email address inside mongodb document."}
            ],
            recommendations_json=[
                {"action": "MASKING", "detail": "Apply dynamic field-level encryption on client-side ledger streams."}
            ],
            evidence_json={"api_response_reference": "REF-STR-010", "blockchain_hash": "0xfa3919e9104058d929ee91b920ad"},
            raw_output_json={"account": "ACC-891901", "transaction_amt": 894000.0, "risk_factors": ["unusual_location", "high_amount", "plaintext_email"]},
            parse_status="PARSED"
        )
        db.add(output1)

        # Seed Failures for Run 2
        failure2 = WorkflowRunFailure(
            id=uuid4(),
            tenant_id=admin_user.id,
            run_id=run2_id,
            failure_type="API_GATEWAY_TIMEOUT",
            failure_code="504_TIMEOUT",
            failure_message="Stripe API Gateway Timeout. Downstream core banking endpoints did not respond within the 5000ms threshold.",
            failed_step_id=None,
            retry_count=2,
            max_retries=2,
            escalation_required=True,
            escalation_sent_at=now - timedelta(minutes=55)
        )
        db.add(failure2)
        db.flush()
        print("   Seeded Step Timelines, Compliance Findings, and Webhook Failures.")

        # 9. Workflow Notifications
        print("[INFO] Seeding Notifications...")
        notifications = [
            # 1. Unread Action required for mchang schedule
            WorkflowNotification(
                id=uuid4(),
                tenant_id=admin_user.id,
                recipient_user_id=admin_user.id,
                notification_type="APPROVAL_REQUIRED",
                title="Schedule Approval Required",
                message=f"Schedule '{sched_refund.schedule_name}' ({sched_refund.schedule_code}) requires authorization due to High risk tools.",
                severity="HIGH",
                entity_type="WORKFLOW_SCHEDULE",
                entity_id=sched_refund.id,
                status="UNREAD",
                created_by=mchang.id,
                created_at=now - timedelta(hours=4)
            ),
            # 2. Unread Failure alert
            WorkflowNotification(
                id=uuid4(),
                tenant_id=admin_user.id,
                recipient_user_id=admin_user.id,
                notification_type="RUN_FAILED",
                title="Workflow Execution Failure",
                message=f"Critical execution '{run2.run_code}' failed at Execute Account Freeze step with 504 Timeout.",
                severity="CRITICAL",
                entity_type="WORKFLOW_RUN",
                entity_id=run2_id,
                status="UNREAD",
                created_by=admin_user.id,
                created_at=now - timedelta(hours=1)
            ),
            # 3. Read High Risk output notification
            WorkflowNotification(
                id=uuid4(),
                tenant_id=admin_user.id,
                recipient_user_id=admin_user.id,
                notification_type="HIGH_RISK_OUTPUT",
                title="Critical Policy Violation Flagged",
                message=f"Run '{run1.run_code}' flagged a critical risk score of 9.82. HIPAA PII exposure detected.",
                severity="CRITICAL",
                entity_type="WORKFLOW_RUN",
                entity_id=run1_id,
                status="READ",
                read_at=now - timedelta(minutes=45),
                created_by=admin_user.id,
                created_at=now - timedelta(hours=2)
            ),
            # 4. Acknowledged schedule activated notification
            WorkflowNotification(
                id=uuid4(),
                tenant_id=admin_user.id,
                recipient_user_id=admin_user.id,
                notification_type="SCHEDULE_ACTIVATED",
                title="Workflow Schedule Activated",
                message=f"Schedule '{sched_fraud.schedule_name}' has been successfully authorized and moved to ACTIVE.",
                severity="LOW",
                entity_type="WORKFLOW_SCHEDULE",
                entity_id=sched_fraud.id,
                status="ACKNOWLEDGED",
                read_at=now - timedelta(days=3),
                acknowledged_at=now - timedelta(days=3),
                created_by=admin_user.id,
                created_at=now - timedelta(days=4)
            )
        ]
        db.add_all(notifications)
        db.flush()
        print("   Seeded 4 Notifications across categories.")

        # 10. Authorization Decisions & Delegations
        print("[INFO] Seeding Authorization Decisions & Delegations...")
        decisions = [
            WorkflowAuthorizationDecision(
                id=uuid4(),
                tenant_id=admin_user.id,
                subject_user_id=admin_user.id,
                subject_type="USER",
                object_type="workflow_schedules",
                object_id=sched_fraud.id,
                action="ACTIVATE_WORKFLOW_SCHEDULE",
                decision="ALLOW",
                reason_json={"details": "User has SUPER_ADMIN role with platform privileges"},
                rbac_result={"roles": ["SUPER_ADMIN"]},
                abac_result={"emergency_flag": False},
                relationship_result={"owner": False}
            ),
            WorkflowAuthorizationDecision(
                id=uuid4(),
                tenant_id=admin_user.id,
                subject_user_id=auditor_user.id,
                subject_type="USER",
                object_type="workflow_schedules",
                object_id=sched_fraud.id,
                action="ACTIVATE_WORKFLOW_SCHEDULE",
                decision="DENY",
                reason_json={"details": "Auditor lacks required ACTIVATE_WORKFLOW_SCHEDULE permissions"},
                rbac_result={"roles": ["AUDITOR"]},
                abac_result={},
                relationship_result={}
            )
        ]
        db.add_all(decisions)

        delegation = WorkflowDelegation(
            id=uuid4(),
            tenant_id=admin_user.id,
            delegator_user_id=reviewer_user.id,
            delegatee_user_id=admin_user.id,
            start_at=now - timedelta(days=2),
            end_at=now + timedelta(days=5),
            status="ACTIVE"
        )
        db.add(delegation)
        db.flush()
        
        db.commit()
        print("[SUCCESS] Seeding Governance Phase 2 Complete!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_phase2_data()
