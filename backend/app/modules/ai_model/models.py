from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.enums.risk_level import RiskLevel
from sqlalchemy.dialects.postgresql import UUID
from app.shared.mixins import WorkflowBaseMixin, GovernableMixin

class AIModelProvider(Base, WorkflowBaseMixin):
    __tablename__ = "ai_model_providers"

    provider_type = Column(String(80), nullable=False)
    provider_name = Column(String(200), nullable=False)
    provider_category = Column(String(80), nullable=True)
    ownership_type = Column(String(80), nullable=True)
    hosting_type = Column(String(80), nullable=True)
    data_residency = Column(String(80), nullable=True)
    risk_classification = Column(String(50), nullable=True)

class AIModel(Base, GovernableMixin):
    __tablename__ = "ai_models"
    __object_type__ = "AI_MODEL"
    __name_column__ = "model_name"

    model_code = Column(String(80), unique=True, nullable=False)
    model_name = Column(String(200), index=True, nullable=False)
    model_type = Column(String(80), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("ai_model_providers.id"), nullable=True)
    version = Column(String(80), nullable=True)
    purpose = Column(Text, nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, default=RiskLevel.LOW)
    deployment_environment = Column(String(50), nullable=True)
    
    data_source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=True)

    # Relationships
    provider = relationship("AIModelProvider", backref="models")
    owner_department = relationship("Department", backref="ai_models")
    data_source = relationship("DataSource", backref="ai_models")
