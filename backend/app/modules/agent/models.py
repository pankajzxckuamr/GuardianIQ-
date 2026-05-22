from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.enums.execution_mode import ExecutionMode

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    execution_mode = Column(SQLEnum(ExecutionMode), nullable=False, default=ExecutionMode.APPROVAL_REQUIRED)
    
    ai_model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=True)

    # Relationships
    ai_model = relationship("AIModel", backref="agents")
