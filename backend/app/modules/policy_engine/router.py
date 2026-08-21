from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper
from app.modules.policy_engine.service import PolicyService, PolicyVersionService
from app.modules.policy_engine.enums import PolicyStatus, TargetType, VersionStrategy
from app.modules.relationship.models import PolicyBinding

router = APIRouter(prefix="/api/v1/policies", tags=["v1 Policy Engine"])
binding_router = APIRouter(prefix="/api/v1/policy-bindings", tags=["v1 Policy Bindings"])


class RuleDefinition(BaseModel):
    rule_code: str
    name: str
    description: Optional[str] = None
    rule_type: str = "GENERAL"
    target_type: str = "AGENT"
    target_id: str = "*"
    condition_expression: str = "true"
    condition_json: Optional[Dict[str, Any]] = None
    action: str = "DENY"
    severity: str = "MEDIUM"
    execution_order: int = 1
    is_active: bool = True


class PolicyCreateRequest(BaseModel):
    policy_code: str
    name: str
    description: Optional[str] = None
    category: str = "GENERAL"
    enforcement_mode: str = "BLOCKING"
    priority: int = 100
    initial_rules: Optional[List[RuleDefinition]] = None


class DraftVersionCreateRequest(BaseModel):
    changelog: Optional[str] = None
    rules: Optional[List[RuleDefinition]] = None


class PolicyActionRequest(BaseModel):
    reason: Optional[str] = None


class PolicyBindingCreateRequest(BaseModel):
    policy_id: UUID
    target_type: TargetType
    target_id: str
    binding_scope: Optional[str] = "GLOBAL"
    priority: int = 100
    is_mandatory: bool = True
    version_strategy: VersionStrategy = VersionStrategy.LATEST
    pinned_policy_version_id: Optional[UUID] = None
    condition_json: Optional[dict] = None


