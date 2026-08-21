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
@router.get("")
async def list_relationships(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="per_page"),
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    relationship_type: Optional[str] = None,
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
    if source_type:
        st_norm = source_type.lower()
        if st_norm in {"agent", "agents", "ai_agent", "ai_agents"}:
            conditions.append(func.lower(GenericRelationship.source_type).in_(["agent", "agents", "ai_agent", "ai_agents"]))
        elif st_norm in {"model", "models", "ai_model", "ai_models"}:
            conditions.append(func.lower(GenericRelationship.source_type).in_(["model", "models", "ai_model", "ai_models"]))
        elif st_norm in {"tool", "tools"}:
            conditions.append(func.lower(GenericRelationship.source_type).in_(["tool", "tools"]))
        elif st_norm in {"workflow", "workflows"}:
            conditions.append(func.lower(GenericRelationship.source_type).in_(["workflow", "workflows"]))
        elif st_norm in {"datasource", "data_source", "data_sources"}:
            conditions.append(func.lower(GenericRelationship.source_type).in_(["datasource", "data_source", "data_sources"]))
        elif st_norm in {"department", "departments"}:
            conditions.append(func.lower(GenericRelationship.source_type).in_(["department", "departments"]))
        elif st_norm in {"user", "users"}:
            conditions.append(func.lower(GenericRelationship.source_type).in_(["user", "users"]))
        elif st_norm in {"role", "roles"}:
            conditions.append(func.lower(GenericRelationship.source_type).in_(["role", "roles"]))
        else:
            conditions.append(func.lower(GenericRelationship.source_type) == st_norm)

    if source_id:
        conditions.append(GenericRelationship.source_id == str(source_id))

    if target_type:
        tt_norm = target_type.lower()
        if tt_norm in {"agent", "agents", "ai_agent", "ai_agents"}:
            conditions.append(func.lower(GenericRelationship.target_type).in_(["agent", "agents", "ai_agent", "ai_agents"]))
        elif tt_norm in {"model", "models", "ai_model", "ai_models"}:
            conditions.append(func.lower(GenericRelationship.target_type).in_(["model", "models", "ai_model", "ai_models"]))
        elif tt_norm in {"tool", "tools"}:
            conditions.append(func.lower(GenericRelationship.target_type).in_(["tool", "tools"]))
        elif tt_norm in {"workflow", "workflows"}:
            conditions.append(func.lower(GenericRelationship.target_type).in_(["workflow", "workflows"]))
        elif tt_norm in {"datasource", "data_source", "data_sources"}:
            conditions.append(func.lower(GenericRelationship.target_type).in_(["datasource", "data_source", "data_sources"]))
        elif tt_norm in {"department", "departments"}:
            conditions.append(func.lower(GenericRelationship.target_type).in_(["department", "departments"]))
        elif tt_norm in {"user", "users"}:
            conditions.append(func.lower(GenericRelationship.target_type).in_(["user", "users"]))
        elif tt_norm in {"role", "roles"}:
            conditions.append(func.lower(GenericRelationship.target_type).in_(["role", "roles"]))
        else:
            conditions.append(func.lower(GenericRelationship.target_type) == tt_norm)

    if target_id:
        conditions.append(GenericRelationship.target_id == str(target_id))

    if relationship_type:
        rt_norm = relationship_type.upper()
        if rt_norm in {"USES_TOOL", "USES"}:
            conditions.append(func.upper(GenericRelationship.relationship_type).in_(["USES_TOOL", "USES"]))
        elif rt_norm in {"USES_DATA_SOURCE", "USES"}:
            conditions.append(func.upper(GenericRelationship.relationship_type).in_(["USES_DATA_SOURCE", "USES"]))
        elif rt_norm in {"USES_MODEL", "USES"}:
            conditions.append(func.upper(GenericRelationship.relationship_type).in_(["USES_MODEL", "USES"]))
        else:
            conditions.append(func.upper(GenericRelationship.relationship_type) == rt_norm)

    if status:
        conditions.append(func.upper(GenericRelationship.status) == status.upper())
    
    stmt = select(GenericRelationship).where(and_(*conditions))
    total_stmt = select(func.count()).select_from(GenericRelationship).where(and_(*conditions))
    
    total = db.execute(total_stmt).scalar()
    
    stmt = stmt.order_by(GenericRelationship.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list(db.execute(stmt).scalars().all())
    
    import math
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    items_data = []
    from app.modules.relationship.models import ObjectResponsibility
    for item in items:
        owner_resp = db.query(ObjectResponsibility).filter(
            ObjectResponsibility.tenant_id == tenant_id,
            func.lower(ObjectResponsibility.object_type) == item.source_type.lower(),
            ObjectResponsibility.object_id == item.source_id,
            ObjectResponsibility.responsibility_type == "OWNER",
            ObjectResponsibility.is_primary == True,
            ObjectResponsibility.status == "ACTIVE"
        ).first()

        resp_type = owner_resp.responsibility_type if owner_resp else None
        resp_user = None
        if owner_resp and (owner_resp.actor_type or "").upper() == "USER":
            resp_user = resolve_entity_name(db, "users", owner_resp.actor_id)

        items_data.append({
            **GenericRelationshipResponse.model_validate(item).model_dump(),
            "source_name": resolve_entity_name(db, item.source_type, item.source_id),
            "target_name": resolve_entity_name(db, item.target_type, item.target_id),
            "responsibility_type": resp_type,
            "responsible_user_name": resp_user
        })

    return ResponseHelper.success(
        data={
            "items": items_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        },
        message="Relationships retrieved",
        request_id=request_id
    )

@router.post("", summary="Create a relationship")
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
        raise HTTPException(status_code=403, detail=reason)
        
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
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().invalidate_tenant(tenant_id)
    return ResponseHelper.success(
        data=GenericRelationshipResponse.model_validate(rel).model_dump(),
        message="Relationship created",
        request_id=request_id
    )

@router.post("/validate", summary="Dry-run validate a relationship payload")
async def validate_relationship(
    request: Request,
    payload: GenericRelationshipCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    from app.modules.relationship.validators import ValidationEngine
    validator = ValidationEngine(db, tenant_id)
    
    validation_results = validator.validate_payload(request_id, payload.model_dump())
    failures = [{"rule_id": r.rule_id, "message": r.message, "severity": r.severity} for r in validation_results if r.status == "FAIL"]
    
    db.commit()
    
    if failures:
        return ResponseHelper.success(
            data={"valid": False, "errors": failures},
            message="Payload validation failed",
            request_id=request_id
        )
    return ResponseHelper.success(
        data={"valid": True, "errors": []},
        message="Payload validation passed",
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
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().invalidate_tenant(tenant_id)
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
    
    existing = service.repo.get_by_id(db, id, tenant_id)
    if not existing:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
        
    from app.modules.authorization.abac_service import check_relationship_modification_access
    subject = {"user_id": current_user.id, "roles": [r.role_code for r in getattr(current_user, "roles", [])], "department_id": current_user.department_id, "tenant_id": tenant_id}
    allowed, err_reason = await check_relationship_modification_access(subject, existing.source_type, existing.source_id, db)
    if not allowed:
        raise HTTPException(status_code=403, detail=err_reason)
        
    success = await service.revoke_relationship(id, reason)
    if not success:
        return ResponseHelper.error(message="Relationship not found or could not be revoked", status_code=404, request_id=request_id)
        
    db.commit()
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().invalidate_tenant(tenant_id)
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
    
    existing = service.repo.get_by_id(db, id, tenant_id)
    if not existing:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
        
    from app.modules.authorization.abac_service import check_relationship_modification_access
    subject = {"user_id": current_user.id, "roles": [r.role_code for r in getattr(current_user, "roles", [])], "department_id": current_user.department_id, "tenant_id": tenant_id}
    allowed, err_reason = await check_relationship_modification_access(subject, existing.source_type, existing.source_id, db)
    if not allowed:
        raise HTTPException(status_code=403, detail=err_reason)
        
    success = await service.suspend_relationship(id, reason)
    if not success:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
        
    db.commit()
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().invalidate_tenant(tenant_id)
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
    
    existing = service.repo.get_by_id(db, id, tenant_id)
    if not existing:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
        
    from app.modules.authorization.abac_service import check_relationship_modification_access
    subject = {"user_id": current_user.id, "roles": [r.role_code for r in getattr(current_user, "roles", [])], "department_id": current_user.department_id, "tenant_id": tenant_id}
    allowed, err_reason = await check_relationship_modification_access(subject, existing.source_type, existing.source_id, db)
    if not allowed:
        raise HTTPException(status_code=403, detail=err_reason)
        
    success = await service.approve_relationship(id)
    if not success:
        return ResponseHelper.error(message="Relationship not found or invalid state", status_code=404, request_id=request_id)
        
    db.commit()
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().invalidate_tenant(tenant_id)
    return ResponseHelper.success(message="Relationship approved", request_id=request_id)


@router.post("/{id}/reject", summary="Reject a relationship approval request")
async def reject_relationship(
    request: Request,
    id: uuid.UUID,
    reason: str = Query(..., description="Reason for rejection"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    service = RelationshipService(db, tenant_id, current_user.id)
    
    existing = service.repo.get_by_id(db, id, tenant_id)
    if not existing:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
        
    from app.modules.authorization.abac_service import check_relationship_modification_access
    subject = {"user_id": current_user.id, "roles": [r.role_code for r in getattr(current_user, "roles", [])], "department_id": current_user.department_id, "tenant_id": tenant_id}
    allowed, err_reason = await check_relationship_modification_access(subject, existing.source_type, existing.source_id, db)
    if not allowed:
        raise HTTPException(status_code=403, detail=err_reason)
        
    success = await service.reject_relationship(id, reason)
    if not success:
        return ResponseHelper.error(message="Relationship not found or invalid state", status_code=404, request_id=request_id)
        
    db.commit()
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().invalidate_tenant(tenant_id)
    return ResponseHelper.success(message="Relationship rejected", request_id=request_id)


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
    
    existing = service.repo.get_by_id(db, id, tenant_id)
    if not existing:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
        
    from app.modules.authorization.abac_service import check_relationship_modification_access
    subject = {"user_id": current_user.id, "roles": [r.role_code for r in getattr(current_user, "roles", [])], "department_id": current_user.department_id, "tenant_id": tenant_id}
    allowed, err_reason = await check_relationship_modification_access(subject, existing.source_type, existing.source_id, db)
    if not allowed:
        raise HTTPException(status_code=403, detail=err_reason)
        
    success = await service.activate_relationship(id)
    if not success:
        return ResponseHelper.error(message="Relationship not found or invalid state", status_code=404, request_id=request_id)
        
    db.commit()
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().invalidate_tenant(tenant_id)
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
        raise HTTPException(status_code=403, detail=reason)
        
    service = ResponsibilityService(db, tenant_id, current_user.id)
    
    resp = await service.assign_responsibility(payload)
    db.commit()
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().invalidate_tenant(tenant_id)
    return ResponseHelper.success(
        data=ObjectResponsibilityResponse.model_validate(resp).model_dump(),
        message="Responsibility assigned",
        request_id=request_id
    )

@router.get("/responsibilities", summary="List responsibilities across tenant")
async def list_tenant_responsibilities(
    request: Request,
    object_type: Optional[str] = None,
    object_id: Optional[str] = None,
    actor_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    responsibility_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    from app.modules.relationship.models import ObjectResponsibility
    from sqlalchemy import and_
    
    conditions = [ObjectResponsibility.tenant_id == tenant_id]
    if object_type: conditions.append(ObjectResponsibility.object_type == object_type)
    if object_id: conditions.append(ObjectResponsibility.object_id == object_id)
    if actor_type: conditions.append(ObjectResponsibility.actor_type == actor_type)
    if actor_id: conditions.append(ObjectResponsibility.actor_id == actor_id)
    if responsibility_type: conditions.append(ObjectResponsibility.responsibility_type == responsibility_type)
    
    resps = db.query(ObjectResponsibility).filter(and_(*conditions)).all()
    return ResponseHelper.success(
        data=[ObjectResponsibilityResponse.model_validate(r).model_dump() for r in resps],
        message="Responsibilities list retrieved",
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
    mapped = []
    for r in resps:
        d = ObjectResponsibilityResponse.model_validate(r).model_dump()
        if (r.actor_type or "").upper() == "USER":
            d["actor_name"] = resolve_entity_name(db, "users", r.actor_id)
        else:
            d["actor_name"] = r.actor_id
        mapped.append(d)

    return ResponseHelper.success(
        data=mapped,
        message="Responsibilities retrieved",
        request_id=request_id
    )

def resolve_entity_name(db: Session, entity_type: str, entity_id: str) -> str:
    try:
        from sqlalchemy import text
        from app.modules.relationship.constants import canonicalize_entity_type, table_for_entity_type
        c_type = canonicalize_entity_type(entity_type)
        table_name = table_for_entity_type(entity_type)

        name_cols = {
            "MODEL": "model_name",
            "AGENT": "agent_name",
            "TOOL": "tool_name",
            "WORKFLOW": "workflow_name",
            "DATA_SOURCE": "source_name",
            "DEPARTMENT": "department_name",
            "USER": "name",
            "ROLE": "role_name"
        }
        col = name_cols.get(c_type, "name")
        res = db.execute(text(f"SELECT {col} FROM {table_name} WHERE id = :id LIMIT 1"), {"id": str(entity_id)})
        val = res.scalar()
        if val:
            return str(val)
    except Exception:
        pass
    return f"{entity_type} ({str(entity_id)[:8]})"

def resolve_entity_status_and_risk(db: Session, entity_type: str, entity_id: str):
    status = "ACTIVE"
    risk_level = "LOW"
    try:
        from sqlalchemy import text
        from app.modules.relationship.constants import canonicalize_entity_type, table_for_entity_type
        table_name = table_for_entity_type(entity_type)

        res = db.execute(text(f"SELECT * FROM {table_name} WHERE id = :id LIMIT 1"), {"id": str(entity_id)})
        row = res.mappings().first()
        if row:
            if "status" in row:
                status = row["status"]
            
            if "risk_level" in row:
                risk_level = row["risk_level"]
            elif "sensitivity_level" in row:
                risk_level = row["sensitivity_level"]
            elif "business_criticality" in row:
                risk_level = row["business_criticality"]
            elif "classification" in row:
                risk_level = row["classification"]
    except Exception:
        pass
    return status, risk_level

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
    
    from app.modules.authorization.abac_service import check_node_read_clearance
    subject = {
        "user_id": current_user.id,
        "roles": [r.role_code for r in getattr(current_user, "roles", [])],
        "department_id": current_user.department_id,
        "tenant_id": tenant_id
    }
    
    # Root clearance check
    if not await check_node_read_clearance(subject, object_type, object_id, db):
        raise HTTPException(status_code=403, detail="Access denied: Insufficient clearance for root object")
        
    # Audit log the context build and traversal
    audit = RelationshipAuditService(db, current_user.id)
    await audit.publish_governance_context_built(object_type, uuid.UUID(object_id) if len(object_id) == 36 else None)
    await audit.publish_graph_traversal(object_type, uuid.UUID(object_id) if len(object_id) == 36 else None, depth)
    
    from app.modules.relationship.cache_service import MemoryCacheService
    cache_key = f"graph:{tenant_id}:{object_type}:{object_id}:{depth}:{current_user.id}"
    cached = MemoryCacheService().get(cache_key)
    if cached:
        return ResponseHelper.success(
            data=cached,
            message="Graph retrieved (cached)",
            request_id=request_id
        )
        
    service = RelationshipService(db, tenant_id, current_user.id)
    
    # Recursive outgoing traversal
    visited_outgoing = set()
    outgoing_relationships = []
    
    async def traverse_outgoing(current_type: str, current_id: str, current_depth: int):
        if current_depth > depth:
            return
        node_key = (current_type.lower(), current_id)
        if node_key in visited_outgoing:
            return
        visited_outgoing.add(node_key)
        
        has_clearance = await check_node_read_clearance(subject, current_type, current_id, db)
        if not has_clearance and current_depth > 1:
            # Non-root nodes without clearance are skipped entirely
            return
            
        rels = service.search_relationships(source_type=current_type, source_id=current_id)
        for r in rels:
            outgoing_relationships.append(r)
            # Only recurse deeper if the target node has clearance
            if await check_node_read_clearance(subject, r.target_type, r.target_id, db):
                await traverse_outgoing(r.target_type, r.target_id, current_depth + 1)
            
    await traverse_outgoing(object_type, object_id, 1)
    
    # Recursive incoming traversal
    visited_incoming = set()
    incoming_relationships = []
    
    async def traverse_incoming(current_type: str, current_id: str, current_depth: int):
        if current_depth > depth:
            return
        node_key = (current_type.lower(), current_id)
        if node_key in visited_incoming:
            return
        visited_incoming.add(node_key)
        
        has_clearance = await check_node_read_clearance(subject, current_type, current_id, db)
        if not has_clearance and current_depth > 1:
            return
            
        rels = service.repo.find_reverse(db, tenant_id, target_type=current_type, target_id=current_id)
        for r in rels:
            incoming_relationships.append(r)
            if await check_node_read_clearance(subject, r.source_type, r.source_id, db):
                await traverse_incoming(r.source_type, r.source_id, current_depth + 1)
            
    await traverse_incoming(object_type, object_id, 1)
    
    seen_outgoing_ids = set()
    outgoing_mapped = []
    for r in outgoing_relationships:
        if r.id in seen_outgoing_ids:
            continue
        seen_outgoing_ids.add(r.id)
        
        has_clear = await check_node_read_clearance(subject, r.target_type, r.target_id, db)
        
        d = GenericRelationshipResponse.model_validate(r).model_dump()
        d["other_entity_type"] = r.target_type
        d["other_entity_id"] = r.target_id
        
        if has_clear:
            d["other_entity_name"] = resolve_entity_name(db, r.target_type, r.target_id)
            other_status, other_risk = resolve_entity_status_and_risk(db, r.target_type, r.target_id)
            d["other_entity_status"] = other_status
            d["other_entity_risk"] = other_risk
        else:
            d["other_entity_name"] = "[REDACTED (Insufficient Clearance)]"
            d["other_entity_status"] = "INACTIVE"
            d["other_entity_risk"] = "HIGH"
            d["metadata_json"] = {}
            d["scope_json"] = {}
            d["relationship_scope"] = None

        d["source_name"] = resolve_entity_name(db, r.source_type, r.source_id)
        d["target_name"] = resolve_entity_name(db, r.target_type, r.target_id)
            
        outgoing_mapped.append(d)

    seen_incoming_ids = set()
    incoming_mapped = []
    for r in incoming_relationships:
        if r.id in seen_incoming_ids:
            continue
        seen_incoming_ids.add(r.id)
        
        has_clear = await check_node_read_clearance(subject, r.source_type, r.source_id, db)
        
        d = GenericRelationshipResponse.model_validate(r).model_dump()
        d["other_entity_type"] = r.source_type
        d["other_entity_id"] = r.source_id
        
        if has_clear:
            d["other_entity_name"] = resolve_entity_name(db, r.source_type, r.source_id)
            other_status, other_risk = resolve_entity_status_and_risk(db, r.source_type, r.source_id)
            d["other_entity_status"] = other_status
            d["other_entity_risk"] = other_risk
        else:
            d["other_entity_name"] = "[REDACTED (Insufficient Clearance)]"
            d["other_entity_status"] = "INACTIVE"
            d["other_entity_risk"] = "HIGH"
            d["metadata_json"] = {}
            d["scope_json"] = {}
            d["relationship_scope"] = None

        d["source_name"] = resolve_entity_name(db, r.source_type, r.source_id)
        d["target_name"] = resolve_entity_name(db, r.target_type, r.target_id)
            
        incoming_mapped.append(d)
        
    # Gather policies & evidence for traversed nodes
    from app.modules.relationship.models import PolicyBinding, EvidenceLink
    from app.modules.relationship.repository import RelationshipRepository
    from sqlalchemy import func
    
    policies_mapped = []
    evidence_mapped = []
    
    all_node_keys = visited_outgoing.union(visited_incoming)
    all_node_keys.add((object_type.lower(), object_id))
    
    for (nt, nid) in all_node_keys:
        if not await check_node_read_clearance(subject, nt, nid, db):
            continue
            
        # Get active policies
        p_bindings = db.query(PolicyBinding).filter(
            PolicyBinding.tenant_id == tenant_id,
            func.lower(PolicyBinding.target_type).in_(RelationshipRepository._normalize_entity_types(nt)),
            PolicyBinding.target_id == nid,
            PolicyBinding.status == "ACTIVE"
        ).all()
        for pb in p_bindings:
            policy_name = ""
            try:
                from sqlalchemy import text
                policy_res = db.execute(text("SELECT policy_name FROM policies WHERE id = :id LIMIT 1"), {"id": pb.policy_id})
                policy_name = policy_res.scalar() or ""
            except Exception:
                policy_name = f"Policy ({str(pb.policy_id)[:8]})"
                
            policies_mapped.append({
                "id": str(pb.id),
                "policy_id": str(pb.policy_id),
                "policy_name": policy_name,
                "target_type": pb.target_type,
                "target_id": pb.target_id,
                "binding_scope": pb.binding_scope,
                "priority": pb.priority,
                "is_mandatory": pb.is_mandatory,
                "status": pb.status
            })
            
        # Get evidence links
        e_links = db.query(EvidenceLink).filter(
            EvidenceLink.tenant_id == tenant_id,
            func.lower(EvidenceLink.target_type).in_(RelationshipRepository._normalize_entity_types(nt)),
            EvidenceLink.target_id == nid
        ).all()
        for el in e_links:
            evidence_name = ""
            try:
                from sqlalchemy import text
                ev_res = db.execute(text("SELECT name FROM audit_events WHERE id = :id LIMIT 1"), {"id": el.evidence_id})
                evidence_name = ev_res.scalar() or ""
            except Exception:
                evidence_name = f"Evidence ({str(el.evidence_id)[:8]})"
                
            evidence_mapped.append({
                "id": str(el.id),
                "evidence_id": str(el.evidence_id),
                "evidence_name": evidence_name,
                "target_type": el.target_type,
                "target_id": el.target_id,
                "link_type": el.link_type,
                "confidence_score": float(el.confidence_score) if el.confidence_score is not None else None,
                "source_system": el.source_system
            })
    
    root_status, root_risk = resolve_entity_status_and_risk(db, object_type, object_id)
    res_data = {
        "root": {
            "type": object_type,
            "id": object_id,
            "name": resolve_entity_name(db, object_type, object_id),
            "status": root_status,
            "risk": root_risk
        },
        "outgoing": outgoing_mapped,
        "incoming": incoming_mapped,
        "policies": policies_mapped,
        "evidence": evidence_mapped
    }
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().set(cache_key, res_data, ttl_seconds=300)
    db.commit() # Save audit events
    return ResponseHelper.success(
        data=res_data,
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
    
    from app.modules.authorization.abac_service import check_node_read_clearance
    subject = {
        "user_id": current_user.id,
        "roles": [r.role_code for r in getattr(current_user, "roles", [])],
        "department_id": current_user.department_id,
        "tenant_id": tenant_id
    }
    
    if not await check_node_read_clearance(subject, object_type, object_id, db):
        return ResponseHelper.error(message="Access denied: Insufficient clearance for root object", status_code=403, request_id=request_id)
        
    audit = RelationshipAuditService(db, current_user.id)
    await audit.publish_impact_analysis(object_type, uuid.UUID(object_id) if len(object_id) == 36 else None, 1, change_type)
    
    from app.modules.relationship.cache_service import MemoryCacheService
    cache_key = f"impact:{tenant_id}:{object_type}:{object_id}:{change_type}:{current_user.id}"
    cached = MemoryCacheService().get(cache_key)
    if cached:
        return ResponseHelper.success(
            data=cached,
            message="Impact analysis retrieved (cached)",
            request_id=request_id
        )
        
    service = RelationshipService(db, tenant_id, current_user.id)
    
    # Recursive impact traversal (incoming dependencies)
    visited_impact = set()
    impact_relationships = []
    
    async def traverse_impact(current_type: str, current_id: str, current_depth: int):
        if current_depth > 5: # standard limit for impact
            return
        node_key = (current_type.lower(), current_id)
        if node_key in visited_impact:
            return
        visited_impact.add(node_key)
        
        if not await check_node_read_clearance(subject, current_type, current_id, db):
            return
            
        rels = service.repo.find_reverse(db, tenant_id, target_type=current_type, target_id=current_id)
        for r in rels:
            impact_relationships.append(r)
            await traverse_impact(r.source_type, r.source_id, current_depth + 1)
            
    await traverse_impact(object_type, object_id, 1)
    
    seen_impact_ids = set()
    incoming_mapped = []
    for r in impact_relationships:
        if r.id in seen_impact_ids:
            continue
        seen_impact_ids.add(r.id)
        
        has_clear = await check_node_read_clearance(subject, r.source_type, r.source_id, db)
        
        d = GenericRelationshipResponse.model_validate(r).model_dump()
        d["other_entity_type"] = r.source_type
        d["other_entity_id"] = r.source_id
        
        if has_clear:
            d["other_entity_name"] = resolve_entity_name(db, r.source_type, r.source_id)
        else:
            d["other_entity_name"] = "[REDACTED (Insufficient Clearance)]"
            d["metadata_json"] = {}
            d["scope_json"] = {}
            d["relationship_scope"] = None
            
        incoming_mapped.append(d)
        
    res_data = {
        "root": {"type": object_type, "id": object_id},
        "impacted_dependents": incoming_mapped
    }
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().set(cache_key, res_data, ttl_seconds=300)
    db.commit()
    return ResponseHelper.success(
        data=res_data,
        message="Impact analysis retrieved",
        request_id=request_id
    )

@router.get("/objects/{object_type}/{object_id}/policies", summary="Resolve applicable policies for an object")
async def resolve_policies(
    request: Request,
    object_type: str,
    object_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    from app.modules.relationship.models import PolicyBinding
    from app.modules.authorization.abac_service import check_node_read_clearance
    
    subject = {
        "user_id": current_user.id,
        "roles": [r.role_code for r in getattr(current_user, "roles", [])],
        "department_id": current_user.department_id,
        "tenant_id": tenant_id
    }
    
    # Check read clearance
    if not await check_node_read_clearance(subject, object_type, object_id, db):
        return ResponseHelper.error(message="Access denied", status_code=403, request_id=request_id)
        
    from app.modules.relationship.cache_service import MemoryCacheService
    cache_key = f"policies:{tenant_id}:{object_type}:{object_id}:{current_user.id}"
    cached = MemoryCacheService().get(cache_key)
    if cached:
        return ResponseHelper.success(data=cached, message="Policies resolved (cached)", request_id=request_id)
        
    p_bindings = db.query(PolicyBinding).filter(
        PolicyBinding.tenant_id == tenant_id,
        PolicyBinding.target_type == object_type.lower(),
        PolicyBinding.target_id == object_id,
        PolicyBinding.status == "ACTIVE"
    ).all()
    
    policies_mapped = []
    for pb in p_bindings:
        policy_name = ""
        try:
            from sqlalchemy import text
            policy_res = db.execute(text("SELECT policy_name FROM policies WHERE id = :id LIMIT 1"), {"id": pb.policy_id})
            policy_name = policy_res.scalar() or ""
        except Exception:
            policy_name = f"Policy ({str(pb.policy_id)[:8]})"
            
        policies_mapped.append({
            "id": str(pb.id),
            "policy_id": str(pb.policy_id),
            "policy_name": policy_name,
            "target_type": pb.target_type,
            "target_id": pb.target_id,
            "binding_scope": pb.binding_scope,
            "priority": pb.priority,
            "is_mandatory": pb.is_mandatory,
            "status": pb.status
        })
        
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().set(cache_key, policies_mapped, ttl_seconds=300)
    return ResponseHelper.success(data=policies_mapped, message="Policies resolved", request_id=request_id)

@router.get("/objects/{object_type}/{object_id}/evidence", summary="Resolve evidence for an object")
async def resolve_evidence(
    request: Request,
    object_type: str,
    object_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    from app.modules.relationship.models import EvidenceLink
    from app.modules.authorization.abac_service import check_node_read_clearance
    
    subject = {
        "user_id": current_user.id,
        "roles": [r.role_code for r in getattr(current_user, "roles", [])],
        "department_id": current_user.department_id,
        "tenant_id": tenant_id
    }
    
    # Check read clearance
    if not await check_node_read_clearance(subject, object_type, object_id, db):
        return ResponseHelper.error(message="Access denied", status_code=403, request_id=request_id)
        
    from app.modules.relationship.cache_service import MemoryCacheService
    cache_key = f"evidence:{tenant_id}:{object_type}:{object_id}:{current_user.id}"
    cached = MemoryCacheService().get(cache_key)
    if cached:
        return ResponseHelper.success(data=cached, message="Evidence resolved (cached)", request_id=request_id)
        
    e_links = db.query(EvidenceLink).filter(
        EvidenceLink.tenant_id == tenant_id,
        EvidenceLink.target_type == object_type.lower(),
        EvidenceLink.target_id == object_id
    ).all()
    
    evidence_mapped = []
    for el in e_links:
        evidence_name = ""
        try:
            from sqlalchemy import text
            ev_res = db.execute(text("SELECT name FROM audit_events WHERE id = :id LIMIT 1"), {"id": el.evidence_id})
            evidence_name = ev_res.scalar() or ""
        except Exception:
            evidence_name = f"Evidence ({str(el.evidence_id)[:8]})"
            
        evidence_mapped.append({
            "id": str(el.id),
            "evidence_id": str(el.evidence_id),
            "evidence_name": evidence_name,
            "target_type": el.target_type,
            "target_id": el.target_id,
            "link_type": el.link_type,
            "confidence_score": float(el.confidence_score) if el.confidence_score is not None else None,
            "source_system": el.source_system
        })
        
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().set(cache_key, evidence_mapped, ttl_seconds=300)
    return ResponseHelper.success(data=evidence_mapped, message="Evidence resolved", request_id=request_id)

@router.get("/lifecycle-states", summary="Get valid lifecycle states")
def get_lifecycle_states_new(request: Request, current_user = Depends(get_current_user)):
    return get_lifecycle_states(request, current_user)

@router.get("/{id}", summary="Get relationship details")
async def get_relationship_details(
    request: Request,
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    service = RelationshipService(db, tenant_id, current_user.id)
    existing = service.repo.get_by_id(db, id, tenant_id)
    if not existing:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
    
    from app.modules.authorization.abac_service import check_node_read_clearance
    subject = {
        "user_id": current_user.id,
        "roles": [r.role_code for r in getattr(current_user, "roles", [])],
        "department_id": current_user.department_id,
        "tenant_id": tenant_id
    }
    if not await check_node_read_clearance(subject, existing.source_type, existing.source_id, db) or \
       not await check_node_read_clearance(subject, existing.target_type, existing.target_id, db):
        return ResponseHelper.error(message="Access denied", status_code=403, request_id=request_id)

    data = {
        **GenericRelationshipResponse.model_validate(existing).model_dump(),
        "source_name": resolve_entity_name(db, existing.source_type, existing.source_id),
        "target_name": resolve_entity_name(db, existing.target_type, existing.target_id)
    }
    return ResponseHelper.success(data=data, message="Relationship details retrieved", request_id=request_id)

@router.post("/{id}/submit", summary="Submit a relationship for approval")
async def submit_relationship(
    request: Request,
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    service = RelationshipService(db, tenant_id, current_user.id)
    
    existing = service.repo.get_by_id(db, id, tenant_id)
    if not existing:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
        
    from app.modules.authorization.abac_service import check_relationship_modification_access
    subject = {"user_id": current_user.id, "roles": [r.role_code for r in getattr(current_user, "roles", [])], "department_id": current_user.department_id, "tenant_id": tenant_id}
    allowed, err_reason = await check_relationship_modification_access(subject, existing.source_type, existing.source_id, db)
    if not allowed:
        raise HTTPException(status_code=403, detail=err_reason)
        
    success = await service.approve_relationship(id)
    if not success:
        return ResponseHelper.error(message="Relationship not found or invalid state transition", status_code=404, request_id=request_id)
        
    db.commit()
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().invalidate_tenant(tenant_id)
    return ResponseHelper.success(message="Relationship submitted for approval", request_id=request_id)

@router.post("/{id}/expire", summary="Manually expire a relationship")
async def expire_relationship(
    request: Request,
    id: uuid.UUID,
    reason: str = Query(..., description="Reason for expiration"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    service = RelationshipService(db, tenant_id, current_user.id)
    
    existing = service.repo.get_by_id(db, id, tenant_id)
    if not existing:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
        
    from app.modules.authorization.abac_service import check_relationship_modification_access
    subject = {"user_id": current_user.id, "roles": [r.role_code for r in getattr(current_user, "roles", [])], "department_id": current_user.department_id, "tenant_id": tenant_id}
    allowed, err_reason = await check_relationship_modification_access(subject, existing.source_type, existing.source_id, db)
    if not allowed:
        raise HTTPException(status_code=403, detail=err_reason)
        
    success = await service.expire_relationship(id, reason)
    if not success:
        return ResponseHelper.error(message="Relationship not found or could not be expired", status_code=404, request_id=request_id)
        
    db.commit()
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().invalidate_tenant(tenant_id)
    return ResponseHelper.success(message="Relationship expired manually", request_id=request_id)

@router.post("/{id}/revoke", summary="Revoke a relationship")
async def revoke_relationship_post(
    request: Request,
    id: uuid.UUID,
    reason: str = Query(..., description="Reason for revocation"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    service = RelationshipService(db, tenant_id, current_user.id)
    
    existing = service.repo.get_by_id(db, id, tenant_id)
    if not existing:
        return ResponseHelper.error(message="Relationship not found", status_code=404, request_id=request_id)
        
    from app.modules.authorization.abac_service import check_relationship_modification_access
    subject = {"user_id": current_user.id, "roles": [r.role_code for r in getattr(current_user, "roles", [])], "department_id": current_user.department_id, "tenant_id": tenant_id}
    allowed, err_reason = await check_relationship_modification_access(subject, existing.source_type, existing.source_id, db)
    if not allowed:
        raise HTTPException(status_code=403, detail=err_reason)
        
    success = await service.revoke_relationship(id, reason)
    if not success:
        return ResponseHelper.error(message="Relationship not found or could not be revoked", status_code=404, request_id=request_id)
        
    db.commit()
    from app.modules.relationship.cache_service import MemoryCacheService
    MemoryCacheService().invalidate_tenant(tenant_id)
    return ResponseHelper.success(message="Relationship revoked", request_id=request_id)

@router.post("/bulk-validate", summary="Bulk validate and optionally commit relationships")
async def bulk_validate_relationships(
    request: Request,
    payloads: List[GenericRelationshipCreate],
    commit: bool = Query(False, description="Whether to commit valid relationships to the database"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    from app.modules.relationship.validators import ValidationEngine
    validator = ValidationEngine(db, tenant_id)
    
    results = []
    has_any_invalid = False
    for i, payload in enumerate(payloads):
        validation_results = validator.validate_payload(request_id, payload.model_dump())
        failures = [{"rule_id": r.rule_id, "message": r.message, "severity": r.severity} for r in validation_results if r.status == "FAIL"]
        is_valid = len(failures) == 0
        if not is_valid:
            has_any_invalid = True
        results.append({
            "index": i,
            "valid": is_valid,
            "errors": failures
        })
        
    if commit:
        if has_any_invalid:
            db.rollback()
            return ResponseHelper.success(
                data=results, 
                message="Bulk validation failed. Transaction rolled back, no records created.",
                request_id=request_id
            )
        else:
            from app.modules.relationship.service import RelationshipService
            service = RelationshipService(db, tenant_id, current_user.id)
            created_ids = []
            for payload in payloads:
                rel, _ = await service.create_relationship(request_id, payload)
                if rel:
                    created_ids.append(str(rel.id))
            db.commit()
            from app.modules.relationship.cache_service import MemoryCacheService
            MemoryCacheService().invalidate_tenant(tenant_id)
            return ResponseHelper.success(
                data={"created_ids": created_ids, "validation": results}, 
                message="Bulk validation succeeded. All records successfully committed.",
                request_id=request_id
            )
            
    db.commit()
    return ResponseHelper.success(data=results, message="Bulk validation completed", request_id=request_id)


@router.get("/objects/{object_type}/{object_id}/owners", summary="Get owners for object")
async def get_object_owners(
    request: Request,
    object_type: str,
    object_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    from app.modules.authorization.abac_service import check_node_read_clearance
    subject = {
        "user_id": current_user.id,
        "roles": [r.role_code for r in getattr(current_user, "roles", [])],
        "department_id": current_user.department_id,
        "tenant_id": tenant_id
    }
    if not await check_node_read_clearance(subject, object_type, object_id, db):
        raise HTTPException(status_code=403, detail="Access denied: Insufficient clearance")
        
    from app.modules.relationship.models import ObjectResponsibility
    resps = db.query(ObjectResponsibility).filter(
        ObjectResponsibility.tenant_id == tenant_id,
        ObjectResponsibility.object_type == object_type.lower(),
        ObjectResponsibility.object_id == object_id,
        ObjectResponsibility.responsibility_type == "OWNER",
        ObjectResponsibility.status == "ACTIVE"
    ).all()
    
    return ResponseHelper.success(
        data=[ObjectResponsibilityResponse.model_validate(r).model_dump() for r in resps],
        message="Object owners retrieved",
        request_id=request_id
    )

@router.get("/objects/{object_type}/{object_id}/approvers", summary="Get approvers for object")
async def get_object_approvers(
    request: Request,
    object_type: str,
    object_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    from app.modules.authorization.abac_service import check_node_read_clearance
    subject = {
        "user_id": current_user.id,
        "roles": [r.role_code for r in getattr(current_user, "roles", [])],
        "department_id": current_user.department_id,
        "tenant_id": tenant_id
    }
    if not await check_node_read_clearance(subject, object_type, object_id, db):
        raise HTTPException(status_code=403, detail="Access denied: Insufficient clearance")
        
    from app.modules.relationship.models import ObjectResponsibility
    resps = db.query(ObjectResponsibility).filter(
        ObjectResponsibility.tenant_id == tenant_id,
        ObjectResponsibility.object_type == object_type.lower(),
        ObjectResponsibility.object_id == object_id,
        ObjectResponsibility.responsibility_type == "APPROVER",
        ObjectResponsibility.status == "ACTIVE"
    ).all()
    
    return ResponseHelper.success(
        data=[ObjectResponsibilityResponse.model_validate(r).model_dump() for r in resps],
        message="Object approvers retrieved",
        request_id=request_id
    )

@router.get("/objects/{object_type}/{object_id}/governance-context", summary="Get aggregate governance context")
async def get_governance_context(
    request: Request,
    object_type: str,
    object_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    tenant_id = get_tenant_id(current_user)
    
    from app.modules.authorization.abac_service import check_node_read_clearance
    subject = {
        "user_id": current_user.id,
        "roles": [r.role_code for r in getattr(current_user, "roles", [])],
        "department_id": current_user.department_id,
        "tenant_id": tenant_id
    }
    
    if not await check_node_read_clearance(subject, object_type, object_id, db):
        raise HTTPException(status_code=403, detail="Access denied: Insufficient clearance")
        
    status, risk = resolve_entity_status_and_risk(db, object_type, object_id)
    
    from app.modules.relationship.models import ObjectResponsibility, PolicyBinding, EvidenceLink
    resps = db.query(ObjectResponsibility).filter(
        ObjectResponsibility.tenant_id == tenant_id,
        ObjectResponsibility.object_type == object_type.lower(),
        ObjectResponsibility.object_id == object_id,
        ObjectResponsibility.status == "ACTIVE"
    ).all()
    
    owners = [ObjectResponsibilityResponse.model_validate(r).model_dump() for r in resps if r.responsibility_type == "OWNER"]
    approvers = [ObjectResponsibilityResponse.model_validate(r).model_dump() for r in resps if r.responsibility_type == "APPROVER"]
    
    p_bindings = db.query(PolicyBinding).filter(
        PolicyBinding.tenant_id == tenant_id,
        PolicyBinding.target_type == object_type.lower(),
        PolicyBinding.target_id == object_id,
        PolicyBinding.status == "ACTIVE"
    ).all()
    policies = []
    for pb in p_bindings:
        policy_name = ""
        try:
            from sqlalchemy import text
            policy_res = db.execute(text("SELECT policy_name FROM policies WHERE id = :id LIMIT 1"), {"id": pb.policy_id})
            policy_name = policy_res.scalar() or ""
        except Exception:
            policy_name = f"Policy ({str(pb.policy_id)[:8]})"
        policies.append({
            "id": str(pb.id),
            "policy_id": str(pb.policy_id),
            "policy_name": policy_name,
            "is_mandatory": pb.is_mandatory,
            "status": pb.status
        })
        
    e_links = db.query(EvidenceLink).filter(
        EvidenceLink.tenant_id == tenant_id,
        EvidenceLink.target_type == object_type.lower(),
        EvidenceLink.target_id == object_id
    ).all()
    evidence = []
    for el in e_links:
        evidence_name = ""
        try:
            from sqlalchemy import text
            ev_res = db.execute(text("SELECT name FROM audit_events WHERE id = :id LIMIT 1"), {"id": el.evidence_id})
            evidence_name = ev_res.scalar() or ""
        except Exception:
            evidence_name = f"Evidence ({str(el.evidence_id)[:8]})"
        evidence.append({
            "id": str(el.id),
            "evidence_id": str(el.evidence_id),
            "evidence_name": evidence_name,
            "link_type": el.link_type,
            "confidence_score": float(el.confidence_score) if el.confidence_score is not None else None,
            "source_system": el.source_system
        })
        
    from app.modules.audit.models import AuditEvent
    from sqlalchemy import or_
    
    entity_id_str = str(object_id)
    where_clause = or_(
        AuditEvent.entity_id == entity_id_str,
        AuditEvent.event_metadata.op("->>")("entity_id") == entity_id_str
    )
    
    from app.modules.auth.models import User as AuthUser
    stmt = (
        db.query(AuditEvent, AuthUser.name, AuthUser.email)
        .outerjoin(AuthUser, AuditEvent.actor_user_id == AuthUser.id)
        .where(where_clause)
        .order_by(AuditEvent.created_at.desc())
        .limit(20)
    )
    
    events_rows = stmt.all()
    audit_events = []
    for event, actor_name, actor_email in events_rows:
        meta = event.event_metadata or {}
        payload = meta.get("payload") if isinstance(meta.get("payload"), dict) else {}
        summary = meta.get("event_summary") or meta.get("change_summary") or f"Action {event.action or event.event_type} on {event.entity_type}"
        
        audit_events.append({
            "id": str(event.id),
            "event_type": event.event_type,
            "changed_by_name": actor_name or "System",
            "change_summary": summary,
            "created_at": event.created_at.isoformat() if event.created_at else None
        })
        
    context = {
        "status": status,
        "risk_level": risk,
        "owners": owners,
        "approvers": approvers,
        "policies": policies,
        "evidence": evidence,
        "audit_events": audit_events
    }
    
    return ResponseHelper.success(data=context, message="Governance context retrieved", request_id=request_id)
