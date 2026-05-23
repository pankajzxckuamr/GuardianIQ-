from pydantic import BaseModel
from typing import Optional
from app.shared.enums.risk_level import RiskLevel

class AIModelBase(BaseModel):
    model_name: str
    model_type: str
    version: str
    risk_level: Optional[RiskLevel] = RiskLevel.LOW
    status: Optional[str] = "ACTIVE"
    owner_department_id: Optional[int] = None
    data_source_id: Optional[int] = None

class AIModelCreate(AIModelBase):
    pass

class AIModelUpdate(BaseModel):
    model_name: Optional[str] = None
    model_type: Optional[str] = None
    version: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    status: Optional[str] = None
    owner_department_id: Optional[int] = None
    data_source_id: Optional[int] = None

class AIModelResponse(AIModelBase):
    id: int

    class Config:
        from_attributes = True
