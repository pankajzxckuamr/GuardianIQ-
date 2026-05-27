from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.recommendation.models import Recommendation
from app.modules.recommendation.schemas import RecommendationCreate, RecommendationUpdate, RecommendationResponse
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

@router.post("/", response_model=StandardResponse[RecommendationResponse], status_code=status.HTTP_201_CREATED)
def create_recommendation(recommendation_in: RecommendationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_obj = Recommendation(**recommendation_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return ResponseHelper.success(
        message="Recommendation created successfully",
        data=RecommendationResponse.model_validate(db_obj).model_dump()
    )

@router.get("/", response_model=StandardResponse[List[RecommendationResponse]])
def get_recommendations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    recommendations = db.query(Recommendation).offset(skip).limit(limit).all()
    return ResponseHelper.success(
        message="Recommendations retrieved successfully",
        data=[RecommendationResponse.model_validate(r).model_dump() for r in recommendations]
    )

@router.get("/{recommendation_id}", response_model=StandardResponse[RecommendationResponse])
def get_recommendation(recommendation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_obj = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return ResponseHelper.success(
        message="Recommendation retrieved successfully",
        data=RecommendationResponse.model_validate(db_obj).model_dump()
    )

@router.put("/{recommendation_id}", response_model=StandardResponse[RecommendationResponse])
def update_recommendation(recommendation_id: int, recommendation_in: RecommendationUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_obj = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    update_data = recommendation_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return ResponseHelper.success(
        message="Recommendation updated successfully",
        data=RecommendationResponse.model_validate(db_obj).model_dump()
    )

@router.delete("/{recommendation_id}", response_model=StandardResponse[None])
def delete_recommendation(recommendation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_obj = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    db.delete(db_obj)
    db.commit()
    return ResponseHelper.success(
        message="Recommendation deleted successfully",
        data=None
    )
