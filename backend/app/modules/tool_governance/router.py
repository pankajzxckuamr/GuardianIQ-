from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper
from app.modules.tool_governance.service import ToolGovernanceService
from app.modules.tool_governance.schemas import ToolCapabilityCreate, AgentToolPermissionCreate

router = APIRouter(prefix="/api/v1/tool-governance", tags=["v1 Tool Governance"])


@router.get("/tools/{tool_id}/capabilities", response_model=StandardResponse[List[dict]])
def list_tool_capabilities(
    tool_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all registered capabilities for a tool."""
    service = ToolGovernanceService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    caps = service.list_capabilities(tool_id, tenant_id)
    data = [
        {
            "id": str(c.id),
            "tool_id": str(c.tool_id),
            "capability_name": c.capability_name,
            "description": c.description,
            "access_mode": c.access_mode,
            "requires_approval": c.requires_approval,
            "rate_limit": c.rate_limit,
            "is_backfilled": bool(c.metadata_json and c.metadata_json.get("_backfilled")),
        }
        for c in caps
    ]
    return ResponseHelper.success(message="Tool capabilities retrieved successfully", data=data)


@router.post("/capabilities", response_model=StandardResponse[dict], status_code=status.HTTP_201_CREATED)
def create_tool_capability(
    payload: ToolCapabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a new capability for a tool."""
    service = ToolGovernanceService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    cap = service.add_capability(tenant_id, payload.model_dump())
    return ResponseHelper.success(
        message="Tool capability registered successfully",
        data={"id": str(cap.id), "tool_id": str(cap.tool_id), "capability_name": cap.capability_name},
    )


@router.get("/agents/{agent_id}/permissions", response_model=StandardResponse[List[dict]])
def list_agent_tool_permissions(
    agent_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tool execution permissions assigned to an agent."""
    service = ToolGovernanceService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    perms = service.list_agent_permissions(agent_id, tenant_id)
    data = [
        {
            "id": str(p.id),
            "agent_id": str(p.agent_id),
            "tool_id": str(p.tool_id),
            "capability_id": str(p.capability_id) if p.capability_id else None,
            "permission_level": p.permission_level,
            "require_approval": p.require_approval,
            "is_active": p.is_active,
        }
        for p in perms
    ]
    return ResponseHelper.success(message="Agent tool permissions retrieved successfully", data=data)


@router.post("/permissions", response_model=StandardResponse[dict], status_code=status.HTTP_201_CREATED)
def grant_agent_tool_permission(
    payload: AgentToolPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Grant or update tool permissions for an agent."""
    service = ToolGovernanceService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    perm = service.grant_permission(tenant_id, payload.model_dump())
    return ResponseHelper.success(
        message="Agent tool permission granted successfully",
        data={"id": str(perm.id), "agent_id": str(perm.agent_id), "tool_id": str(perm.tool_id)},
    )
