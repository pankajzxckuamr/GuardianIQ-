from typing import Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session
import math

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.shared.response_utils import ResponseHelper
from app.shared.responses import StandardResponse
from app.modules.registry import schemas, services
from app.modules.registry import repositories as repo

models_router = APIRouter()
agents_router = APIRouter()
tools_router = APIRouter()
workflows_router = APIRouter()
summary_router = APIRouter()
departments_router = APIRouter()
roles_router = APIRouter()
users_router = APIRouter()
data_sources_router = APIRouter()
relationships_router = APIRouter()
audit_router = APIRouter()
search_router = APIRouter()

def require_read_roles(current_user, request_id: str):
    if current_user.role_code not in ["ADMIN", "GOVERNANCE_MANAGER", "REVIEWER", "AUDITOR"]:
        raise HTTPException(403, detail=ResponseHelper.error(
            message="Insufficient permission", error_code="FORBIDDEN", request_id=request_id
        ).model_dump())

def require_write_roles(current_user, request_id: str):
    if current_user.role_code not in ["ADMIN", "GOVERNANCE_MANAGER"]:
        raise HTTPException(403, detail=ResponseHelper.error(
            message="Insufficient permission", error_code="FORBIDDEN", request_id=request_id
        ).model_dump())

# ---------------------------------------------------------
# Models Endpoints
# ---------------------------------------------------------

