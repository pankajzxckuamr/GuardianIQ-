from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.db.session import get_db
from app.modules.approval.models import Approval
from app.modules.approval.schemas import ApprovalCreate, ApprovalUpdate, ApprovalResponse
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])

@router.post("/", response_model=StandardResponse[ApprovalResponse], status_code=status.HTTP_201_CREATED)
def create_approval(approval_in: ApprovalCreate, db: Session = Depends(get_db)):
    db_obj = Approval(**approval_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return ResponseHelper.success(
        message="Approval created successfully",
        data=ApprovalResponse.model_validate(db_obj).model_dump()
    )

@router.get("/", response_model=StandardResponse[List[ApprovalResponse]])
def get_approvals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    approvals = db.query(Approval).offset(skip).limit(limit).all()
    return ResponseHelper.success(
        message="Approvals retrieved successfully",
        data=[ApprovalResponse.model_validate(a).model_dump() for a in approvals]
    )

@router.get("/{approval_id}", response_model=StandardResponse[ApprovalResponse])
def get_approval(approval_id: int, db: Session = Depends(get_db)):
    db_obj = db.query(Approval).filter(Approval.id == approval_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Approval not found")
    return ResponseHelper.success(
        message="Approval retrieved successfully",
        data=ApprovalResponse.model_validate(db_obj).model_dump()
    )

@router.put("/{approval_id}", response_model=StandardResponse[ApprovalResponse])
def update_approval(approval_id: int, approval_in: ApprovalUpdate, db: Session = Depends(get_db)):
    db_obj = db.query(Approval).filter(Approval.id == approval_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    update_data = approval_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    # Update reviewed_at automatically on update (simplified logic)
    db_obj.reviewed_at = datetime.now(timezone.utc)
        
    db.commit()
    db.refresh(db_obj)
    return ResponseHelper.success(
        message="Approval updated successfully",
        data=ApprovalResponse.model_validate(db_obj).model_dump()
    )

@router.delete("/{approval_id}", response_model=StandardResponse[None])
def delete_approval(approval_id: int, db: Session = Depends(get_db)):
    db_obj = db.query(Approval).filter(Approval.id == approval_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    db.delete(db_obj)
    db.commit()
    return ResponseHelper.success(
        message="Approval deleted successfully",
        data=None
    )
