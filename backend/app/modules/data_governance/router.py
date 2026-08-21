from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper
from app.modules.data_governance.service import DataGovernanceService
from app.modules.data_governance.schemas import DataSourceFieldCreate, AgentDataPermissionCreate

router = APIRouter(prefix="/api/v1/data-governance", tags=["v1 Data Governance"])


@router.get("/datasources/{data_source_id}/fields", response_model=StandardResponse[List[dict]])
def list_datasource_fields(
    data_source_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all classified schema fields for a registered data source."""
    service = DataGovernanceService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    fields = service.list_fields(data_source_id, tenant_id)
    data = [
        {
            "id": str(f.id),
            "data_source_id": str(f.data_source_id),
            "field_name": f.field_name,
            "data_type": f.data_type,
            "classification": f.classification,
            "sensitivity_level": f.sensitivity_level,
            "is_pii": f.is_pii,
            "masking_strategy": f.masking_strategy,
            "is_active": f.is_active,
        }
        for f in fields
    ]
    return ResponseHelper.success(message="Data source fields retrieved successfully", data=data)


@router.post("/fields", response_model=StandardResponse[dict], status_code=status.HTTP_201_CREATED)
def create_datasource_field(
    payload: DataSourceFieldCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a new classified field for a data source."""
    service = DataGovernanceService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    field = service.add_field(tenant_id, payload.model_dump())
    return ResponseHelper.success(
        message="Data source field created successfully",
        data={"id": str(field.id), "field_name": field.field_name, "data_source_id": str(field.data_source_id)},
    )


@router.get("/agents/{agent_id}/permissions", response_model=StandardResponse[List[dict]])
def list_agent_data_permissions(
    agent_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List data access permissions assigned to an agent."""
    service = DataGovernanceService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    perms = service.list_agent_permissions(agent_id, tenant_id)
    data = [
        {
            "id": str(p.id),
            "agent_id": str(p.agent_id),
            "data_source_id": str(p.data_source_id),
            "field_id": str(p.field_id) if p.field_id else None,
            "allowed_operations": p.allowed_operations_json,
            "max_classification": p.max_classification,
            "max_sensitivity": p.max_sensitivity,
            "is_active": p.is_active,
        }
        for p in perms
    ]
    return ResponseHelper.success(message="Agent data permissions retrieved successfully", data=data)


@router.post("/permissions", response_model=StandardResponse[dict], status_code=status.HTTP_201_CREATED)
def grant_agent_data_permission(
    payload: AgentDataPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Grant or update data access permissions for an agent."""
    service = DataGovernanceService(db)
    tenant_id = getattr(current_user, "tenant_id", current_user.id)
    perm = service.grant_permission(tenant_id, payload.model_dump())
    return ResponseHelper.success(
        message="Agent data permission granted successfully",
        data={"id": str(perm.id), "agent_id": str(perm.agent_id), "data_source_id": str(perm.data_source_id)},
    )
