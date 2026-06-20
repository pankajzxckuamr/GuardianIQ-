from uuid import UUID
from sqlalchemy.future import select
from app.modules.notifications.adapters import NotificationAdapter, InAppAdapter
from app.modules.workflow_notifications.models import WorkflowNotification
from app.modules.workflow_scheduler.models import ApprovalGroupMember, Phase2WorkflowSchedule
from app.modules.registry.models import GuardianUser, RegistryRole, RegistryDepartment
from app.shared.db_compat import execute_statement, db_flush

class ScheduleNotificationService:
    def __init__(self, adapter: NotificationAdapter = None):
        self.adapter = adapter or InAppAdapter()

    async def notify_approval_required(self, schedule, db):
        recipients = [schedule.owner_user_id]
        if schedule.approval_group_id:
            stmt = select(ApprovalGroupMember.user_id).where(ApprovalGroupMember.approval_group_id == schedule.approval_group_id)
            res = await execute_statement(db, stmt)
            members = res.scalars().all()
            recipients.extend(members)
        
        recipients = list(set([r for r in recipients if r]))

        for user_id in recipients:
            notification = WorkflowNotification(
                recipient_user_id=user_id,
                notification_type='APPROVAL_REQUIRED',
                title=f"Approval required for schedule {schedule.schedule_name}",
                message=f"Schedule {schedule.schedule_code} requires your approval.",
                severity='HIGH',
                entity_type='WORKFLOW_SCHEDULE',
                entity_id=schedule.id,
                status='UNREAD'
            )
            await self.adapter.send(notification, db)
        await db_flush(db)

    async def notify_activation_decision(self, schedule, approval, db):
        status = approval.approval_status
        notif_type = 'ACTIVATION_APPROVED' if status == 'APPROVED' else 'ACTIVATION_REJECTED'
        
        notification = WorkflowNotification(
            recipient_user_id=schedule.owner_user_id,
            notification_type=notif_type,
            title=f"Schedule {schedule.schedule_name} {status}",
            message=f"The activation request for schedule {schedule.schedule_code} was {status.lower()}.",
            severity='MEDIUM',
            entity_type='WORKFLOW_SCHEDULE',
            entity_id=schedule.id,
            status='UNREAD'
        )
        await self.adapter.send(notification, db)
        await db_flush(db)

    async def _get_escalation_owner(self, schedule, db):
        if schedule.metadata_json and schedule.metadata_json.get('escalation_owner_id'):
            return schedule.metadata_json.get('escalation_owner_id')
        if schedule.owner_department_id:
            stmt = select(RegistryDepartment.escalation_owner_user_id).where(RegistryDepartment.id == schedule.owner_department_id)
            res = await execute_statement(db, stmt)
            return res.scalar()
        return None

    async def notify_run_failed(self, run, failure, db):
        stmt = select(Phase2WorkflowSchedule).where(Phase2WorkflowSchedule.id == run.schedule_id)
        res = await execute_statement(db, stmt)
        schedule = res.scalar()
        
        recipients = []
        if schedule:
            recipients.append(schedule.owner_user_id)
            if schedule.metadata_json and schedule.metadata_json.get('escalation_owner_id'):
                recipients.append(schedule.metadata_json.get('escalation_owner_id'))

        recipients = list(set([r for r in recipients if r]))

        for user_id in recipients:
            notification = WorkflowNotification(
                recipient_user_id=user_id,
                notification_type='RUN_FAILED',
                title=f"Workflow Run Failed: {run.run_code}",
                message=f"Run {run.run_code} failed with error: {failure.failure_message}",
                severity='HIGH',
                entity_type='WORKFLOW_RUN',
                entity_id=run.id,
                status='UNREAD'
            )
            await self.adapter.send(notification, db)
        await db_flush(db)

    async def notify_sla_breach(self, run, db):
        stmt = select(Phase2WorkflowSchedule).where(Phase2WorkflowSchedule.id == run.schedule_id)
        res = await execute_statement(db, stmt)
        schedule = res.scalar()

        recipients = []
        if schedule:
            esc_owner = await self._get_escalation_owner(schedule, db)
            if esc_owner:
                recipients.append(esc_owner)

        stmt = select(GuardianUser.id).join(RegistryRole).where(RegistryRole.role_code == 'GOVERNANCE_ADMIN')
        res = await execute_statement(db, stmt)
        gov_admins = res.scalars().all()
        recipients.extend(gov_admins)

        recipients = list(set([r for r in recipients if r]))

        for user_id in recipients:
            notification = WorkflowNotification(
                recipient_user_id=user_id,
                notification_type='SLA_BREACHED',
                title=f"SLA Breach: {run.run_code}",
                message=f"Run {run.run_code} exceeded the maximum allowed runtime.",
                severity='CRITICAL',
                entity_type='WORKFLOW_RUN',
                entity_id=run.id,
                status='UNREAD'
            )
            await self.adapter.send(notification, db)
        await db_flush(db)

    async def notify_high_risk_output(self, run, output, db):
        stmt = select(Phase2WorkflowSchedule).where(Phase2WorkflowSchedule.id == run.schedule_id)
        res = await execute_statement(db, stmt)
        schedule = res.scalar()

        recipients = []
        if schedule:
            recipients.append(schedule.owner_user_id)

        stmt = select(GuardianUser.id).join(RegistryRole).where(RegistryRole.role_code.in_(['RISK_MANAGER', 'COMPLIANCE_OFFICER']))
        res = await execute_statement(db, stmt)
        risk_users = res.scalars().all()
        recipients.extend(risk_users)

        recipients = list(set([r for r in recipients if r]))

        for user_id in recipients:
            notification = WorkflowNotification(
                recipient_user_id=user_id,
                notification_type='HIGH_RISK_OUTPUT',
                title=f"High Risk Output Detected: {run.run_code}",
                message=f"Run {run.run_code} generated a high risk output.",
                severity='CRITICAL',
                entity_type='WORKFLOW_RUN',
                entity_id=run.id,
                status='UNREAD'
            )
            await self.adapter.send(notification, db)
        await db_flush(db)
