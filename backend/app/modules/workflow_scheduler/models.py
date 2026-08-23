from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, TIMESTAMP, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.mixins import WorkflowBaseMixin

class ApprovalGroup(Base, WorkflowBaseMixin):
    __tablename__ = "approval_groups"


    name = Column(String(255), nullable=False)

    # Relationships
    schedules = relationship("Phase2WorkflowSchedule", back_populates="approval_group")
    approvals = relationship("WorkflowScheduleApproval", back_populates="approval_group", foreign_keys="[WorkflowScheduleApproval.approval_group_id]")


class Phase2WorkflowSchedule(Base, WorkflowBaseMixin):
    __tablename__ = "workflow_schedules"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'schedule_code', name='uix_tenant_schedule_code'),
        UniqueConstraint('tenant_id', 'schedule_name', name='uix_tenant_schedule_name'),
    )

    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    schedule_code = Column(String(100), nullable=False)
    schedule_name = Column(String(255), nullable=False)
    schedule_type = Column(String(50), nullable=False)
    cron_expression = Column(String(120), nullable=True)
    timezone = Column(String(100), server_default="Asia/Kolkata", nullable=False, default="Asia/Kolkata")
    start_at = Column(TIMESTAMP(timezone=True), nullable=True)
    end_at = Column(TIMESTAMP(timezone=True), nullable=True)
    next_run_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_run_at = Column(TIMESTAMP(timezone=True), nullable=True)
    concurrency_policy = Column(String(50), server_default="SKIP_IF_RUNNING", nullable=True, default="SKIP_IF_RUNNING")
    max_runtime_seconds = Column(Integer, server_default="1800", nullable=True, default=1800)
    retry_policy_json = Column(JSONB, server_default='{"max_retries":1,"retry_delay_seconds":300}', nullable=True, default=None)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    approval_required = Column(Boolean, server_default="FALSE", nullable=True, default=False)
    approval_group_id = Column(UUID(as_uuid=True), ForeignKey("approval_groups.id"), nullable=True)
    risk_level = Column(String(50), server_default="MEDIUM", nullable=True, default="MEDIUM")
    schedule_status = Column(String(50), server_default="DRAFT", nullable=True, default="DRAFT")

    # Relationships
    workflow = relationship("Workflow", foreign_keys=[workflow_id])
    owner_user = relationship("User", foreign_keys=[owner_user_id])
    owner_department = relationship("Department", foreign_keys=[owner_department_id])
    approval_group = relationship("ApprovalGroup", back_populates="schedules")
    
    agent_assignments = relationship(
        "WorkflowScheduleAgentAssignment",
        back_populates="schedule",
        cascade="all, delete-orphan"
    )
    runs = relationship("WorkflowRun", back_populates="schedule")
    approvals = relationship("WorkflowScheduleApproval", back_populates="schedule")
    history = relationship("WorkflowScheduleHistory", back_populates="schedule")


class WorkflowScheduleAgentAssignment(Base, WorkflowBaseMixin):
    __tablename__ = "workflow_schedule_agent_assignments"


    schedule_id = Column(UUID(as_uuid=True), ForeignKey("workflow_schedules.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ai_models.id"), nullable=True)
    assignment_role = Column(String(50), server_default="PRIMARY", nullable=True, default="PRIMARY")
    execution_mode = Column(String(50), server_default="RECOMMEND_ONLY", nullable=True, default="RECOMMEND_ONLY")
    confidence_threshold = Column(Numeric(5, 2), nullable=True)
    allowed_tools_json = Column(JSONB, server_default="[]", nullable=True, default=None)
    allowed_data_sources_json = Column(JSONB, server_default="[]", nullable=True, default=None)
    blocked_operations_json = Column(JSONB, server_default="[]", nullable=True, default=None)
    boundary_rules_json = Column(JSONB, server_default="{}", nullable=True, default=None)
    status = Column(String(50), server_default="ACTIVE", nullable=True, default="ACTIVE")

    # Relationships
    schedule = relationship("Phase2WorkflowSchedule", back_populates="agent_assignments")
    agent = relationship("Agent", foreign_keys=[agent_id])
    model = relationship("AIModel", foreign_keys=[model_id])


class ScheduleApprovalLayerSelection(Base, WorkflowBaseMixin):
    __tablename__ = "schedule_approval_layer_selections"

    schedule_id = Column(UUID(as_uuid=True), ForeignKey("workflow_schedules.id", ondelete="CASCADE"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)
    layer_order = Column(Integer, nullable=False)

    schedule = relationship("Phase2WorkflowSchedule")
    department = relationship("Department")


class WorkflowScheduleApproval(Base, WorkflowBaseMixin):
    __tablename__ = "workflow_schedule_approvals"


    schedule_id = Column(UUID(as_uuid=True), ForeignKey("workflow_schedules.id"), nullable=False)
    approval_cycle_id = Column(UUID(as_uuid=True), nullable=False)
    approval_layer = Column(Integer, nullable=False, server_default="1")
    parent_approval_id = Column(UUID(as_uuid=True), ForeignKey("workflow_schedule_approvals.id"), nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    
    approval_type = Column(String(100), server_default="ACTIVATION", nullable=True, default="ACTIVATION")
    approver_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approval_group_id = Column(UUID(as_uuid=True), ForeignKey("approval_groups.id"), nullable=True)
    approval_status = Column(String(50), server_default="PENDING", nullable=True, default="PENDING")
    decision_reason = Column(Text, nullable=True)
    skip_reason = Column(Text, nullable=True)
    decided_at = Column(TIMESTAMP(timezone=True), nullable=True)
    decided_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    schedule = relationship("Phase2WorkflowSchedule", back_populates="approvals")
    department = relationship("Department", foreign_keys=[department_id])
    parent_approval = relationship("WorkflowScheduleApproval", remote_side="[WorkflowScheduleApproval.id]")
    approver_user = relationship("User", foreign_keys=[approver_user_id])
    approval_group = relationship("ApprovalGroup", back_populates="approvals", foreign_keys=[approval_group_id])
    submitter_user = relationship("User", foreign_keys=[submitted_by])
    decider_user = relationship("User", foreign_keys=[decided_by])


class WorkflowScheduleHistory(Base, WorkflowBaseMixin):
    __tablename__ = "workflow_schedule_history"


    schedule_id = Column(UUID(as_uuid=True), ForeignKey("workflow_schedules.id"), nullable=False)
    change_type = Column(String(100), nullable=True)
    change_summary = Column(Text, nullable=True)
    before_json = Column(JSONB, server_default="{}", nullable=True, default=None)
    after_json = Column(JSONB, server_default="{}", nullable=True, default=None)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    changed_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=True)

    # Relationships
    schedule = relationship("Phase2WorkflowSchedule", back_populates="history")
    changed_by_user = relationship("User", foreign_keys=[changed_by])


class ApprovalGroupMember(Base):
    __tablename__ = "approval_group_members"


    approval_group_id = Column(UUID(as_uuid=True), ForeignKey("approval_groups.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)

    # Relationships
    approval_group = relationship("ApprovalGroup", backref="members")
    user = relationship("User", backref="approval_groups")

