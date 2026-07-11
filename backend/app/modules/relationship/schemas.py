from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class GenericRelationshipBase(BaseModel):
    source_type: str = Field(..., max_length=100)
    source_id: str = Field(..., max_length=255)
    relationship_type: str = Field(..., max_length=100)
    target_type: str = Field(..., max_length=100)
    target_id: str = Field(..., max_length=255)
    relationship_scope: Optional[str] = Field(None, max_length=255)
    scope_json: Optional[dict] = None
    responsibility_type: Optional[str] = Field(None, max_length=100)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class GenericRelationshipCreate(GenericRelationshipBase):
    pass


class GenericRelationshipUpdate(BaseModel):
    relationship_scope: Optional[str] = Field(None, max_length=255)
    scope_json: Optional[dict] = None
    responsibility_type: Optional[str] = Field(None, max_length=100)
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    status: Optional[str] = Field(None, max_length=50)


class GenericRelationshipResponse(GenericRelationshipBase):
    id: UUID
    tenant_id: UUID
    status: str
    approved_by: Optional[UUID] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ObjectResponsibilityBase(BaseModel):
    object_type: str = Field(..., max_length=100)
    object_id: str = Field(..., max_length=255)
    actor_type: str = Field(..., max_length=50)
    actor_id: str = Field(..., max_length=255)
    responsibility_type: str = Field(..., max_length=50)
    is_primary: bool = False
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class ObjectResponsibilityCreate(ObjectResponsibilityBase):
    pass


class ObjectResponsibilityUpdate(BaseModel):
    is_primary: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    status: Optional[str] = Field(None, max_length=50)


class ObjectResponsibilityResponse(ObjectResponsibilityBase):
    id: UUID
    tenant_id: UUID
    status: str
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RelationshipValidationResultResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    request_id: str
    relationship_id: Optional[UUID] = None
    validation_rule_id: str
    validation_status: str
    severity: str
    message: str
    resolution_hint: Optional[str] = None
    payload_json: Optional[dict] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

