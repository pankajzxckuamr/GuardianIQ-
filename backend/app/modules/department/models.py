from sqlalchemy import Column, String, ForeignKey, Integer, CheckConstraint
from app.db.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.shared.mixins import WorkflowBaseMixin, GovernableMixin
from app.modules.workflow_scheduler.models import ApprovalGroup

class Department(Base, GovernableMixin):
    __tablename__ = "departments"
    __object_type__ = "DEPARTMENT"
    __name_column__ = "department_name"

    parent_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    
    department_code = Column(
        String,
        unique=True,
        nullable=False
    )

    department_name = Column(
        String,
        nullable=False
    )

    description = Column(String)

    data_sources = relationship(
        "DataSource",
        back_populates="department"
    )
    
    approval_default_order = Column(Integer, nullable=True)


class DepartmentOwnerAssignment(Base, WorkflowBaseMixin):
    __tablename__ = "department_owner_assignments"
    __table_args__ = (
        CheckConstraint(
            '(owner_user_id IS NOT NULL AND owner_group_id IS NULL) OR '
            '(owner_user_id IS NULL AND owner_group_id IS NOT NULL)',
            name='check_single_owner'
        ),
    )
    
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    owner_group_id = Column(UUID(as_uuid=True), ForeignKey("approval_groups.id", ondelete="SET NULL"), nullable=True)

    department = relationship("Department")
    owner_user = relationship("User", foreign_keys=[owner_user_id])
    owner_group = relationship("ApprovalGroup", foreign_keys=[owner_group_id])

