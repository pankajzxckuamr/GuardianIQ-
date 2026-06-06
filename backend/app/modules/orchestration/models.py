from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from app.db.session import Base

class WorkflowExecution(Base):
    __tablename__ = "orchestration_workflow_executions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("registry_workflows.id"), nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    is_dry_run = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    workflow = relationship("RegistryWorkflow", primaryjoin="WorkflowExecution.workflow_id == RegistryWorkflow.id", foreign_keys=[workflow_id])

    @property
    def workflow_name(self):
        return self.workflow.workflow_name if self.workflow else "Unknown Workflow"

class WorkflowSchedule(Base):
    __tablename__ = "orchestration_workflow_schedules"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("registry_workflows.id"), nullable=False)
    cron_expression = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    next_run_at = Column(DateTime, nullable=True)

class ExecutionFinding(Base):
    __tablename__ = "orchestration_execution_findings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("orchestration_workflow_executions.id"), nullable=False)
    severity = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    recommendation_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ExecutionEventLog(Base):
    __tablename__ = "orchestration_execution_event_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("orchestration_workflow_executions.id"), nullable=False)
    event_type = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
