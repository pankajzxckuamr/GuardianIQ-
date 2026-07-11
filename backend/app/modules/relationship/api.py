import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.shared.response_utils import ResponseHelper
from app.modules.relationship.schemas import (
    GenericRelationshipCreate, GenericRelationshipUpdate, GenericRelationshipResponse,
    ObjectResponsibilityCreate, ObjectResponsibilityUpdate, ObjectResponsibilityResponse
)
from app.modules.relationship.service import RelationshipService
from app.modules.relationship.responsibility_service import ResponsibilityService
from app.modules.relationship.constants import (
    RelationshipType, LifecycleState, ResponsibilityType, ValidationRuleCategory
)
from app.modules.relationship.audit_service import RelationshipAuditService

router = APIRouter()

def get_tenant_id(current_user):
    # Returns the user's tenant_id, handling the case where it might be on the user object or defaulting to admin
    return current_user.tenant_id if hasattr(current_user, 'tenant_id') and current_user.tenant_id else current_user.id

# --- Constants Endpoints ---
@router.get("/types", summary="Get valid relationship types")
def get_relationship_types(request: Request, current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return ResponseHelper.success(
        data=[t.value for t in RelationshipType],
        message="Relationship types retrieved",
        request_id=request_id
    )

@router.get("/states", summary="Get valid lifecycle states")
def get_lifecycle_states(request: Request, current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return ResponseHelper.success(
        data=[s.value for s in LifecycleState],
        message="Lifecycle states retrieved",
        request_id=request_id
    )

@router.get("/responsibilities/types", summary="Get valid responsibility types")
def get_responsibility_types(request: Request, current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return ResponseHelper.success(
        data=[r.value for r in ResponsibilityType],
        message="Responsibility types retrieved",
        request_id=request_id
    )

@router.get("/validation-rules", summary="Get validation rule categories")
def get_validation_rules(request: Request, current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return ResponseHelper.success(
        data=[r.value for r in ValidationRuleCategory],
        message="Validation rule categories retrieved",
        request_id=request_id
    )


# --- Core Relationship Endpoints ---
@router.get("/")
async def list_relationships(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="per_page"),
    source_type: Optional[str] = None,
    target_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    # We can just query directly here for simplicity
    from sqlalchemy import select, func, and_
    from app.modules.relationship.models import GenericRelationship
    
    conditions = [GenericRelationship.tenant_id == tenant_id]
    if source_type: conditions.append(GenericRelationship.source_type == source_type)
    if target_type: conditions.append(GenericRelationship.target_type == target_type)
    if status: conditions.append(GenericRelationship.status == status)
    
    stmt = select(GenericRelationship).where(and_(*conditions))
    total_stmt = select(func.count()).select_from(GenericRelationship).where(and_(*conditions))
    
    total = db.execute(total_stmt).scalar()
    
    stmt = stmt.order_by(GenericRelationship.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(stmt).scalars().all())
    
    import math
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return ResponseHelper.success(
        data={
            "items": [GenericRelationshipResponse.model_validate(item).model_dump() for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        },
        message="Relationships retrieved",
        request_id=request_id
    )

@router.post("/", summary="Create a relationship")
async def create_relationship(
    request: Request,
    payload: GenericRelationshipCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    # ABAC Check
    from app.modules.authorization.abac_service import check_relationship_modification_access
    subject = {"user_id": current_user.id, "roles": [r.role_code for r in getattr(current_user, "roles", [])], "department_id": current_user.department_id, "tenant_id": tenant_id}
    allowed, reason = await check_relationship_modification_access(subject, payload.source_type, payload.source_id, db)
    if not allowed:
        return ResponseHelper.error(message="Access denied", data={"reason": reason}, status_code=403, request_id=request_id)
        
    service = RelationshipService(db, tenant_id, current_user.id)
    
    rel, errors = await service.create_relationship(request_id, payload)
    
    if errors:
        return ResponseHelper.error(
            message="Validation failed",
            data=errors,
            status_code=400,
            request_id=request_id
        )
        
    db.commit()
    return ResponseHelper.success(
        data=GenericRelationshipResponse.model_validate(rel).model_dump(),
        message="Relationship created",
        request_id=request_id
    )

@router.put("/{id}", summary="Update a relationship")
async def update_relationship(
    request: Request,
    id: uuid.UUID,
    payload: GenericRelationshipUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    # We must fetch the existing relationship to know the source_type/source_id for ABAC
    service = RelationshipService(db, tenant_id, current_user.id)
    existing = service.repo.get_by_id(db, id, tenant_id)
    if not existing:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
        
    from app.modules.authorization.abac_service import check_relationship_modification_access
    subject = {"user_id": current_user.id, "roles": [r.role_code for r in getattr(current_user, "roles", [])], "department_id": current_user.department_id, "tenant_id": tenant_id}
    allowed, reason = await check_relationship_modification_access(subject, existing.source_type, existing.source_id, db)
    if not allowed:
        return ResponseHelper.error(message="Access denied", data={"reason": reason}, status_code=403, request_id=request_id)
        
    rel, errors = await service.update_relationship(request_id, id, payload)
    
    if errors:
        return ResponseHelper.error(
            message="Validation failed",
            data=errors,
            status_code=400,
            request_id=request_id
        )
        
    db.commit()
    return ResponseHelper.success(
        data=GenericRelationshipResponse.model_validate(rel).model_dump(),
        message="Relationship updated",
        request_id=request_id
    )

@router.delete("/{id}", summary="Revoke/Soft delete a relationship")
async def delete_relationship(
    request: Request,
    id: uuid.UUID,
    reason: str = Query(..., description="Reason for revocation"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    service = RelationshipService(db, tenant_id, current_user.id)
    
    success = await service.revoke_relationship(id, reason)
    if not success:
        return ResponseHelper.error(message="Relationship not found or could not be revoked", status_code=404, request_id=request_id)
        
    db.commit()
    return ResponseHelper.success(message="Relationship revoked", request_id=request_id)

@router.post("/{id}/suspend", summary="Suspend a relationship")
async def suspend_relationship(
    request: Request,
    id: uuid.UUID,
    reason: str = Query(..., description="Reason for suspension"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    service = RelationshipService(db, tenant_id, current_user.id)
    
    success = await service.suspend_relationship(id, reason)
    if not success:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
        
    db.commit()
    return ResponseHelper.success(message="Relationship suspended", request_id=request_id)

@router.post("/{id}/approve", summary="Approve a relationship")
async def approve_relationship(
    request: Request,
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    service = RelationshipService(db, tenant_id, current_user.id)
    
    success = await service.approve_relationship(id)
    if not success:
        return ResponseHelper.error(message="Relationship not found or invalid state", status_code=404, request_id=request_id)
        
    db.commit()
    return ResponseHelper.success(message="Relationship approved", request_id=request_id)

@router.post("/{id}/activate", summary="Activate a relationship")
async def activate_relationship(
    request: Request,
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    service = RelationshipService(db, tenant_id, current_user.id)
    
    success = await service.activate_relationship(id)
    if not success:
        return ResponseHelper.error(message="Relationship not found or invalid state", status_code=404, request_id=request_id)
        
    db.commit()
    return ResponseHelper.success(message="Relationship activated", request_id=request_id)

# --- Responsibility Endpoints ---
@router.post("/responsibilities", summary="Assign responsibility")
async def assign_responsibility(
    request: Request,
    payload: ObjectResponsibilityCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    from app.modules.authorization.abac_service import check_relationship_modification_access
    subject = {"user_id": current_user.id, "roles": [r.role_code for r in getattr(current_user, "roles", [])], "department_id": current_user.department_id, "tenant_id": tenant_id}
    allowed, reason = await check_relationship_modification_access(subject, payload.object_type, payload.object_id, db)
    if not allowed:
        return ResponseHelper.error(message="Access denied", data={"reason": reason}, status_code=403, request_id=request_id)
        
    service = ResponsibilityService(db, tenant_id, current_user.id)
    
    resp = await service.assign_responsibility(payload)
    db.commit()
    return ResponseHelper.success(
        data=ObjectResponsibilityResponse.model_validate(resp).model_dump(),
        message="Responsibility assigned",
        request_id=request_id
    )

@router.get("/responsibilities/{object_type}/{object_id}", summary="Get responsibilities for object")
async def get_responsibilities(
    request: Request,
    object_type: str,
    object_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    service = ResponsibilityService(db, tenant_id, current_user.id)
    
    resps = service.get_responsibilities_for_object(object_type, object_id)
    return ResponseHelper.success(
        data=[ObjectResponsibilityResponse.model_validate(r).model_dump() for r in resps],
        message="Responsibilities retrieved",
        request_id=request_id
    )

# --- Graph & Impact Endpoints ---
@router.get("/graph/{object_type}/{object_id}", summary="Get relationship graph")
async def get_relationship_graph(
    request: Request,
    object_type: str,
    object_id: str,
    depth: int = Query(2, ge=1, le=5),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    # Audit log the context build and traversal
    audit = RelationshipAuditService(db, current_user.id)
    await audit.publish_governance_context_built(object_type, uuid.UUID(object_id) if len(object_id) == 36 else None)
    await audit.publish_graph_traversal(object_type, uuid.UUID(object_id) if len(object_id) == 36 else None, depth)
    
    service = RelationshipService(db, tenant_id, current_user.id)
    # Simple direct retrieval for MVP graph
    outgoing = service.search_relationships(source_type=object_type, source_id=object_id)
    incoming = service.repo.find_reverse(db, tenant_id, target_type=object_type, target_id=object_id)
    
    db.commit() # To save audit events
    return ResponseHelper.success(
        data={
            "root": {"type": object_type, "id": object_id},
            "outgoing": [GenericRelationshipResponse.model_validate(r).model_dump() for r in outgoing],
            "incoming": [GenericRelationshipResponse.model_validate(r).model_dump() for r in incoming]
        },
        message="Graph retrieved",
        request_id=request_id
    )

@router.get("/impact/{object_type}/{object_id}", summary="Get impact analysis")
async def get_impact_analysis(
    request: Request,
    object_type: str,
    object_id: str,
    change_type: str = Query("UPDATE"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    audit = RelationshipAuditService(db, current_user.id)
    await audit.publish_impact_analysis(object_type, uuid.UUID(object_id) if len(object_id) == 36 else None, 1, change_type)
    
    service = RelationshipService(db, tenant_id, current_user.id)
    incoming = service.repo.find_reverse(db, tenant_id, target_type=object_type, target_id=object_id)
    
    db.commit()
    return ResponseHelper.success(
        data={
            "root": {"type": object_type, "id": object_id},
            "impacted_dependents": [GenericRelationshipResponse.model_validate(r).model_dump() for r in incoming]
        },
        message="Impact analysis retrieved",
        request_id=request_id
    )
