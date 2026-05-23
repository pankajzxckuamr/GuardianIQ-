from pydantic import BaseModel
from typing import Optional
from app.shared.enums.recommendation_status import RecommendationStatus
from app.shared.enums.risk_level import RiskLevel
from app.shared.enums.source_type import SourceType

class RecommendationBase(BaseModel):
    source_system: str
    source_type: SourceType
    title: str
    risk_score: Optional[int] = None
    risk_level: Optional[RiskLevel] = RiskLevel.LOW
    status: Optional[RecommendationStatus] = RecommendationStatus.NEW
    recommended_action: Optional[str] = None
    agent_id: Optional[int] = None
    policy_id: Optional[int] = None

class RecommendationCreate(RecommendationBase):
    pass

class RecommendationUpdate(BaseModel):
    source_system: Optional[str] = None
    source_type: Optional[SourceType] = None
    title: Optional[str] = None
    risk_score: Optional[int] = None
    risk_level: Optional[RiskLevel] = None
    status: Optional[RecommendationStatus] = None
    recommended_action: Optional[str] = None
    agent_id: Optional[int] = None
    policy_id: Optional[int] = None

class RecommendationResponse(RecommendationBase):
    id: int

    class Config:
        from_attributes = True
