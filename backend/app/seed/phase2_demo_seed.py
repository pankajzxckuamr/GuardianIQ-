"""
Phase 2 demo data seeder.

Populates rich, varied data so all Phase 2 screens can be verified:
  - Workflow Scheduler  (schedules across every status)
  - Run History         (runs across every status)
  - Schedule Approvals  (pending-approval schedules + approval records)
  - Notifications        (varied types / severities / read states)
  - Agent Assignments    (assignments with boundaries)

The demo rows use a DEMO_ prefix and are fully re-runnable: existing demo
rows are removed first, then recreated.

Usage:
    cd backend
    python -m app.seed.phase2_demo_seed
"""
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.modules.registry.models import (
    GuardianUser, RegistryRole, RegistryDepartment,
    RegistryWorkflow, RegistryAIAgent, RegistryAIModel,
)
from app.modules.workflow_scheduler.models import (
    ApprovalGroup, ApprovalGroupMember, Phase2WorkflowSchedule,
    WorkflowScheduleAgentAssignment, WorkflowScheduleApproval,
)
from app.modules.workflow_execution.models import WorkflowRun
from app.modules.workflow_notifications.models import WorkflowNotification
from app.modules.auth.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phase2_demo_seed")

DEMO_PREFIX = "DEMO_"
now = datetime.now(timezone.utc)


def _get_or_create(db, model, defaults=None, **filters):
    obj = db.query(model).filter_by(**filters).first()
    if obj:
        return obj, False
    params = {**filters, **(defaults or {})}
    obj = model(**params)
    db.add(obj)
    db.flush()
    return obj, True


def clear_demo_data(db, tenant_id):
    """Remove previously seeded demo rows (idempotent re-runs)."""
    demo_sched_ids = [
        s.id for s in db.query(Phase2WorkflowSchedule)
        .filter(Phase2WorkflowSchedule.schedule_code.like(f"{DEMO_PREFIX}%")).all()
    ]
    if demo_sched_ids:
        db.query(WorkflowRun).filter(WorkflowRun.schedule_id.in_(demo_sched_ids)).delete(synchronize_session=False)
        db.query(WorkflowScheduleApproval).filter(WorkflowScheduleApproval.schedule_id.in_(demo_sched_ids)).delete(synchronize_session=False)
        db.query(WorkflowScheduleAgentAssignment).filter(WorkflowScheduleAgentAssignment.schedule_id.in_(demo_sched_ids)).delete(synchronize_session=False)
        db.query(Phase2WorkflowSchedule).filter(Phase2WorkflowSchedule.id.in_(demo_sched_ids)).delete(synchronize_session=False)
    db.query(WorkflowNotification).filter(WorkflowNotification.title.like(f"{DEMO_PREFIX}%")).delete(synchronize_session=False)
    db.flush()


