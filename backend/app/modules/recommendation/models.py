from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.shared.enums.recommendation_status import RecommendationStatus
from app.shared.enums.risk_level import RiskLevel
from app.shared.enums.source_type import SourceType

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    source_system = Column(String, nullable=False)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    title = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=True)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, default=RiskLevel.LOW)
    status = Column(SQLEnum(RecommendationStatus), nullable=False, default=RecommendationStatus.NEW, index=True)
    recommended_action = Column(String, nullable=True)
    
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=True)

    # Relationships
    agent = relationship("Agent", backref="recommendations")
    policy = relationship("Policy", backref="recommendations")