@router.get("", response_model=StandardResponse[List[dict]])
def list_policies(
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all governance policies for the current tenant."""
    service = PolicyService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    policies = service.list_policies(tenant_id, category, status)
    data = [
        {
            "id": str(p.id),
            "policy_code": p.policy_code,
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "enforcement_mode": p.enforcement_mode,
            "priority": p.priority,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in policies
    ]
    return ResponseHelper.success(message="Policies retrieved successfully", data=data)


@router.post("", response_model=StandardResponse[dict], status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: PolicyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new draft governance policy."""
    service = PolicyService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    initial_rules_data = [r.model_dump() for r in payload.initial_rules] if payload.initial_rules else None
    policy = service.create_policy(
        tenant_id,
        current_user.id,
        payload.model_dump(exclude={"initial_rules"}),
        initial_rules=initial_rules_data,
    )
    return ResponseHelper.success(
        message="Policy created successfully",
        data={"id": str(policy.id), "policy_code": policy.policy_code, "status": policy.status},
    )


@router.get("/{policy_id}", response_model=StandardResponse[dict])
def get_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get policy details by ID."""
    service = PolicyService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    policy = service.get_policy(policy_id, tenant_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return ResponseHelper.success(
        message="Policy retrieved successfully",
        data={
            "id": str(policy.id),
            "policy_code": policy.policy_code,
            "name": policy.name,
            "description": policy.description,
            "category": policy.category,
            "enforcement_mode": policy.enforcement_mode,
            "priority": policy.priority,
            "status": policy.status,
        },
    )


@router.get("/{policy_id}/versions", response_model=StandardResponse[List[dict]])
def list_policy_versions(
    policy_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all version snapshots for a policy."""
    service = PolicyService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    versions = service.list_versions(policy_id, tenant_id)
    data = [
        {
            "id": str(v.id),
            "version_number": v.version_number,
            "status": v.status,
            "changelog": v.changelog,
            "rules_count": v.rules_count,
            "activated_at": v.activated_at.isoformat() if v.activated_at else None,
        }
        for v in versions
    ]
    return ResponseHelper.success(message="Policy versions retrieved successfully", data=data)


@router.post("/{policy_id}/versions", response_model=StandardResponse[dict], status_code=status.HTTP_201_CREATED)
def create_draft_version(
    policy_id: UUID,
    payload: DraftVersionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new draft policy version with rules."""
    version_service = PolicyVersionService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    rules_data = [r.model_dump() for r in payload.rules] if payload.rules else []
    try:
        version = version_service.create_draft_version(
            tenant_id=tenant_id,
            policy_id=policy_id,
            user_id=current_user.id,
            changelog=payload.changelog,
            rules_data=rules_data,
        )
        return ResponseHelper.success(
            message="Draft version created successfully",
            data={"id": str(version.id), "version_number": version.version_number, "status": version.status},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{policy_id}/versions/{version_id}/activate", response_model=StandardResponse[dict])
def activate_policy_version(
    policy_id: UUID,
    version_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate a draft policy version and supersede any previous version."""
    version_service = PolicyVersionService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    try:
        version = version_service.activate_version(
            tenant_id=tenant_id,
            policy_id=policy_id,
            version_id=version_id,
            user_id=current_user.id,
        )
        return ResponseHelper.success(
            message="Policy version activated successfully",
            data={"id": str(version.id), "version_number": version.version_number, "status": version.status},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{policy_id}/suspend", response_model=StandardResponse[dict])
def suspend_policy(
    policy_id: UUID,
    payload: Optional[PolicyActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Suspend a policy from active enforcement."""
    service = PolicyService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    reason = payload.reason if payload else None
    try:
        policy = service.suspend_policy(tenant_id, policy_id, current_user.id, reason=reason)
        return ResponseHelper.success(
            message="Policy suspended successfully",
            data={"id": str(policy.id), "status": policy.status},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{policy_id}/retire", response_model=StandardResponse[dict])
def retire_policy(
    policy_id: UUID,
    payload: Optional[PolicyActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retire a policy permanently."""
    service = PolicyService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    reason = payload.reason if payload else None
    try:
        policy = service.retire_policy(tenant_id, policy_id, current_user.id, reason=reason)
        return ResponseHelper.success(
            message="Policy retired successfully",
            data={"id": str(policy.id), "status": policy.status},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


from app.modules.policy_engine.binding_service import PolicyBindingService


@binding_router.get("", response_model=StandardResponse[List[dict]])
def list_policy_bindings(
    policy_id: Optional[UUID] = None,
    target_type: Optional[TargetType] = None,
    target_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all policy bindings for the current tenant."""
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    query = db.query(PolicyBinding).filter(PolicyBinding.tenant_id == tenant_id)
    if policy_id:
        query = query.filter(PolicyBinding.policy_id == policy_id)
    if target_type:
        query = query.filter(PolicyBinding.target_type == target_type.value)
    if target_id:
        query = query.filter(PolicyBinding.target_id == target_id)
    bindings = query.order_by(PolicyBinding.priority.asc()).all()
    data = [
        {
            "id": str(b.id),
            "policy_id": str(b.policy_id),
            "target_type": b.target_type,
            "target_id": b.target_id,
            "binding_scope": b.binding_scope,
            "priority": b.priority,
            "is_mandatory": b.is_mandatory,
            "version_strategy": b.version_strategy,
            "pinned_policy_version_id": str(b.pinned_policy_version_id) if b.pinned_policy_version_id else None,
            "status": b.status,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in bindings
    ]
    return ResponseHelper.success(message="Policy bindings retrieved successfully", data=data)


@binding_router.post("", response_model=StandardResponse[dict], status_code=status.HTTP_201_CREATED)
def create_policy_binding(
    payload: PolicyBindingCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bind a policy to a target agent, tool, data source, or workflow."""
    binding_service = PolicyBindingService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    try:
        binding = binding_service.create_binding(tenant_id, current_user.id, payload.model_dump())
        return ResponseHelper.success(
            message="Policy bound successfully",
            data={
                "id": str(binding.id),
                "policy_id": str(binding.policy_id),
                "target_type": binding.target_type,
                "target_id": binding.target_id,
                "status": binding.status,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@binding_router.post("/{binding_id}/suspend", response_model=StandardResponse[dict])
def suspend_policy_binding(
    binding_id: UUID,
    payload: Optional[PolicyActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Suspend an active policy binding."""
    binding_service = PolicyBindingService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    reason = payload.reason if payload else None
    try:
        binding = binding_service.suspend_binding(tenant_id, binding_id, current_user.id, reason=reason)
        return ResponseHelper.success(
            message="Policy binding suspended successfully",
            data={"id": str(binding.id), "status": binding.status},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@binding_router.post("/{binding_id}/revoke", response_model=StandardResponse[dict])
def revoke_policy_binding(
    binding_id: UUID,
    payload: Optional[PolicyActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke/deactivate a policy binding."""
    binding_service = PolicyBindingService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    reason = payload.reason if payload else None
    try:
        binding = binding_service.revoke_binding(tenant_id, binding_id, current_user.id, reason=reason)
        return ResponseHelper.success(
            message="Policy binding revoked successfully",
            data={"id": str(binding.id), "status": binding.status},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@binding_router.get("/effective", response_model=StandardResponse[List[dict]])
def get_effective_bindings(
    target_type: TargetType,
    target_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resolve active direct and inherited effective policy bindings for a target."""
    binding_service = PolicyBindingService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    bindings = binding_service.resolve_effective_bindings(tenant_id, target_type.value, target_id)
    data = [
        {
            "id": str(b.id),
            "policy_id": str(b.policy_id),
            "target_type": b.target_type,
            "target_id": b.target_id,
            "priority": b.priority,
            "is_mandatory": b.is_mandatory,
            "version_strategy": b.version_strategy,
            "pinned_policy_version_id": str(b.pinned_policy_version_id) if b.pinned_policy_version_id else None,
            "status": b.status,
        }
        for b in bindings
    ]
    return ResponseHelper.success(message="Effective bindings resolved successfully", data=data)

