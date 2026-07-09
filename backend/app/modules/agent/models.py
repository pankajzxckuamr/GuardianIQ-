from sqlalchemy import Column, String, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.mixins import GovernableMixin

class Agent(Base, GovernableMixin):
    __tablename__ = "agents"
    __object_type__ = "AGENT"
    __name_column__ = "agent_name"

    agent_code = Column(String(80), unique=True, nullable=False)
    agent_name = Column(String(200), index=True, nullable=False)
    agent_type = Column(String(80), nullable=False)
    description = Column(Text, nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    execution_mode = Column(String(80), nullable=False)
    risk_level = Column(String(50), nullable=False)
    confidence_threshold = Column(Numeric(5, 2), nullable=True)
    capabilities_json = Column(JSONB, nullable=True)
    
    ai_model_id = Column(UUID(as_uuid=True), ForeignKey("ai_models.id"), nullable=True)

    # Relationships
    ai_model = relationship("AIModel", backref="agents")
