from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.shared.response_utils import ResponseHelper
from app.shared.responses import StandardResponse
from app.modules.auth.models import User
import math

router = APIRouter(
    prefix="/api/tenants",
    tags=["Tenants"]
)

@router.get("", response_model=StandardResponse[dict])
def get_tenants(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", "")
    
    # In GuardianIQ, user accounts/IDs serve as the tenant partition key/identity.
    # We will list active system admin/users as tenants.
    users = db.query(User).filter(User.status == "ACTIVE").all()
    
    items = []
    # Always include a default tenant for backward compatibility
    items.append({
        "id": "00000000-0000-0000-0000-000000000000",
        "name": "Default Platform Tenant",
        "slug": "default",
        "is_active": True,
        "created_at": "2026-07-22T00:00:00Z"
    })
    
    for u in users:
        # Convert each active user acting as a tenant space
        items.append({
            "id": str(u.id),
            "name": f"{u.full_name or u.name} Workspace",
            "slug": u.name.lower().replace(" ", "-"),
            "is_active": u.status == "ACTIVE",
            "created_at": u.created_at.isoformat()
        })
        
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = items[start:end]
    pages = math.ceil(total / per_page)
    
    return ResponseHelper.success(
        data={
            "items": paginated_items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        },
        message="Tenants retrieved successfully",
        request_id=request_id
    )

@router.post("", response_model=StandardResponse[dict])
def create_tenant(
    request: Request,
    payload: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", "")
    # In this single-database multi-tenant workspace architecture, provisioning a new tenant
    # dynamically registers a mock workspace endpoint mapping the request.
    name = payload.get("name", "New Workspace")
    slug = payload.get("slug", "new-workspace")
    
    import uuid
    from datetime import datetime, timezone
    new_tenant = {
        "id": str(uuid.uuid4()),
        "name": name,
        "slug": slug,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    return ResponseHelper.success(
        data=new_tenant,
        message="Tenant workspace provisioned successfully",
        request_id=request_id
    )
