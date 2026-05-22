from typing import Optional
from pydantic import BaseModel
from app.shared.enums.policy_status import PolicyStatus
from app.shared.enums.risk_level import RiskLevel


class PolicyCreate(BaseModel):
    policy_name: str

    policy_type: str

    severity: RiskLevel

    status: PolicyStatus

    conditions: Optional[list] = None

    actions: Optional[list] = None

    created_by: Optional[int] = None


class PolicyResponse(BaseModel):
    id: int

    policy_name: str

    policy_type: str

    severity: str

    status: str

    conditions: Optional[list]

    actions: Optional[list]

    created_by: Optional[int]

    class Config:
        from_attributes = True
