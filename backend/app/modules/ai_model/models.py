from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.enums.risk_level import RiskLevel

class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True, nullable=False)
    model_type = Column(String, nullable=False)
    version = Column(String, nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, default=RiskLevel.LOW)
    status = Column(String, nullable=False, default="ACTIVE")
    
    owner_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)

    # Relationships
    owner_department = relationship("Department", backref="ai_models")
    data_source = relationship("DataSource", backref="ai_models")
