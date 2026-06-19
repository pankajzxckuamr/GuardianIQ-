from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, TIMESTAMP, ForeignKey, JSON, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.mixins import WorkflowBaseMixin

class WorkflowRun(Base, WorkflowBaseMixin):
    __tablename__ = "workflow_runs"

    schedule_id = Column(UUID(as_uuid=True), ForeignKey("workflow_schedules.id"), nullable=False)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("registry_workflows.id"), nullable=False)
    run_code = Column(String(120), nullable=False)
    trigger_type = Column(String(50), nullable=False)
    triggered_by_user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"), nullable=True)
    triggered_by_actor_type = Column(String(50), server_default="SYSTEM", nullable=True, default="SYSTEM")
    run_status = Column(String(50), server_default="QUEUED", nullable=True, default="QUEUED")
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    duration_ms = Column(BigInteger, nullable=True)
    risk_level = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    context_json = Column(JSON, server_default="{}", nullable=True, default=None)
    result_json = Column(JSON, server_default="{}", nullable=True, default=None)

    # Relationships
    schedule = relationship("Phase2WorkflowSchedule", back_populates="runs")
    workflow = relationship("RegistryWorkflow", foreign_keys=[workflow_id])
    triggered_by_user = relationship("GuardianUser", foreign_keys=[triggered_by_user_id])
    
    steps = relationship("WorkflowRunStep", back_populates="run", cascade="all, delete-orphan")
    outputs = relationship("WorkflowRunOutput", back_populates="run", cascade="all, delete-orphan")
    failures = relationship("WorkflowRunFailure", back_populates="run", cascade="all, delete-orphan")


class WorkflowRunStep(Base, WorkflowBaseMixin):
    __tablename__ = "workflow_run_steps"

    run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    step_code = Column(String(100), nullable=False)
    step_order = Column(Integer, nullable=False)
    step_type = Column(String(100), nullable=True)
    step_status = Column(String(50), server_default="PENDING", nullable=True, default="PENDING")
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    input_json = Column(JSON, server_default="{}", nullable=True, default=None)
    output_json = Column(JSON, server_default="{}", nullable=True, default=None)
    error_message = Column(Text, nullable=True)

    # Relationships
    run = relationship("WorkflowRun", back_populates="steps")
    failures = relationship("WorkflowRunFailure", back_populates="failed_step")


class WorkflowRunOutput(Base, WorkflowBaseMixin):
    __tablename__ = "workflow_run_outputs"

    run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    output_type = Column(String(100), nullable=True)
    severity = Column(String(50), nullable=True)
    risk_score = Column(Numeric(5, 2), nullable=True)
    findings_json = Column(JSON, server_default="[]", nullable=True, default=None)
    recommendations_json = Column(JSON, server_default="[]", nullable=True, default=None)
    evidence_json = Column(JSON, server_default="{}", nullable=True, default=None)
    raw_output_json = Column(JSON, server_default="{}", nullable=True, default=None)
    parse_status = Column(String(50), server_default="PARSED", nullable=True, default="PARSED")

    # Relationships
    run = relationship("WorkflowRun", back_populates="outputs")


class WorkflowRunFailure(Base, WorkflowBaseMixin):
    __tablename__ = "workflow_run_failures"

    run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    failure_type = Column(String(100), nullable=True)
    failure_code = Column(String(100), nullable=True)
    failure_message = Column(Text, nullable=True)
    failed_step_id = Column(UUID(as_uuid=True), ForeignKey("workflow_run_steps.id"), nullable=True)
    retry_count = Column(Integer, server_default="0", nullable=True, default=0)
    max_retries = Column(Integer, server_default="1", nullable=True, default=1)
    escalation_required = Column(Boolean, server_default="FALSE", nullable=True, default=False)
    escalation_sent_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    run = relationship("WorkflowRun", back_populates="failures")
    failed_step = relationship("WorkflowRunStep", back_populates="failures", foreign_keys=[failed_step_id])