def seed():
    db = SessionLocal()
    try:
        # ── Foundational registry rows ───────────────────────────────
        dept, _ = _get_or_create(
            db, RegistryDepartment,
            department_code="DEMO_DEPT",
            defaults={"department_name": "AI Governance Office"},
        )
        role, _ = _get_or_create(
            db, RegistryRole,
            role_code="DEMO_ROLE",
            defaults={"role_name": "Governance Member", "role_type": "GOVERNANCE", "permissions_json": {}},
        )

        # Guardian user mirroring the auth admin (so resolve_user_uuid maps id=1 -> this row)
        admin_email = "admin@guardianiq.com"
        auth_admin = db.query(User).filter(User.email == admin_email).first()
        admin_full_name = (auth_admin.name if auth_admin else None) or "Super Admin"
        admin_user, _ = _get_or_create(
            db, GuardianUser, email=admin_email,
            defaults={"full_name": admin_full_name, "department_id": dept.id, "role_id": role.id, "status": "ACTIVE"},
        )

        approver, _ = _get_or_create(
            db, GuardianUser, email="risk.manager@guardianiq.demo",
            defaults={"full_name": "Risk Manager", "department_id": dept.id, "role_id": role.id, "status": "ACTIVE"},
        )

        tenant_id = admin_user.id

        # Workflow / Agent / Model
        wf, _ = _get_or_create(
            db, RegistryWorkflow, workflow_code="DEMO_AI_REVIEW_WF",
            defaults={
                "workflow_name": "AI Recommendation Review",
                "workflow_type": "ASSESSMENT",
                "business_criticality": "HIGH",
                "owner_user_id": admin_user.id,
                "status": "ACTIVE",
                "metadata_json": {},
            },
        )
        wf2, _ = _get_or_create(
            db, RegistryWorkflow, workflow_code="DEMO_COMPLIANCE_WF",
            defaults={
                "workflow_name": "Compliance Audit Pipeline",
                "workflow_type": "AUDIT",
                "business_criticality": "MEDIUM",
                "owner_user_id": admin_user.id,
                "status": "ACTIVE",
                "metadata_json": {},
            },
        )
        agent, _ = _get_or_create(
            db, RegistryAIAgent, agent_code="DEMO_REVIEW_AGENT",
            defaults={
                "agent_name": "Governance Review Agent",
                "agent_type": "REVIEW",
                "execution_mode": "RECOMMEND_ONLY",
                "risk_level": "HIGH",
                "owner_user_id": admin_user.id,
                "status": "ACTIVE",
            },
        )
        model, _ = _get_or_create(
            db, RegistryAIModel, model_code="DEMO_RISK_MODEL",
            defaults={
                "model_name": "Risk Classification Model v2.1",
                "model_type": "CLASSIFICATION",
                "purpose": "Risk classification of AI recommendations",
                "risk_level": "HIGH",
                "owner_user_id": admin_user.id,
                "status": "ACTIVE",
            },
        )

        # Approval group + members
        ag, created_ag = _get_or_create(
            db, ApprovalGroup, name="AI Governance Board",
            defaults={"tenant_id": tenant_id},
        )
        for uid in (admin_user.id, approver.id):
            exists = db.query(ApprovalGroupMember).filter_by(approval_group_id=ag.id, user_id=uid).first()
            if not exists:
                db.add(ApprovalGroupMember(approval_group_id=ag.id, user_id=uid))
        db.flush()

        # ── Clear prior demo rows for clean re-run ───────────────────
        clear_demo_data(db, tenant_id)

        # ── Schedules across every status ────────────────────────────
        schedules_spec = [
            # code, name, workflow, type, status, risk, approval_required, next(+days), last(-days)
            ("DEMO_DAILY_RISK",    "Daily AI Model Risk Review",   wf,  "DAILY",    "ACTIVE",           "HIGH",     False, 1,  1),
            ("DEMO_WEEKLY_AUDIT",  "Weekly Compliance Audit",      wf2, "WEEKLY",   "ACTIVE",           "MEDIUM",   False, 3,  4),
            ("DEMO_FRAUD_SWEEP",   "Critical Fraud Sweep",         wf,  "CRON",     "ACTIVE",           "CRITICAL", False, 1,  1),
            ("DEMO_VENDOR_ASSESS", "Monthly Vendor Assessment",    wf2, "MONTHLY",  "PENDING_APPROVAL", "CRITICAL", True,  None, None),
            ("DEMO_BIAS_REVIEW",   "Quarterly Bias Review",        wf,  "CRON",     "PENDING_APPROVAL", "HIGH",     True,  None, None),
            ("DEMO_INCIDENT_SCAN", "Ad-hoc Incident Scan",         wf,  "MANUAL",   "PAUSED",           "MEDIUM",   False, None, 6),
            ("DEMO_DATA_CLEANUP",  "Legacy Data Cleanup",          wf2, "WEEKLY",   "RETIRED",          "LOW",      False, None, 30),
            ("DEMO_DRIFT_MONITOR", "Experimental Drift Monitor",   wf,  "INTERVAL", "DRAFT",            "LOW",      False, None, None),
        ]

        created_schedules = {}
        for code, name, workflow, stype, status, risk, appr, nxt, last in schedules_spec:
            sched = Phase2WorkflowSchedule(
                id=uuid4(),
                tenant_id=tenant_id,
                workflow_id=workflow.id,
                schedule_code=code,
                schedule_name=name,
                schedule_type=stype,
                cron_expression="0 9 * * *" if stype in ("CRON", "DAILY") else None,
                timezone="Asia/Kolkata",
                next_run_at=(now + timedelta(days=nxt)) if nxt is not None else None,
                last_run_at=(now - timedelta(days=last)) if last is not None else None,
                owner_user_id=admin_user.id,
                owner_department_id=dept.id,
                risk_level=risk,
                approval_required=appr,
                approval_group_id=ag.id if appr else None,
                max_runtime_seconds=3600,
                schedule_status=status,
                created_by=admin_user.id,
                updated_by=admin_user.id,
            )
            db.add(sched)
            db.flush()
            created_schedules[code] = sched

            # Agent assignment for each schedule
            db.add(WorkflowScheduleAgentAssignment(
                id=uuid4(),
                tenant_id=tenant_id,
                schedule_id=sched.id,
                agent_id=agent.id,
                model_id=model.id,
                assignment_role="PRIMARY",
                execution_mode="RECOMMEND_ONLY" if risk in ("HIGH", "CRITICAL") else "READ_ONLY",
                confidence_threshold=85.0,
                allowed_tools_json=["REGISTRY_READ_API", "AUDIT_READ_API"],
                allowed_data_sources_json=[],
                blocked_operations_json=["UPDATE_POLICY", "EXECUTE_EXTERNAL_ACTION"],
                status="ACTIVE",
                created_by=admin_user.id,
                updated_by=admin_user.id,
            ))

            # Pending approval records
            if status == "PENDING_APPROVAL":
                db.add(WorkflowScheduleApproval(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    schedule_id=sched.id,
                    approval_type="ACTIVATION",
                    approval_status="PENDING",
                    approval_group_id=ag.id,
                    submitted_by=admin_user.id,
                    created_by=admin_user.id,
                    updated_by=admin_user.id,
                ))
        db.flush()

        # ── Runs across every status ─────────────────────────────────
        runs_spec = [
            # schedule_code, status, trigger, risk, started(-hrs), duration_ms
            ("DEMO_DAILY_RISK",  "COMPLETED", "SCHEDULED", "HIGH",     26, 42000),
            ("DEMO_DAILY_RISK",  "COMPLETED", "SCHEDULED", "HIGH",     50, 38500),
            ("DEMO_DAILY_RISK",  "RUNNING",   "MANUAL",    "HIGH",     0,  None),
            ("DEMO_WEEKLY_AUDIT","COMPLETED", "SCHEDULED", "MEDIUM",   96, 120000),
            ("DEMO_WEEKLY_AUDIT","QUEUED",    "SCHEDULED", "MEDIUM",   None, None),
            ("DEMO_FRAUD_SWEEP", "FAILED",    "SCHEDULED", "CRITICAL", 5,  9000),
            ("DEMO_FRAUD_SWEEP", "COMPLETED", "API",       "CRITICAL", 29, 51000),
            ("DEMO_INCIDENT_SCAN","CANCELLED","MANUAL",    "MEDIUM",   140, 3000),
            ("DEMO_FRAUD_SWEEP", "RETRY_QUEUED","SCHEDULED","CRITICAL",2, None),
        ]
        run_n = 0
        for code, status, trigger, risk, started_hrs, dur in runs_spec:
            sched = created_schedules[code]
            run_n += 1
            started = (now - timedelta(hours=started_hrs)) if started_hrs is not None else None
            completed = None
            if started and dur and status in ("COMPLETED", "FAILED", "CANCELLED"):
                completed = started + timedelta(milliseconds=dur)
            db.add(WorkflowRun(
                id=uuid4(),
                tenant_id=tenant_id,
                schedule_id=sched.id,
                workflow_id=sched.workflow_id,
                run_code=f"{DEMO_PREFIX}RUN-{run_n:04d}",
                trigger_type=trigger,
                triggered_by_user_id=admin_user.id if trigger in ("MANUAL", "API") else None,
                triggered_by_actor_type="USER" if trigger in ("MANUAL", "API") else "SYSTEM",
                run_status=status,
                started_at=started,
                completed_at=completed,
                duration_ms=dur,
                risk_level=risk,
                summary=f"{status.title()} run for {sched.schedule_name}",
                created_by=admin_user.id,
                updated_by=admin_user.id,
            ))
        db.flush()

        # ── Notifications (varied) ───────────────────────────────────
        notif_spec = [
            ("APPROVAL_REQUIRED", "HIGH",     "UNREAD",       "Approval needed: Monthly Vendor Assessment", "A high-risk schedule is awaiting your approval decision.", "workflow_schedules", created_schedules["DEMO_VENDOR_ASSESS"].id),
            ("RUN_FAILED",        "CRITICAL", "UNREAD",       "Run failed: Critical Fraud Sweep",            "The latest fraud sweep run failed with a connector error.", "workflow_runs", None),
            ("HIGH_RISK_OUTPUT",  "HIGH",     "UNREAD",       "High-risk output detected",                   "An AI run produced an output flagged as high risk.",       "workflow_runs", None),
            ("SLA_BREACH",        "MEDIUM",   "READ",         "SLA warning: Weekly Compliance Audit",        "A scheduled run is approaching its SLA threshold.",        "workflow_schedules", created_schedules["DEMO_WEEKLY_AUDIT"].id),
            ("APPROVAL_REQUIRED", "HIGH",     "READ",         "Approval needed: Quarterly Bias Review",      "A high-risk schedule is awaiting your approval decision.", "workflow_schedules", created_schedules["DEMO_BIAS_REVIEW"].id),
            ("RUN_COMPLETED",     "LOW",      "ACKNOWLEDGED", "Run completed: Daily AI Model Risk Review",    "The daily risk review completed successfully.",            "workflow_runs", None),
        ]
        for ntype, sev, status, title, message, etype, eid in notif_spec:
            read_at = now - timedelta(hours=2) if status in ("READ", "ACKNOWLEDGED") else None
            ack_at = now - timedelta(hours=1) if status == "ACKNOWLEDGED" else None
            db.add(WorkflowNotification(
                id=uuid4(),
                tenant_id=tenant_id,
                recipient_user_id=admin_user.id,
                notification_type=ntype,
                title=f"{DEMO_PREFIX}{title}",
                message=message,
                severity=sev,
                entity_type=etype,
                entity_id=eid,
                status=status,
                read_at=read_at,
                acknowledged_at=ack_at,
                created_by=admin_user.id,
                updated_by=admin_user.id,
            ))

        db.commit()
        logger.info("Phase 2 demo seed complete: %d schedules, %d runs, %d notifications.",
                    len(schedules_spec), len(runs_spec), len(notif_spec))
    except Exception as e:
        db.rollback()
        logger.error("Phase 2 demo seed failed: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
