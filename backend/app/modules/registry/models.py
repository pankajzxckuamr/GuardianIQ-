from uuid import uuid4
from sqlalchemy import Column, String, Boolean, Text, TIMESTAMP, Numeric, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.session import Base

class GuardianUser(Base):
    __tablename__ = "guardian_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False)
    
    full_name = Column(String(200), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("registry_departments.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("registry_roles.id"), nullable=False)
    approval_limit_level = Column(String(50), nullable=True)
    status = Column(String(30), default='ACTIVE')
    last_login_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())

class RegistryRole(Base):
    __tablename__ = "registry_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    role_code = Column(String(50), unique=True, nullable=False)
    role_name = Column(String(150), nullable=False)
    role_type = Column(String(50), nullable=False)
    permissions_json = Column(JSONB, nullable=False, default={})
    status = Column(String(30), default='ACTIVE')
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())

class RegistryDepartment(Base):
    __tablename__ = "registry_departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    department_code = Column(String(50), unique=True, nullable=False)
    department_name = Column(String(150), nullable=False)
    parent_department_id = Column(UUID(as_uuid=True), ForeignKey("registry_departments.id"), nullable=True)
    business_owner_user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"), nullable=True)
    escalation_owner_user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"), nullable=True)
    status = Column(String(30), default='ACTIVE')
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

class RegistryDataSource(Base):
    __tablename__ = "registry_data_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_code = Column(String(80), unique=True, nullable=False)
    source_name = Column(String(200), nullable=False)
    source_type = Column(String(80), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"))
    department_id = Column(UUID(as_uuid=True), ForeignKey("registry_departments.id"))
    classification = Column(String(80), nullable=False)
    sensitivity_level = Column(String(50), nullable=False)
    region = Column(String(80), nullable=True)
    contains_pii = Column(Boolean, default=False)
    retention_policy = Column(String(200), nullable=True)
    connection_reference = Column(String(500), nullable=True)
    status = Column(String(30), default='ACTIVE')
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

class RegistryAIModelProvider(Base):
    __tablename__ = "registry_ai_model_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_type = Column(String(80), nullable=False)
    provider_name = Column(String(200), nullable=False)
    provider_category = Column(String(80), nullable=True)
    ownership_type = Column(String(80), nullable=True)
    hosting_type = Column(String(80), nullable=True)
    data_residency = Column(String(80), nullable=True)
    risk_classification = Column(String(50), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

class RegistryAIModel(Base):
    __tablename__ = "registry_ai_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    model_code = Column(String(80), unique=True, nullable=False)
    model_name = Column(String(200), nullable=False)
    model_type = Column(String(80), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("registry_ai_model_providers.id"), nullable=True)
    version = Column(String(80), nullable=True)
    purpose = Column(Text, nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"))
    department_id = Column(UUID(as_uuid=True), ForeignKey("registry_departments.id"))
    risk_level = Column(String(50), nullable=False)
    deployment_environment = Column(String(50), nullable=True)
    status = Column(String(30), default='DRAFT')
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    provider = relationship("RegistryAIModelProvider", backref="models")

class RegistryAIAgent(Base):
    __tablename__ = "registry_ai_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_code = Column(String(80), unique=True, nullable=False)
    agent_name = Column(String(200), nullable=False)
    agent_type = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"))
    department_id = Column(UUID(as_uuid=True), ForeignKey("registry_departments.id"))
    execution_mode = Column(String(80), nullable=False)
    risk_level = Column(String(50), nullable=False)
    confidence_threshold = Column(Numeric(5, 2), nullable=True)
    status = Column(String(30), default='DRAFT')
    capabilities_json = Column(JSONB, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

class RegistryTool(Base):
    __tablename__ = "registry_tools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tool_code = Column(String(80), unique=True, nullable=False)
    tool_name = Column(String(200), nullable=False)
    tool_category = Column(String(80), nullable=False)
    access_mode = Column(String(80), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"))
    sensitivity_level = Column(String(50), nullable=False)
    allowed_operations_json = Column(JSONB, nullable=False, default=[])
    endpoint_reference = Column(String(500), nullable=True)
    status = Column(String(30), default='ACTIVE')
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())

class RegistryWorkflow(Base):
    __tablename__ = "registry_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_code = Column(String(80), unique=True, nullable=False)
    workflow_name = Column(String(200), nullable=False)
    workflow_type = Column(String(80), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("registry_departments.id"))
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"))
    description = Column(Text, nullable=True)
    approval_required = Column(Boolean, default=False)
    approver_user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"), nullable=True)
    business_criticality = Column(String(50), nullable=False)
    status = Column(String(30), default='DRAFT')
    steps_json = Column(JSONB, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, default=func.now(), onupdate=func.now())

    approver = relationship("GuardianUser", foreign_keys=[approver_user_id])

class RegistryRelationship(Base):
    __tablename__ = "registry_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_entity_type = Column(String(80), nullable=False)
    source_entity_id = Column(UUID(as_uuid=True), nullable=False)
    relationship_type = Column(String(80), nullable=False)
    target_entity_type = Column(String(80), nullable=False)
    target_entity_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(30), default='ACTIVE')
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)

class RegistryAuditEvent(Base):
    __tablename__ = "registry_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type = Column(String(80), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(String(80), nullable=False)
    changed_by = Column(UUID(as_uuid=True), nullable=True)
    change_summary = Column(Text, nullable=True)
    before_json = Column(JSONB, nullable=True)
    after_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())

class RegistryRegisterAll(Base):
    __tablename__ = "registry_register_all"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("registry_departments.id"), nullable=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("registry_roles.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("guardian_users.id"), nullable=True)
    data_source_id = Column(UUID(as_uuid=True), ForeignKey("registry_data_sources.id"), nullable=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("registry_ai_models.id"), nullable=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("registry_ai_agents.id"), nullable=True)
    tool_id = Column(UUID(as_uuid=True), ForeignKey("registry_tools.id"), nullable=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("registry_workflows.id"), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)

    department = relationship("RegistryDepartment", foreign_keys=[department_id])
    role = relationship("RegistryRole", foreign_keys=[role_id])
    user = relationship("GuardianUser", foreign_keys=[user_id])
    data_source = relationship("RegistryDataSource", foreign_keys=[data_source_id])
    model = relationship("RegistryAIModel", foreign_keys=[model_id])
    agent = relationship("RegistryAIAgent", foreign_keys=[agent_id])
    tool = relationship("RegistryTool", foreign_keys=[tool_id])
    workflow = relationship("RegistryWorkflow", foreign_keys=[workflow_id])

