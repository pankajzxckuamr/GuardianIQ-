from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.shared.response_utils import ResponseHelper
from app.modules.registry.constants import EntityStatus

def validate_unique_code(db: Session, table_class, code_field: str, code_value: str, exclude_id: Optional[UUID] = None):
    query = select(table_class).where(getattr(table_class, code_field) == code_value)
    if exclude_id:
        query = query.where(table_class.id != exclude_id)
    
    result = db.execute(query).scalar_one_or_none()
    if result:
        raise HTTPException(
            status_code=409,
            detail=ResponseHelper.error(
                message=f"Code '{code_value}' already exists.",
                error_code="CONFLICT",
                details=[{"field": code_field, "message": "already exists"}]
            ).model_dump()
        )

def validate_entity_exists(db: Session, table_class, entity_id: UUID, entity_name: str):
    if not entity_id:
        return
    
    result = db.execute(select(table_class).filter_by(id=entity_id)).scalar_one_or_none()
    if not result:
        raise HTTPException(
            status_code=422,
            detail=ResponseHelper.error(
                message=f"{entity_name} not found.",
                error_code="VALIDATION_ERROR",
                details=[{"field": entity_name.lower(), "message": "does not exist"}]
            ).model_dump()
        )

def validate_status_transition(current: str, new: str):
    if current == new:
        return
        
    allowed_transitions = {
        EntityStatus.DRAFT: [EntityStatus.ACTIVE, EntityStatus.ARCHIVED],
        EntityStatus.ACTIVE: [EntityStatus.INACTIVE, EntityStatus.RETIRED],
        EntityStatus.INACTIVE: [EntityStatus.ACTIVE, EntityStatus.RETIRED],
        EntityStatus.RETIRED: [EntityStatus.ARCHIVED],
        EntityStatus.SUSPENDED: [EntityStatus.ACTIVE, EntityStatus.RETIRED],
        EntityStatus.ARCHIVED: []
    }
    
    current_enum = EntityStatus(current)
    new_enum = EntityStatus(new)
    
    if new_enum not in allowed_transitions.get(current_enum, []):
        raise HTTPException(
            status_code=400,
            detail=ResponseHelper.error(
                message=f"Invalid status transition from {current} to {new}.",
                error_code="INVALID_STATUS_TRANSITION",
                details=[]
            ).model_dump()
        )

def validate_confidence_threshold(value: Optional[float]):
    if value is not None and not (0 <= value <= 100):
        raise HTTPException(
            status_code=422,
            detail=ResponseHelper.error(
                message="Confidence threshold must be between 0 and 100.",
                error_code="VALIDATION_ERROR",
                details=[{"field": "confidence_threshold", "message": "must be between 0 and 100"}]
            ).model_dump()
        )

FORBIDDEN_PATTERNS = ['password=', 'token=', 'secret=', 'api_key=', 'apikey=', 'pwd=', 'passwd=']

def contains_credentials(value: str) -> bool:
    if not value:
        return False
    return any(p in value.lower() for p in FORBIDDEN_PATTERNS)

def validate_endpoint_reference(endpoint: Optional[str]):
    if endpoint and contains_credentials(endpoint):
        raise HTTPException(
            status_code=422,
            detail=ResponseHelper.error(
                message="Endpoint reference must not contain credentials or secrets",
                error_code="VALIDATION_ERROR",
                details=[{"field": "endpoint_reference", "message": "contains forbidden credential pattern"}]
            ).model_dump()
        )

def validate_steps_json(steps_json: Optional[list]):
    if steps_json is not None:
        if not isinstance(steps_json, list):
            raise HTTPException(
                status_code=422,
                detail=ResponseHelper.error(
                    message="steps_json must be an array",
                    error_code="VALIDATION_ERROR",
                    details=[{"field": "steps_json", "message": "must be an array"}]
                ).model_dump()
            )
        for i, step in enumerate(steps_json):
            if not isinstance(step, dict) or 'step_name' not in step:
                raise HTTPException(
                    status_code=422,
                    detail=ResponseHelper.error(
                        message=f"Step at index {i} must be an object containing a 'step_name' key",
                        error_code="VALIDATION_ERROR",
                        details=[{"field": f"steps_json[{i}]", "message": "missing step_name"}]
                    ).model_dump()
                )

def validate_parent_department(department_id: UUID, parent_department_id: Optional[UUID]):
    if parent_department_id and department_id == parent_department_id:
        raise HTTPException(
            status_code=422,
            detail=ResponseHelper.error(
                message="Department cannot be its own parent",
                error_code="VALIDATION_ERROR",
                details=[{"field": "parent_department_id", "message": "cannot equal department_id"}]
            ).model_dump()
        )

