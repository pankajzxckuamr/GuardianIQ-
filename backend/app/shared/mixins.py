from uuid import uuid4
from sqlalchemy import Column, ForeignKey, TIMESTAMP, Integer, Boolean, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr

class TenantMixin:
    @declared_attr
    def tenant_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"), nullable=False)

class TimestampMixin:
    @declared_attr
    def created_by(cls):
        return Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"), nullable=True)

    @declared_attr
    def updated_by(cls):
        return Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

class WorkflowBaseMixin(TenantMixin, TimestampMixin):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, server_default=func.gen_random_uuid())
    version_no = Column(Integer, server_default="1", default=1, nullable=True)
    is_deleted = Column(Boolean, server_default="FALSE", default=False, nullable=True)
    metadata_json = Column(JSON, server_default="{}", default=None, nullable=True)
