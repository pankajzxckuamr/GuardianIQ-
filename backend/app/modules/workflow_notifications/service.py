from uuid import UUID, uuid4
from datetime import datetime, timezone
from app.modules.workflow_notifications.models import WorkflowNotification
from app.shared.db_compat import db_flush

class ScheduleNotificationService:
    @staticmethod
    async def create_notification(
        db,
        tenant_id: UUID,
        recipient_user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        severity: str,
        entity_type: str,
        entity_id: UUID,
        actor_id: UUID = None
    ) -> WorkflowNotification:
        notif = WorkflowNotification(
            id=uuid4(),
            tenant_id=tenant_id,
            recipient_user_id=recipient_user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            severity=severity,
            entity_type=entity_type,
            entity_id=entity_id,
            status="UNREAD",
            created_by=actor_id,
            updated_by=actor_id
        )
        db.add(notif)
        await db_flush(db)
        return notif
