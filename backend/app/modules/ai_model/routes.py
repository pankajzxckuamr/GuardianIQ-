from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.ai_model.models import AIModel
from app.modules.ai_model.schemas import AIModelCreate, AIModelUpdate, AIModelResponse
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper

router = APIRouter(prefix="/api/ai-models", tags=["AI Models"])

@router.post("/", response_model=StandardResponse[AIModelResponse], status_code=status.HTTP_201_CREATED)
def create_ai_model(ai_model_in: AIModelCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_obj = AIModel(**ai_model_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return ResponseHelper.success(
        message="AI Model created successfully",
        data=AIModelResponse.model_validate(db_obj).model_dump()
    )

@router.get("/", response_model=StandardResponse[List[AIModelResponse]])
def get_ai_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    models = db.query(AIModel).offset(skip).limit(limit).all()
    return ResponseHelper.success(
        message="AI Models retrieved successfully",
        data=[AIModelResponse.model_validate(m).model_dump() for m in models]
    )

@router.get("/{model_id}", response_model=StandardResponse[AIModelResponse])
def get_ai_model(model_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_obj = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="AI Model not found")
    return ResponseHelper.success(
        message="AI Model retrieved successfully",
        data=AIModelResponse.model_validate(db_obj).model_dump()
    )

@router.put("/{model_id}", response_model=StandardResponse[AIModelResponse])
def update_ai_model(model_id: int, ai_model_in: AIModelUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_obj = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="AI Model not found")
    
    update_data = ai_model_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return ResponseHelper.success(
        message="AI Model updated successfully",
        data=AIModelResponse.model_validate(db_obj).model_dump()
    )

@router.delete("/{model_id}", response_model=StandardResponse[None])
def delete_ai_model(model_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_obj = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="AI Model not found")
    
    db.delete(db_obj)
    db.commit()
    return ResponseHelper.success(
        message="AI Model deleted successfully",
        data=None
    )
