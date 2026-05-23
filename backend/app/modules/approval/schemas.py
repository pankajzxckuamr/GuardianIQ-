from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.shared.enums.approval_status import ApprovalStatus

class ApprovalBase(BaseModel):
    status: Optional[ApprovalStatus] = ApprovalStatus.PENDING
    comments: Optional[str] = None
    recommendation_id: int
    reviewer_id: Optional[int] = None

class ApprovalCreate(ApprovalBase):
    pass

class ApprovalUpdate(BaseModel):
    status: Optional[ApprovalStatus] = None
    comments: Optional[str] = None
    recommendation_id: Optional[int] = None
    reviewer_id: Optional[int] = None

class ApprovalResponse(ApprovalBase):
    id: int
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