@models_router.get("/models", summary="List AI Models", description="Retrieve a paginated list of registered AI Models.")
def list_models(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    model_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    department_id: Optional[UUID] = None,
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    
    filters = {
        "search": search,
        "status": status,
        "model_type": model_type,
        "risk_level": risk_level,
        "department_id": department_id
    }
    
    items, total = repo.list_models(db, filters, page, page_size, sort_by, sort_dir)
    
    response_data = schemas.AIModelListResponse(
        items=[schemas.AIModelResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        has_next=page < (math.ceil(total / page_size) if total > 0 else 0),
        has_prev=page > 1
    )
    
    return ResponseHelper.success(
        data=response_data.model_dump(),
        message="Models retrieved successfully",
        request_id=request_id
    )

@models_router.post("/models", summary="Create AI Model", description="Register a new AI Model. Allowed roles: ADMIN, GOVERNANCE_MANAGER", response_model=StandardResponse)
def create_model(
    request: Request,
    payload: schemas.AIModelCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    model = services.create_model(db, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.AIModelResponse.model_validate(model).model_dump(),
        message="AI Model created successfully",
        request_id=request_id
    )

@models_router.get("/models/{id}", summary="Get AI Model", description="Retrieve a specific AI Model by ID.")
def get_model(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    
    model = repo.get_model_by_id(db, id)
    if not model:
        raise HTTPException(404, detail=ResponseHelper.error(message="Model not found", error_code="NOT_FOUND", request_id=request_id).model_dump())
        
    return ResponseHelper.success(
        data=schemas.AIModelResponse.model_validate(model).model_dump(),
        message="Model retrieved successfully",
        request_id=request_id
    )

@models_router.put("/models/{id}", summary="Update AI Model", description="Update an existing AI Model. Allowed roles: ADMIN, GOVERNANCE_MANAGER", response_model=StandardResponse)
def update_model(
    request: Request,
    id: UUID,
    payload: schemas.AIModelUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    model = services.update_model(db, id, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.AIModelResponse.model_validate(model).model_dump(),
        message="AI Model updated successfully",
        request_id=request_id
    )

@models_router.patch("/models/{id}/status", summary="Change Model Status", description="Update the status of an AI Model.")
def change_model_status(
    request: Request,
    id: UUID,
    payload: schemas.StatusChangeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    model = services.change_model_status(db, id, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.AIModelResponse.model_validate(model).model_dump(),
        message="AI Model status updated successfully",
        request_id=request_id
    )

# ---------------------------------------------------------
# Agents Endpoints
# ---------------------------------------------------------

@agents_router.get("/agents", summary="List AI Agents", description="Retrieve a paginated list of registered AI Agents.")
def list_agents(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    agent_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    department_id: Optional[UUID] = None,
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    
    filters = {
        "search": search,
        "status": status,
        "agent_type": agent_type,
        "risk_level": risk_level,
        "department_id": department_id
    }
    
    items, total = repo.list_agents(db, filters, page, page_size, sort_by, sort_dir)
    
    response_data = schemas.AIAgentListResponse(
        items=[schemas.AIAgentResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        has_next=page < (math.ceil(total / page_size) if total > 0 else 0),
        has_prev=page > 1
    )
    
    return ResponseHelper.success(
        data=response_data.model_dump(),
        message="Agents retrieved successfully",
        request_id=request_id
    )

@agents_router.post("/agents", summary="Create AI Agent", description="Register a new AI Agent. Allowed roles: ADMIN, GOVERNANCE_MANAGER", response_model=StandardResponse)
def create_agent(
    request: Request,
    payload: schemas.AIAgentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    agent = services.create_agent(db, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.AIAgentResponse.model_validate(agent).model_dump(),
        message="AI Agent created successfully",
        request_id=request_id
    )

@agents_router.get("/agents/{id}", summary="Get AI Agent", description="Retrieve a specific AI Agent by ID.")
def get_agent(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    
    agent = repo.get_agent_by_id(db, id)
    if not agent:
        raise HTTPException(404, detail=ResponseHelper.error(message="Agent not found", error_code="NOT_FOUND", request_id=request_id).model_dump())
        
    return ResponseHelper.success(
        data=schemas.AIAgentResponse.model_validate(agent).model_dump(),
        message="Agent retrieved successfully",
        request_id=request_id
    )

@agents_router.put("/agents/{id}", summary="Update AI Agent", description="Update an existing AI Agent. Allowed roles: ADMIN, GOVERNANCE_MANAGER", response_model=StandardResponse)
def update_agent(
    request: Request,
    id: UUID,
    payload: schemas.AIAgentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    agent = services.update_agent(db, id, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.AIAgentResponse.model_validate(agent).model_dump(),
        message="AI Agent updated successfully",
        request_id=request_id
    )

@agents_router.patch("/agents/{id}/status", summary="Change Agent Status", description="Update the status of an AI Agent.")
def change_agent_status(
    request: Request,
    id: UUID,
    payload: schemas.StatusChangeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    agent = services.change_agent_status(db, id, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.AIAgentResponse.model_validate(agent).model_dump(),
        message="AI Agent status updated successfully",
        request_id=request_id
    )

# ---------------------------------------------------------
# Tools Endpoints
# ---------------------------------------------------------

@tools_router.get("/tools", summary="List Tools", description="Retrieve a paginated list of registered Tools.")
def list_tools(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    tool_category: Optional[str] = None,
    access_mode: Optional[str] = None,
    sensitivity_level: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    
    filters = {
        "search": search,
        "status": status,
        "tool_category": tool_category,
        "access_mode": access_mode,
        "sensitivity_level": sensitivity_level
    }
    
    items, total = repo.list_tools(db, filters, page, page_size, sort_by, sort_dir)
    
    response_data = schemas.ToolListResponse(
        items=[schemas.ToolResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        has_next=page < (math.ceil(total / page_size) if total > 0 else 0),
        has_prev=page > 1
    )
    
    return ResponseHelper.success(
        data=response_data.model_dump(),
        message="Tools retrieved successfully",
        request_id=request_id
    )

@tools_router.post("/tools", summary="Create Tool", description="Register a new Tool.")
def create_tool(
    request: Request,
    payload: schemas.ToolCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    tool = services.create_tool(db, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.ToolResponse.model_validate(tool).model_dump(),
        message="Tool created successfully",
        request_id=request_id
    )

@tools_router.get("/tools/{id}", summary="Get Tool", description="Retrieve a specific Tool by ID.")
def get_tool(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    
    tool = repo.get_tool_by_id(db, id)
    if not tool:
        raise HTTPException(404, detail=ResponseHelper.error(message="Tool not found", error_code="NOT_FOUND", request_id=request_id).model_dump())
        
    return ResponseHelper.success(
        data=schemas.ToolResponse.model_validate(tool).model_dump(),
        message="Tool retrieved successfully",
        request_id=request_id
    )

@tools_router.put("/tools/{id}", summary="Update Tool", description="Update an existing Tool.")
def update_tool(
    request: Request,
    id: UUID,
    payload: schemas.ToolUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    tool = services.update_tool(db, id, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.ToolResponse.model_validate(tool).model_dump(),
        message="Tool updated successfully",
        request_id=request_id
    )

@tools_router.patch("/tools/{id}/status", summary="Change Tool Status", description="Update the status of a Tool.")
def change_tool_status(
    request: Request,
    id: UUID,
    payload: schemas.StatusChangeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    tool = services.change_tool_status(db, id, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.ToolResponse.model_validate(tool).model_dump(),
        message="Tool status updated successfully",
        request_id=request_id
    )

# ---------------------------------------------------------
# Workflows Endpoints
# ---------------------------------------------------------

@workflows_router.get("/workflows", summary="List Workflows", description="Retrieve a paginated list of registered Workflows.")
def list_workflows(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    
    filters = {
        "search": search,
        "status": status
    }
    
    items, total = repo.list_workflows(db, filters, page, page_size, sort_by, sort_dir)
    
    response_data = schemas.WorkflowListResponse(
        items=[schemas.WorkflowResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        has_next=page < (math.ceil(total / page_size) if total > 0 else 0),
        has_prev=page > 1
    )
    
    return ResponseHelper.success(
        data=response_data.model_dump(),
        message="Workflows retrieved successfully",
        request_id=request_id
    )

@workflows_router.post("/workflows", summary="Create Workflow", description="Register a new Workflow.")
def create_workflow(
    request: Request,
    payload: schemas.WorkflowCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    workflow = services.create_workflow(db, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.WorkflowResponse.model_validate(workflow).model_dump(),
        message="Workflow created successfully",
        request_id=request_id
    )

@workflows_router.get("/workflows/{id}", summary="Get Workflow", description="Retrieve a specific Workflow by ID.")
def get_workflow(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    
    workflow = repo.get_workflow_by_id(db, id)
    if not workflow:
        raise HTTPException(404, detail=ResponseHelper.error(message="Workflow not found", error_code="NOT_FOUND", request_id=request_id).model_dump())
        
    return ResponseHelper.success(
        data=schemas.WorkflowResponse.model_validate(workflow).model_dump(),
        message="Workflow retrieved successfully",
        request_id=request_id
    )

@workflows_router.put("/workflows/{id}", summary="Update Workflow", description="Update an existing Workflow.")
def update_workflow(
    request: Request,
    id: UUID,
    payload: schemas.WorkflowUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    workflow = services.update_workflow(db, id, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.WorkflowResponse.model_validate(workflow).model_dump(),
        message="Workflow updated successfully",
        request_id=request_id
    )

@workflows_router.patch("/workflows/{id}/status", summary="Change Workflow Status", description="Update the status of a Workflow.")
def change_workflow_status(
    request: Request,
    id: UUID,
    payload: schemas.StatusChangeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    workflow = services.change_workflow_status(db, id, payload, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.WorkflowResponse.model_validate(workflow).model_dump(),
        message="Workflow status updated successfully",
        request_id=request_id
    )

@workflows_router.post("/workflows/{id}/approve", summary="Approve Workflow", description="Approve a pending workflow.")
def approve_workflow_endpoint(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    workflow = services.approve_workflow(db, id, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.WorkflowResponse.model_validate(workflow).model_dump(),
        message="Workflow approved successfully",
        request_id=request_id
    )

@workflows_router.post("/workflows/{id}/reject", summary="Reject Workflow", description="Reject a pending workflow.")
def reject_workflow_endpoint(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    
    workflow = services.reject_workflow(db, id, current_user)
    db.commit()
    
    return ResponseHelper.success(
        data=schemas.WorkflowResponse.model_validate(workflow).model_dump(),
        message="Workflow rejected successfully",
        request_id=request_id
    )

# ---------------------------------------------------------
# Summary Endpoint
# ---------------------------------------------------------

@summary_router.get("/summary", summary="Registry Summary", description="Retrieve a summary of all registry entities.")
def get_summary(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    
    summary_data = services.get_registry_summary(db)
    
    return ResponseHelper.success(
        data=summary_data,
        message="Registry summary retrieved successfully",
        request_id=request_id
    )

# ---------------------------------------------------------
# Departments Endpoints
# ---------------------------------------------------------

@departments_router.get("/departments/lookup", summary="Lookup Departments", description="Retrieve active departments for dropdowns.")
def lookup_departments(request: Request, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    items = repo.lookup_departments(db)
    return ResponseHelper.success(
        data=[schemas.DepartmentLookup.model_validate(i).model_dump() for i in items],
        message="Departments retrieved successfully",
        request_id=request_id
    )

@departments_router.get("/departments", summary="List Departments")
def list_departments(
    request: Request, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None, status: Optional[str] = None,
    sort_by: str = Query("created_at"), sort_dir: str = Query("desc"),
    db: Session = Depends(get_db), current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    items, total = repo.list_departments(db, {"search": search, "status": status}, page, page_size, sort_by, sort_dir)
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return ResponseHelper.success(
        data=schemas.DepartmentListResponse(
            items=[schemas.DepartmentResponse.model_validate(i) for i in items],
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        ).model_dump(),
        message="Departments retrieved", request_id=request_id
    )

@departments_router.post("/departments", summary="Create Department")
def create_department(request: Request, payload: schemas.DepartmentCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    dept = services.create_department(db, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.DepartmentResponse.model_validate(dept).model_dump(), message="Created", request_id=request_id)

@departments_router.get("/departments/{id}", summary="Get Department")
def get_department(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    dept = repo.get_department_by_id(db, id)
    if not dept: raise HTTPException(404, detail=ResponseHelper.error(message="Not found", error_code="NOT_FOUND", request_id=request_id).model_dump())
    return ResponseHelper.success(data=schemas.DepartmentResponse.model_validate(dept).model_dump(), message="Retrieved", request_id=request_id)

@departments_router.put("/departments/{id}", summary="Update Department")
def update_department(request: Request, id: UUID, payload: schemas.DepartmentUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    dept = services.update_department(db, id, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.DepartmentResponse.model_validate(dept).model_dump(), message="Updated", request_id=request_id)

@departments_router.patch("/departments/{id}/status", summary="Change Department Status")
def change_department_status(request: Request, id: UUID, payload: schemas.StatusChangeRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    dept = services.change_department_status(db, id, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.DepartmentResponse.model_validate(dept).model_dump(), message="Status updated", request_id=request_id)

# ---------------------------------------------------------
# Roles Endpoints
# ---------------------------------------------------------

@roles_router.get("/roles/lookup", summary="Lookup Roles")
def lookup_roles(request: Request, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    items = repo.lookup_roles(db)
    return ResponseHelper.success(
        data=[schemas.RoleLookup.model_validate(i).model_dump() for i in items],
        message="Roles retrieved successfully",
        request_id=request_id
    )

@roles_router.get("/roles", summary="List Roles")
def list_roles(
    request: Request, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None, status: Optional[str] = None,
    sort_by: str = Query("created_at"), sort_dir: str = Query("desc"),
    db: Session = Depends(get_db), current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    items, total = repo.list_roles(db, {"search": search, "status": status}, page, page_size, sort_by, sort_dir)
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return ResponseHelper.success(
        data=schemas.RoleListResponse(
            items=[schemas.RoleResponse.model_validate(i) for i in items],
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        ).model_dump(),
        message="Roles retrieved", request_id=request_id
    )

@roles_router.post("/roles", summary="Create Role")
def create_role(request: Request, payload: schemas.RoleCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    role = services.create_role(db, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.RoleResponse.model_validate(role).model_dump(), message="Created", request_id=request_id)

@roles_router.get("/roles/{id}", summary="Get Role")
def get_role(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    role = repo.get_role_by_id(db, id)
    if not role: raise HTTPException(404, detail=ResponseHelper.error(message="Not found", error_code="NOT_FOUND", request_id=request_id).model_dump())
    return ResponseHelper.success(data=schemas.RoleResponse.model_validate(role).model_dump(), message="Retrieved", request_id=request_id)

@roles_router.put("/roles/{id}", summary="Update Role")
def update_role(request: Request, id: UUID, payload: schemas.RoleUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    role = services.update_role(db, id, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.RoleResponse.model_validate(role).model_dump(), message="Updated", request_id=request_id)

@roles_router.patch("/roles/{id}/status", summary="Change Role Status")
def change_role_status(request: Request, id: UUID, payload: schemas.StatusChangeRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    role = services.change_role_status(db, id, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.RoleResponse.model_validate(role).model_dump(), message="Status updated", request_id=request_id)

# ---------------------------------------------------------
# Users Endpoints
# ---------------------------------------------------------

@users_router.get("/users/lookup", summary="Lookup Users")
def lookup_users(request: Request, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    items = repo.lookup_users(db)
    return ResponseHelper.success(
        data=[schemas.GuardianUserLookup.model_validate(i).model_dump() for i in items],
        message="Users retrieved successfully",
        request_id=request_id
    )

@users_router.get("/users", summary="List Users")
def list_users(
    request: Request, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None, status: Optional[str] = None,
    sort_by: str = Query("created_at"), sort_dir: str = Query("desc"),
    db: Session = Depends(get_db), current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    items, total = repo.list_users(db, {"search": search, "status": status}, page, page_size, sort_by, sort_dir)
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return ResponseHelper.success(
        data=schemas.GuardianUserListResponse(
            items=[schemas.GuardianUserResponse.model_validate(i) for i in items],
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        ).model_dump(),
        message="Users retrieved", request_id=request_id
    )

@users_router.post("/users", summary="Create User")
def create_user(request: Request, payload: schemas.GuardianUserCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    user = services.create_user(db, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.GuardianUserResponse.model_validate(user).model_dump(), message="Created", request_id=request_id)

@users_router.get("/users/{id}", summary="Get User")
def get_user(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    user = repo.get_user_by_id(db, id)
    if not user: raise HTTPException(404, detail=ResponseHelper.error(message="Not found", error_code="NOT_FOUND", request_id=request_id).model_dump())
    return ResponseHelper.success(data=schemas.GuardianUserResponse.model_validate(user).model_dump(), message="Retrieved", request_id=request_id)

@users_router.put("/users/{id}", summary="Update User")
def update_user(request: Request, id: UUID, payload: schemas.GuardianUserUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    user = services.update_user(db, id, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.GuardianUserResponse.model_validate(user).model_dump(), message="Updated", request_id=request_id)

@users_router.patch("/users/{id}/status", summary="Change User Status")
def change_user_status(request: Request, id: UUID, payload: schemas.StatusChangeRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    user = services.change_user_status(db, id, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.GuardianUserResponse.model_validate(user).model_dump(), message="Status updated", request_id=request_id)

# ---------------------------------------------------------
# Data Sources Endpoints
# ---------------------------------------------------------

@data_sources_router.get("/data-sources", summary="List Data Sources")
def list_data_sources(
    request: Request, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None, status: Optional[str] = None,
    sort_by: str = Query("created_at"), sort_dir: str = Query("desc"),
    db: Session = Depends(get_db), current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    items, total = repo.list_data_sources(db, {"search": search, "status": status}, page, page_size, sort_by, sort_dir)
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return ResponseHelper.success(
        data=schemas.DataSourceListResponse(
            items=[schemas.DataSourceResponse.model_validate(i) for i in items],
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        ).model_dump(),
        message="Data Sources retrieved", request_id=request_id
    )

@data_sources_router.post("/data-sources", summary="Create Data Source")
def create_data_source(request: Request, payload: schemas.DataSourceCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    source = services.create_data_source(db, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.DataSourceResponse.model_validate(source).model_dump(), message="Created", request_id=request_id)

@data_sources_router.get("/data-sources/{id}", summary="Get Data Source")
def get_data_source(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    source = repo.get_data_source_by_id(db, id)
    if not source: raise HTTPException(404, detail=ResponseHelper.error(message="Not found", error_code="NOT_FOUND", request_id=request_id).model_dump())
    return ResponseHelper.success(data=schemas.DataSourceResponse.model_validate(source).model_dump(), message="Retrieved", request_id=request_id)

@data_sources_router.put("/data-sources/{id}", summary="Update Data Source")
def update_data_source(request: Request, id: UUID, payload: schemas.DataSourceUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    source = services.update_data_source(db, id, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.DataSourceResponse.model_validate(source).model_dump(), message="Updated", request_id=request_id)

@data_sources_router.patch("/data-sources/{id}/status", summary="Change Data Source Status")
def change_data_source_status(request: Request, id: UUID, payload: schemas.StatusChangeRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    source = services.change_data_source_status(db, id, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.DataSourceResponse.model_validate(source).model_dump(), message="Status updated", request_id=request_id)

# ---------------------------------------------------------
# Relationships Endpoints
# ---------------------------------------------------------

@relationships_router.post("/relationships", summary="Create Relationship")
def create_relationship(request: Request, payload: schemas.RelationshipCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    rel = services.create_relationship(db, payload, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.RelationshipResponse.model_validate(rel).model_dump(), message="Relationship created", request_id=request_id)

@relationships_router.get("/relationships", summary="Get Relationships for Entity")
def get_relationships(request: Request, entity_type: str = Query(...), entity_id: UUID = Query(...), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    
    outgoing_rels, incoming_rels = repo.list_relationships_for_entity(db, entity_type, entity_id)
    
    outgoing_items = []
    for rel in outgoing_rels:
        name = repo.get_entity_name(db, rel.target_entity_type, rel.target_entity_id)
        outgoing_items.append({
            "id": rel.id, "relationship_type": rel.relationship_type,
            "other_entity_type": rel.target_entity_type, "other_entity_id": rel.target_entity_id,
            "other_entity_name": name, "status": rel.status
        })
        
    incoming_items = []
    for rel in incoming_rels:
        name = repo.get_entity_name(db, rel.source_entity_type, rel.source_entity_id)
        incoming_items.append({
            "id": rel.id, "relationship_type": rel.relationship_type,
            "other_entity_type": rel.source_entity_type, "other_entity_id": rel.source_entity_id,
            "other_entity_name": name, "status": rel.status
        })
        
    return ResponseHelper.success(
        data=schemas.RelationshipGroupedResponse(outgoing=outgoing_items, incoming=incoming_items).model_dump(),
        message="Relationships retrieved", request_id=request_id
    )

@relationships_router.delete("/relationships/{id}", summary="Delete Relationship")
def delete_relationship(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    rel = services.delete_relationship(db, id, current_user)
    db.commit()
    return ResponseHelper.success(data=schemas.RelationshipResponse.model_validate(rel).model_dump(), message="Relationship removed", request_id=request_id)

# ---------------------------------------------------------
# Delete Endpoints

@models_router.delete("/models/{id}", summary="Delete AI Model", description="Permanently delete a model. Allowed roles: ADMIN, GOVERNANCE_MANAGER")
def delete_model(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    services.delete_model(db, id, current_user)
    db.commit()
    return ResponseHelper.success(message="Model deleted", request_id=request_id)

@agents_router.delete("/agents/{id}", summary="Delete AI Agent", description="Permanently delete an agent. Allowed roles: ADMIN, GOVERNANCE_MANAGER")
def delete_agent(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    services.delete_agent(db, id, current_user)
    db.commit()
    return ResponseHelper.success(message="Agent deleted", request_id=request_id)

@tools_router.delete("/tools/{id}", summary="Delete Tool", description="Permanently delete a tool. Allowed roles: ADMIN, GOVERNANCE_MANAGER")
def delete_tool(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    services.delete_tool(db, id, current_user)
    db.commit()
    return ResponseHelper.success(message="Tool deleted", request_id=request_id)

@workflows_router.delete("/workflows/{id}", summary="Delete Workflow", description="Permanently delete a workflow. Allowed roles: ADMIN, GOVERNANCE_MANAGER")
def delete_workflow(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    services.delete_workflow(db, id, current_user)
    db.commit()
    return ResponseHelper.success(message="Workflow deleted", request_id=request_id)

@departments_router.delete("/departments/{id}", summary="Delete Department", description="Permanently delete a department. Allowed roles: ADMIN, GOVERNANCE_MANAGER")
def delete_department(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    services.delete_department(db, id, current_user)
    db.commit()
    return ResponseHelper.success(message="Department deleted", request_id=request_id)

@roles_router.delete("/roles/{id}", summary="Delete Role", description="Permanently delete a role. Allowed roles: ADMIN, GOVERNANCE_MANAGER")
def delete_role(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    services.delete_role(db, id, current_user)
    db.commit()
    return ResponseHelper.success(message="Role deleted", request_id=request_id)

@users_router.delete("/users/{id}", summary="Delete User", description="Permanently delete a user. Allowed roles: ADMIN, GOVERNANCE_MANAGER")
def delete_user(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    services.delete_user(db, id, current_user)
    db.commit()
    return ResponseHelper.success(message="User deleted", request_id=request_id)

@data_sources_router.delete("/data-sources/{id}", summary="Delete Data Source", description="Permanently delete a data source. Allowed roles: ADMIN, GOVERNANCE_MANAGER")
def delete_data_source(request: Request, id: UUID, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_write_roles(current_user, request_id)
    services.delete_data_source(db, id, current_user)
    db.commit()
    return ResponseHelper.success(message="Data Source deleted", request_id=request_id)

# ---------------------------------------------------------
# Audit Endpoints
# ---------------------------------------------------------

@audit_router.get("/audit/{entity_type}/{entity_id}", summary="Get Audit Events")
def get_audit_events(
    request: Request, entity_type: str, entity_id: UUID, event_type: Optional[str] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), current_user = Depends(get_current_user)
):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    if current_user.role_code not in ["ADMIN", "AUDITOR"]:
        raise HTTPException(403, detail=ResponseHelper.error(message="Insufficient permission", error_code="FORBIDDEN", request_id=request_id).model_dump())
        
    items, total = repo.list_audit_events(db, entity_type, entity_id, event_type, page, page_size)
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return ResponseHelper.success(
        data=schemas.AuditListResponse(
            items=[schemas.AuditResponse.model_validate(i) for i in items],
            total=total, page=page, page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        ).model_dump(),
        message="Audit events retrieved", request_id=request_id
    )

# ---------------------------------------------------------
# Search Endpoints
# ---------------------------------------------------------

@search_router.get("/search", summary="Global Search")
def global_search(request: Request, q: str = Query(..., min_length=2), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    require_read_roles(current_user, request_id)
    
    if len(q) < 2:
        raise HTTPException(400, detail=ResponseHelper.error(message="Search term must be at least 2 characters", error_code="VALIDATION_ERROR", request_id=request_id).model_dump())
        
    results = repo.global_search(db, q)
    return ResponseHelper.success(
        data=schemas.GlobalSearchResponse.model_validate(results).model_dump(),
        message="Search completed", request_id=request_id
    )

# ---------------------------------------------------------
# Unified Registry Router
# ---------------------------------------------------------
router = APIRouter(prefix="/api/registry")
router.include_router(models_router, tags=["Registry - Models"])
router.include_router(agents_router, tags=["Registry - Agents"])
router.include_router(tools_router, tags=["Registry - Tools"])
router.include_router(workflows_router, tags=["Registry - Workflows"])
router.include_router(summary_router, tags=["Registry - Summary"])
router.include_router(departments_router, tags=["Registry - Departments"])
router.include_router(roles_router, tags=["Registry - Roles"])
router.include_router(users_router, tags=["Registry - Users"])
router.include_router(data_sources_router, tags=["Registry - Data Sources"])
router.include_router(relationships_router, tags=["Registry - Relationships"])
router.include_router(audit_router, tags=["Registry - Audit"])
router.include_router(search_router, tags=["Registry - Search"])
