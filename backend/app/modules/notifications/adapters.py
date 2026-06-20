from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.workflow_notifications.models import WorkflowNotification

class NotificationAdapter(ABC):
    @abstractmethod
    async def send(self, notification: WorkflowNotification, db: AsyncSession): ...

class InAppAdapter(NotificationAdapter):
    async def send(self, notification: WorkflowNotification, db: AsyncSession):
        db.add(notification)

class EmailAdapter(NotificationAdapter):
    async def send(self, notification: WorkflowNotification, db: AsyncSession):
        pass  # TODO: implement SMTP/SendGrid when configured
