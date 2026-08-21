from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper
from app.modules.agent_boundary.service import AgentBoundaryService
from app.modules.agent_boundary.schemas import AgentRuntimeBoundaryCreate

router = APIRouter(prefix="/api/v1/agent-boundaries", tags=["v1 Agent Boundaries"])


@router.get("", response_model=StandardResponse[List[dict]])
def list_agent_boundaries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all agent runtime boundaries."""
    service = AgentBoundaryService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    boundaries = service.list_boundaries(tenant_id)
    data = [
        {
            "id": str(b.id),
            "agent_id": str(b.agent_id),
            "max_autonomy_level": b.max_autonomy_level,
            "allowed_access_modes": b.allowed_access_modes_json,
            "rate_limit_per_minute": b.rate_limit_per_minute,
            "max_concurrency": b.max_concurrency,
            "allow_sub_agent_spawn": b.allow_sub_agent_spawn,
            "require_approval_threshold": float(b.require_approval_threshold) if b.require_approval_threshold else None,
            "is_active": b.is_active,
        }
        for b in boundaries
    ]
    return ResponseHelper.success(message="Agent boundaries retrieved successfully", data=data)


@router.get("/{agent_id}", response_model=StandardResponse[dict])
def get_agent_boundary(
    agent_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get runtime boundary for a specific agent."""
    service = AgentBoundaryService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    boundary = service.get_boundary(agent_id, tenant_id)
    if not boundary:
        raise HTTPException(status_code=404, detail="Agent boundary not configured")
    return ResponseHelper.success(
        message="Agent boundary retrieved successfully",
        data={
            "id": str(boundary.id),
            "agent_id": str(boundary.agent_id),
            "max_autonomy_level": boundary.max_autonomy_level,
            "allowed_access_modes": boundary.allowed_access_modes_json,
            "rate_limit_per_minute": boundary.rate_limit_per_minute,
            "max_concurrency": boundary.max_concurrency,
            "allow_sub_agent_spawn": boundary.allow_sub_agent_spawn,
            "require_approval_threshold": float(boundary.require_approval_threshold) if boundary.require_approval_threshold else None,
            "is_active": boundary.is_active,
        },
    )


@router.post("", response_model=StandardResponse[dict], status_code=status.HTTP_201_CREATED)
def set_agent_boundary(
    payload: AgentRuntimeBoundaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update runtime boundary for an agent."""
    service = AgentBoundaryService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    boundary = service.set_boundary(tenant_id, payload.model_dump())
    return ResponseHelper.success(
        message="Agent boundary saved successfully",
        data={"id": str(boundary.id), "agent_id": str(boundary.agent_id)},
    )
