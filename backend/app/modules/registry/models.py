from uuid import uuid4
from sqlalchemy import Column, String, Boolean, Text, TIMESTAMP, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.mixins import WorkflowBaseMixin, GovernableMixin
from app.modules.auth.models import User

class Tool(Base, GovernableMixin):
    __tablename__ = "tools"
    __object_type__ = "TOOL"
    __name_column__ = "tool_name"

    tool_code = Column(String(80), unique=True, nullable=False)
    tool_name = Column(String(200), nullable=False)
    tool_category = Column(String(80), nullable=False)
    access_mode = Column(String(80), nullable=False)
    sensitivity_level = Column(String(50), nullable=False)
    allowed_operations_json = Column(JSONB, nullable=False, default=[])
    endpoint_reference = Column(String(500), nullable=True)

class Workflow(Base, GovernableMixin):
    __tablename__ = "workflows"
    __object_type__ = "WORKFLOW"
    __name_column__ = "workflow_name"

    workflow_code = Column(String(80), unique=True, nullable=False)
    workflow_name = Column(String(200), nullable=False)
    workflow_type = Column(String(80), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    description = Column(Text, nullable=True)
    approval_required = Column(Boolean, default=False)
    approver_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    business_criticality = Column(String(50), nullable=False)
    steps_json = Column(JSONB, nullable=True)

    approver = relationship("User", foreign_keys=[approver_user_id])

class RegisterAll(Base, WorkflowBaseMixin):
    __tablename__ = "register_all"

    name = Column(String(200), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("ai_models.id"), nullable=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id"), nullable=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=True)

    department = relationship("Department", foreign_keys=[department_id])
    role = relationship("Role", foreign_keys=[role_id])
    user = relationship("User", foreign_keys=[user_id])
    data_source = relationship("DataSource", foreign_keys=[data_source_id])
    model = relationship("AIModel", foreign_keys=[model_id])
    agent = relationship("Agent", foreign_keys=[agent_id])
    tool = relationship("Tool", foreign_keys=[tool_id])
    workflow = relationship("Workflow", foreign_keys=[workflow_id])

# Legacy Registry model aliases for backwards compatibility
from app.modules.department.models import Department as RegistryDepartment
from app.modules.auth.models import User as GuardianUser, Role as RegistryRole
from app.modules.datasource.models import DataSource as RegistryDataSource
from app.modules.ai_model.models import AIModelProvider as RegistryAIModelProvider, AIModel as RegistryAIModel
from app.modules.agent.models import Agent as RegistryAIAgent
from app.modules.relationship.models import GenericRelationship as RegistryRelationship
from app.modules.audit.models import AuditEvent as RegistryAuditEvent

RegistryTool = Tool
RegistryWorkflow = Workflow
RegistryRegisterAll = RegisterAll
