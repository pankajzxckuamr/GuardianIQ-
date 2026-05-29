from typing import Optional, Tuple, List
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.modules.auth.models import User # using User from auth, wait, user said "guardian_users" is for Phase 1
from app.modules.registry.models import (
    RegistryAIModel, RegistryAIAgent, GuardianUser, RegistryDepartment,
    RegistryTool, RegistryWorkflow, RegistryRole, RegistryDataSource
)
from app.modules.registry import repositories as repo
from app.modules.registry import schemas
from app.modules.registry import validators
from app.modules.registry.audit_service import write_registry_audit
from app.shared.response_utils import ResponseHelper
import json

class RegistryEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        if hasattr(obj, 'value'): # Enums
            return obj.value
        return super().default(obj)

def to_dict(obj):
    # Quick helper to serialize SQLAlchemy model state for audit
    return json.loads(json.dumps(
        {c.name: getattr(obj, c.name) for c in obj.__table__.columns},
        cls=RegistryEncoder
    ))

# ---------------------------------------------------------
# AI Models Services
# ---------------------------------------------------------

def create_model(db: Session, payload: schemas.AIModelCreate, current_user) -> RegistryAIModel:
    validators.validate_unique_code(db, RegistryAIModel, 'model_code', payload.model_code)
    
    if payload.owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.owner_user_id, "Owner User")
    if payload.department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.department_id, "Department")
        
    model = repo.create_model(db, payload.model_dump(), current_user.id)
    
    write_registry_audit(
        db=db,
        entity_type="MODEL",
        entity_id=model.id,
        event_type="CREATED",
        changed_by=current_user.id,
        after_json=to_dict(model),
        change_summary="Model registered"
    )
    return model

def update_model(db: Session, model_id: UUID, payload: schemas.AIModelUpdate, current_user) -> RegistryAIModel:
    model = repo.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(404, detail=ResponseHelper.error(message="Model not found", error_code="NOT_FOUND").model_dump())
        
    if payload.owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.owner_user_id, "Owner User")
    if payload.department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.department_id, "Department")

    before_state = to_dict(model)
    model = repo.update_model(db, model, payload.model_dump(exclude_unset=True), current_user.id)
    after_state = to_dict(model)
    
    write_registry_audit(
        db=db,
        entity_type="MODEL",
        entity_id=model.id,
        event_type="UPDATED",
        changed_by=current_user.id,
        before_json=before_state,
        after_json=after_state,
        change_summary="Model updated"
    )
    return model

def change_model_status(db: Session, model_id: UUID, payload: schemas.StatusChangeRequest, current_user) -> RegistryAIModel:
    model = repo.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(404, detail=ResponseHelper.error(message="Model not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_status_transition(model.status, payload.status)
    
    before_state = to_dict(model)
    model = repo.change_model_status(db, model, payload.status, current_user.id)
    after_state = to_dict(model)
    
    write_registry_audit(
        db=db,
        entity_type="MODEL",
        entity_id=model.id,
        event_type="STATUS_CHANGED",
        changed_by=current_user.id,
        before_json=before_state,
        after_json=after_state,
        change_summary=payload.reason or f"Status changed to {payload.status}"
    )
    return model

# ---------------------------------------------------------
# AI Agents Services
# ---------------------------------------------------------

def create_agent(db: Session, payload: schemas.AIAgentCreate, current_user) -> RegistryAIAgent:
    validators.validate_unique_code(db, RegistryAIAgent, 'agent_code', payload.agent_code)
    validators.validate_confidence_threshold(payload.confidence_threshold)
    
    if payload.owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.owner_user_id, "Owner User")
    if payload.department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.department_id, "Department")
        
    agent = repo.create_agent(db, payload.model_dump(), current_user.id)
    
    write_registry_audit(
        db=db,
        entity_type="AGENT",
        entity_id=agent.id,
        event_type="CREATED",
        changed_by=current_user.id,
        after_json=to_dict(agent),
        change_summary="Agent registered"
    )
    return agent

def update_agent(db: Session, agent_id: UUID, payload: schemas.AIAgentUpdate, current_user) -> RegistryAIAgent:
    agent = repo.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(404, detail=ResponseHelper.error(message="Agent not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_confidence_threshold(payload.confidence_threshold)
    if payload.owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.owner_user_id, "Owner User")
    if payload.department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.department_id, "Department")

    before_state = to_dict(agent)
    agent = repo.update_agent(db, agent, payload.model_dump(exclude_unset=True), current_user.id)
    after_state = to_dict(agent)
    
    write_registry_audit(
        db=db,
        entity_type="AGENT",
        entity_id=agent.id,
        event_type="UPDATED",
        changed_by=current_user.id,
        before_json=before_state,
        after_json=after_state,
        change_summary="Agent updated"
    )
    return agent

def change_agent_status(db: Session, agent_id: UUID, payload: schemas.StatusChangeRequest, current_user) -> RegistryAIAgent:
    agent = repo.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(404, detail=ResponseHelper.error(message="Agent not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_status_transition(agent.status, payload.status)
    
    before_state = to_dict(agent)
    agent = repo.change_agent_status(db, agent, payload.status, current_user.id)
    after_state = to_dict(agent)
    
    write_registry_audit(
        db=db,
        entity_type="AGENT",
        entity_id=agent.id,
        event_type="STATUS_CHANGED",
        changed_by=current_user.id,
        before_json=before_state,
        after_json=after_state,
        change_summary=payload.reason or f"Status changed to {payload.status}"
    )
    return agent

# ---------------------------------------------------------
# Tool Services
# ---------------------------------------------------------

def create_tool(db: Session, payload: schemas.ToolCreate, current_user) -> RegistryTool:
    validators.validate_unique_code(db, RegistryTool, 'tool_code', payload.tool_code)
    validators.validate_endpoint_reference(payload.endpoint_reference)
    
    if payload.owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.owner_user_id, "Owner User")
        
    tool = repo.create_tool(db, payload.model_dump())
    
    write_registry_audit(
        db=db,
        entity_type="TOOL",
        entity_id=tool.id,
        event_type="CREATED",
        changed_by=current_user.id,
        after_json=to_dict(tool),
        change_summary="Tool registered"
    )
    return tool

def update_tool(db: Session, tool_id: UUID, payload: schemas.ToolUpdate, current_user) -> RegistryTool:
    tool = repo.get_tool_by_id(db, tool_id)
    if not tool:
        raise HTTPException(404, detail=ResponseHelper.error(message="Tool not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_endpoint_reference(payload.endpoint_reference)
    if payload.owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.owner_user_id, "Owner User")

    before_state = to_dict(tool)
    tool = repo.update_tool(db, tool, payload.model_dump(exclude_unset=True))
    after_state = to_dict(tool)
    
    write_registry_audit(
        db=db,
        entity_type="TOOL",
        entity_id=tool.id,
        event_type="UPDATED",
        changed_by=current_user.id,
        before_json=before_state,
        after_json=after_state,
        change_summary="Tool updated"
    )
    return tool

def change_tool_status(db: Session, tool_id: UUID, payload: schemas.StatusChangeRequest, current_user) -> RegistryTool:
    tool = repo.get_tool_by_id(db, tool_id)
    if not tool:
        raise HTTPException(404, detail=ResponseHelper.error(message="Tool not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_status_transition(tool.status, payload.status)
    
    before_state = to_dict(tool)
    tool = repo.change_tool_status(db, tool, payload.status)
    after_state = to_dict(tool)
    
    write_registry_audit(
        db=db,
        entity_type="TOOL",
        entity_id=tool.id,
        event_type="STATUS_CHANGED",
        changed_by=current_user.id,
        before_json=before_state,
        after_json=after_state,
        change_summary=payload.reason or f"Status changed to {payload.status}"
    )
    return tool

# ---------------------------------------------------------
# Workflow Services
# ---------------------------------------------------------

def create_workflow(db: Session, payload: schemas.WorkflowCreate, current_user) -> RegistryWorkflow:
    validators.validate_unique_code(db, RegistryWorkflow, 'workflow_code', payload.workflow_code)
    validators.validate_steps_json(payload.steps_json)
    
    if payload.owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.owner_user_id, "Owner User")
    if payload.department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.department_id, "Department")
        
    workflow = repo.create_workflow(db, payload.model_dump())
    
    write_registry_audit(
        db=db,
        entity_type="WORKFLOW",
        entity_id=workflow.id,
        event_type="CREATED",
        changed_by=current_user.id,
        after_json=to_dict(workflow),
        change_summary="Workflow registered"
    )
    return workflow

def update_workflow(db: Session, workflow_id: UUID, payload: schemas.WorkflowUpdate, current_user) -> RegistryWorkflow:
    workflow = repo.get_workflow_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(404, detail=ResponseHelper.error(message="Workflow not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_steps_json(payload.steps_json)
    if payload.owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.owner_user_id, "Owner User")
    if payload.department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.department_id, "Department")

    before_state = to_dict(workflow)
    workflow = repo.update_workflow(db, workflow, payload.model_dump(exclude_unset=True))
    after_state = to_dict(workflow)
    
    write_registry_audit(
        db=db,
        entity_type="WORKFLOW",
        entity_id=workflow.id,
        event_type="UPDATED",
        changed_by=current_user.id,
        before_json=before_state,
        after_json=after_state,
        change_summary="Workflow updated"
    )
    return workflow

def change_workflow_status(db: Session, workflow_id: UUID, payload: schemas.StatusChangeRequest, current_user) -> RegistryWorkflow:
    workflow = repo.get_workflow_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(404, detail=ResponseHelper.error(message="Workflow not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_status_transition(workflow.status, payload.status)
    
    before_state = to_dict(workflow)
    workflow = repo.change_workflow_status(db, workflow, payload.status)
    after_state = to_dict(workflow)
    
    write_registry_audit(
        db=db,
        entity_type="WORKFLOW",
        entity_id=workflow.id,
        event_type="STATUS_CHANGED",
        changed_by=current_user.id,
        before_json=before_state,
        after_json=after_state,
        change_summary=payload.reason or f"Status changed to {payload.status}"
    )
    return workflow

# ---------------------------------------------------------
# Summary Service
# ---------------------------------------------------------

def get_registry_summary(db: Session) -> dict:
    return repo.get_registry_summary(db)

# ---------------------------------------------------------
# Department Services
# ---------------------------------------------------------

def create_department(db: Session, payload: schemas.DepartmentCreate, current_user) -> RegistryDepartment:
    validators.validate_unique_code(db, RegistryDepartment, 'department_code', payload.department_code)
    validators.validate_parent_department(payload.department_code, payload.parent_department_id) # Using code as placeholder, actually UUID, wait!
    # Wait, parent_department_id logic requires ID, but it doesn't have an ID yet.
    # The validator requires department_id which doesn't exist before creation. We can skip it on create, or pass None.
    
    if payload.parent_department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.parent_department_id, "Parent Department")
    if payload.business_owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.business_owner_user_id, "Business Owner User")
    if payload.escalation_owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.escalation_owner_user_id, "Escalation Owner User")
        
    dept = repo.create_department(db, payload.model_dump())
    
    write_registry_audit(
        db=db, entity_type="DEPARTMENT", entity_id=dept.id, event_type="CREATED",
        changed_by=current_user.id, after_json=to_dict(dept), change_summary="Department registered"
    )
    return dept

def update_department(db: Session, dept_id: UUID, payload: schemas.DepartmentUpdate, current_user) -> RegistryDepartment:
    dept = repo.get_department_by_id(db, dept_id)
    if not dept:
        raise HTTPException(404, detail=ResponseHelper.error(message="Department not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_parent_department(dept_id, payload.parent_department_id)
    
    if payload.parent_department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.parent_department_id, "Parent Department")
    if payload.business_owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.business_owner_user_id, "Business Owner User")
    if payload.escalation_owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.escalation_owner_user_id, "Escalation Owner User")

    before_state = to_dict(dept)
    dept = repo.update_department(db, dept, payload.model_dump(exclude_unset=True))
    after_state = to_dict(dept)
    
    write_registry_audit(
        db=db, entity_type="DEPARTMENT", entity_id=dept.id, event_type="UPDATED",
        changed_by=current_user.id, before_json=before_state, after_json=after_state, change_summary="Department updated"
    )
    return dept

def change_department_status(db: Session, dept_id: UUID, payload: schemas.StatusChangeRequest, current_user) -> RegistryDepartment:
    dept = repo.get_department_by_id(db, dept_id)
    if not dept:
        raise HTTPException(404, detail=ResponseHelper.error(message="Department not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_status_transition(dept.status, payload.status)
    
    before_state = to_dict(dept)
    dept = repo.change_department_status(db, dept, payload.status)
    after_state = to_dict(dept)
    
    write_registry_audit(
        db=db, entity_type="DEPARTMENT", entity_id=dept.id, event_type="STATUS_CHANGED",
        changed_by=current_user.id, before_json=before_state, after_json=after_state, change_summary=payload.reason or f"Status changed to {payload.status}"
    )
    return dept

# ---------------------------------------------------------
# Role Services
# ---------------------------------------------------------

def create_role(db: Session, payload: schemas.RoleCreate, current_user) -> RegistryRole:
    validators.validate_unique_code(db, RegistryRole, 'role_code', payload.role_code)
    
    role = repo.create_role(db, payload.model_dump())
    
    write_registry_audit(
        db=db, entity_type="ROLE", entity_id=role.id, event_type="CREATED",
        changed_by=current_user.id, after_json=to_dict(role), change_summary="Role registered"
    )
    return role

def update_role(db: Session, role_id: UUID, payload: schemas.RoleUpdate, current_user) -> RegistryRole:
    role = repo.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(404, detail=ResponseHelper.error(message="Role not found", error_code="NOT_FOUND").model_dump())

    before_state = to_dict(role)
    role = repo.update_role(db, role, payload.model_dump(exclude_unset=True))
    after_state = to_dict(role)
    
    write_registry_audit(
        db=db, entity_type="ROLE", entity_id=role.id, event_type="UPDATED",
        changed_by=current_user.id, before_json=before_state, after_json=after_state, change_summary="Role updated"
    )
    return role

def change_role_status(db: Session, role_id: UUID, payload: schemas.StatusChangeRequest, current_user) -> RegistryRole:
    role = repo.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(404, detail=ResponseHelper.error(message="Role not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_status_transition(role.status, payload.status)
    
    before_state = to_dict(role)
    role = repo.change_role_status(db, role, payload.status)
    after_state = to_dict(role)
    
    write_registry_audit(
        db=db, entity_type="ROLE", entity_id=role.id, event_type="STATUS_CHANGED",
        changed_by=current_user.id, before_json=before_state, after_json=after_state, change_summary=payload.reason or f"Status changed to {payload.status}"
    )
    return role

# ---------------------------------------------------------
# User Services
# ---------------------------------------------------------

def create_user(db: Session, payload: schemas.GuardianUserCreate, current_user) -> GuardianUser:
    validators.validate_unique_code(db, GuardianUser, 'email', payload.email)
    
    if payload.department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.department_id, "Department")
    if payload.role_id:
        validators.validate_entity_exists(db, RegistryRole, payload.role_id, "Role")
        
    user = repo.create_user(db, payload.model_dump())
    
    write_registry_audit(
        db=db, entity_type="USER", entity_id=user.id, event_type="CREATED",
        changed_by=current_user.id, after_json=to_dict(user), change_summary="User registered"
    )
    return user

def update_user(db: Session, user_id: UUID, payload: schemas.GuardianUserUpdate, current_user) -> GuardianUser:
    user = repo.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404, detail=ResponseHelper.error(message="User not found", error_code="NOT_FOUND").model_dump())
        
    if payload.department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.department_id, "Department")
    if payload.role_id:
        validators.validate_entity_exists(db, RegistryRole, payload.role_id, "Role")

    before_state = to_dict(user)
    user = repo.update_user(db, user, payload.model_dump(exclude_unset=True))
    after_state = to_dict(user)
    
    write_registry_audit(
        db=db, entity_type="USER", entity_id=user.id, event_type="UPDATED",
        changed_by=current_user.id, before_json=before_state, after_json=after_state, change_summary="User updated"
    )
    return user

def change_user_status(db: Session, user_id: UUID, payload: schemas.StatusChangeRequest, current_user) -> GuardianUser:
    user = repo.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404, detail=ResponseHelper.error(message="User not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_status_transition(user.status, payload.status)
    
    before_state = to_dict(user)
    user = repo.change_user_status(db, user, payload.status)
    after_state = to_dict(user)
    
    write_registry_audit(
        db=db, entity_type="USER", entity_id=user.id, event_type="STATUS_CHANGED",
        changed_by=current_user.id, before_json=before_state, after_json=after_state, change_summary=payload.reason or f"Status changed to {payload.status}"
    )
    return user

# ---------------------------------------------------------
# DataSource Services
# ---------------------------------------------------------

def create_data_source(db: Session, payload: schemas.DataSourceCreate, current_user) -> RegistryDataSource:
    validators.validate_unique_code(db, RegistryDataSource, 'source_code', payload.source_code)
    validators.validate_endpoint_reference(payload.connection_reference)
    
    if payload.owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.owner_user_id, "Owner User")
    if payload.department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.department_id, "Department")
        
    source = repo.create_data_source(db, payload.model_dump())
    
    write_registry_audit(
        db=db, entity_type="DATA_SOURCE", entity_id=source.id, event_type="CREATED",
        changed_by=current_user.id, after_json=to_dict(source), change_summary="Data Source registered"
    )
    return source

def update_data_source(db: Session, source_id: UUID, payload: schemas.DataSourceUpdate, current_user) -> RegistryDataSource:
    source = repo.get_data_source_by_id(db, source_id)
    if not source:
        raise HTTPException(404, detail=ResponseHelper.error(message="Data Source not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_endpoint_reference(payload.connection_reference)
    
    if payload.owner_user_id:
        validators.validate_entity_exists(db, GuardianUser, payload.owner_user_id, "Owner User")
    if payload.department_id:
        validators.validate_entity_exists(db, RegistryDepartment, payload.department_id, "Department")

    before_state = to_dict(source)
    source = repo.update_data_source(db, source, payload.model_dump(exclude_unset=True))
    after_state = to_dict(source)
    
    write_registry_audit(
        db=db, entity_type="DATA_SOURCE", entity_id=source.id, event_type="UPDATED",
        changed_by=current_user.id, before_json=before_state, after_json=after_state, change_summary="Data Source updated"
    )
    return source

def change_data_source_status(db: Session, source_id: UUID, payload: schemas.StatusChangeRequest, current_user) -> RegistryDataSource:
    source = repo.get_data_source_by_id(db, source_id)
    if not source:
        raise HTTPException(404, detail=ResponseHelper.error(message="Data Source not found", error_code="NOT_FOUND").model_dump())
        
    validators.validate_status_transition(source.status, payload.status)
    
    before_state = to_dict(source)
    source = repo.change_data_source_status(db, source, payload.status)
    after_state = to_dict(source)
    
    write_registry_audit(
        db=db, entity_type="DATA_SOURCE", entity_id=source.id, event_type="STATUS_CHANGED",
        changed_by=current_user.id, before_json=before_state, after_json=after_state, change_summary=payload.reason or f"Status changed to {payload.status}"
    )
    return source

# ---------------------------------------------------------
# Relationships Services
# ---------------------------------------------------------

ALLOWED_RELATIONSHIPS = {
    ("MODEL", "USES", "DATA_SOURCE"),
    ("MODEL", "USES", "TOOL"),
    ("AGENT", "USES", "TOOL"),
    ("AGENT", "EXECUTES", "WORKFLOW"),
    ("WORKFLOW", "USES", "DATA_SOURCE"),
    ("WORKFLOW", "USES", "TOOL"),
    ("WORKFLOW", "GOVERNED_BY", "DEPARTMENT"),
    ("USER", "OWNS", "ROLE"),
    ("DEPARTMENT", "GOVERNED_BY", "USER")
}

def create_relationship(db: Session, payload: schemas.RelationshipCreate, current_user):
    rel_tuple = (payload.source_entity_type, payload.relationship_type, payload.target_entity_type)
    if rel_tuple not in ALLOWED_RELATIONSHIPS:
        raise HTTPException(400, detail=ResponseHelper.error(message="Relationship not allowed for selected entities", error_code="VALIDATION_ERROR").model_dump())
        
    def check_entity(entity_type, entity_id):
        table_map = {
            "MODEL": RegistryAIModel, "AGENT": RegistryAIAgent, "TOOL": RegistryTool,
            "WORKFLOW": RegistryWorkflow, "DATA_SOURCE": RegistryDataSource,
            "USER": GuardianUser, "DEPARTMENT": RegistryDepartment, "ROLE": RegistryRole
        }
        model = table_map.get(entity_type)
        if not model: raise HTTPException(400, detail=ResponseHelper.error(message=f"Invalid entity type: {entity_type}", error_code="VALIDATION_ERROR").model_dump())
        
        entity = db.execute(select(model).filter_by(id=entity_id)).scalar_one_or_none()
        if not entity: raise HTTPException(422, detail=ResponseHelper.error(message=f"{entity_type} not found", error_code="NOT_FOUND").model_dump())
        if getattr(entity, 'status', 'ACTIVE') not in ["ACTIVE", "DRAFT"]:
            raise HTTPException(400, detail=ResponseHelper.error(message=f"{entity_type} is not in ACTIVE or DRAFT status", error_code="VALIDATION_ERROR").model_dump())
            
    check_entity(payload.source_entity_type, payload.source_entity_id)
    check_entity(payload.target_entity_type, payload.target_entity_id)
    
    if repo.check_duplicate_relationship(db, payload.source_entity_type, payload.source_entity_id, payload.target_entity_type, payload.target_entity_id, payload.relationship_type):
        raise HTTPException(409, detail=ResponseHelper.error(message="Duplicate active relationship exists", error_code="CONFLICT").model_dump())
        
    rel = repo.create_relationship(db, payload.model_dump())
    
    write_registry_audit(
        db=db, entity_type=payload.source_entity_type, entity_id=payload.source_entity_id, event_type="RELATIONSHIP_ADDED",
        changed_by=current_user.id, change_summary=f"{payload.source_entity_type} {payload.relationship_type} {payload.target_entity_type} relationship created"
    )
    
    return rel

def delete_relationship(db: Session, rel_id: UUID, current_user):
    rel = repo.get_relationship_by_id(db, rel_id)
    if not rel:
        raise HTTPException(404, detail=ResponseHelper.error(message="Relationship not found", error_code="NOT_FOUND").model_dump())
        
    rel = repo.change_relationship_status(db, rel, "INACTIVE")
    
    write_registry_audit(
        db=db, entity_type=rel.source_entity_type, entity_id=rel.source_entity_id, event_type="RELATIONSHIP_REMOVED",
        changed_by=current_user.id, change_summary=f"{rel.source_entity_type} {rel.relationship_type} {rel.target_entity_type} relationship removed"
    )
    return rel


# ---------------------------------------------------------
# Deletion Services
# ---------------------------------------------------------

def delete_model(db: Session, model_id: UUID, current_user):
    model = repo.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(404, detail=ResponseHelper.error(message="Model not found", error_code="NOT_FOUND").model_dump())
    
    before_state = to_dict(model)
    repo.delete_all_relationships_for_entity(db, "MODEL", model_id)
    repo.delete_entity(db, model)
    
    write_registry_audit(
        db=db, entity_type="MODEL", entity_id=model_id, event_type="DELETED",
        changed_by=current_user.id, before_json=before_state, change_summary="Model permanently deleted"
    )
    return model

def delete_agent(db: Session, agent_id: UUID, current_user):
    agent = repo.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(404, detail=ResponseHelper.error(message="Agent not found", error_code="NOT_FOUND").model_dump())
    
    before_state = to_dict(agent)
    repo.delete_all_relationships_for_entity(db, "AGENT", agent_id)
    repo.delete_entity(db, agent)
    
    write_registry_audit(
        db=db, entity_type="AGENT", entity_id=agent_id, event_type="DELETED",
        changed_by=current_user.id, before_json=before_state, change_summary="Agent permanently deleted"
    )
    return agent

def delete_tool(db: Session, tool_id: UUID, current_user):
    tool = repo.get_tool_by_id(db, tool_id)
    if not tool:
        raise HTTPException(404, detail=ResponseHelper.error(message="Tool not found", error_code="NOT_FOUND").model_dump())
    
    before_state = to_dict(tool)
    repo.delete_all_relationships_for_entity(db, "TOOL", tool_id)
    repo.delete_entity(db, tool)
    
    write_registry_audit(
        db=db, entity_type="TOOL", entity_id=tool_id, event_type="DELETED",
        changed_by=current_user.id, before_json=before_state, change_summary="Tool permanently deleted"
    )
    return tool

def delete_workflow(db: Session, workflow_id: UUID, current_user):
    workflow = repo.get_workflow_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(404, detail=ResponseHelper.error(message="Workflow not found", error_code="NOT_FOUND").model_dump())
    
    before_state = to_dict(workflow)
    repo.delete_all_relationships_for_entity(db, "WORKFLOW", workflow_id)
    repo.delete_entity(db, workflow)
    
    write_registry_audit(
        db=db, entity_type="WORKFLOW", entity_id=workflow_id, event_type="DELETED",
        changed_by=current_user.id, before_json=before_state, change_summary="Workflow permanently deleted"
    )
    return workflow

def delete_data_source(db: Session, source_id: UUID, current_user):
    source = repo.get_data_source_by_id(db, source_id)
    if not source:
        raise HTTPException(404, detail=ResponseHelper.error(message="Data Source not found", error_code="NOT_FOUND").model_dump())
    
    before_state = to_dict(source)
    repo.delete_all_relationships_for_entity(db, "DATA_SOURCE", source_id)
    repo.delete_entity(db, source)
    
    write_registry_audit(
        db=db, entity_type="DATA_SOURCE", entity_id=source_id, event_type="DELETED",
        changed_by=current_user.id, before_json=before_state, change_summary="Data Source permanently deleted"
    )
    return source

def delete_department(db: Session, dept_id: UUID, current_user):
    dept = repo.get_department_by_id(db, dept_id)
    if not dept:
        raise HTTPException(404, detail=ResponseHelper.error(message="Department not found", error_code="NOT_FOUND").model_dump())
    
    err_msg = repo.check_active_references(db, "DEPARTMENT", dept_id)
    if err_msg:
        raise HTTPException(400, detail=ResponseHelper.error(message=err_msg, error_code="VALIDATION_ERROR").model_dump())
        
    before_state = to_dict(dept)
    repo.delete_all_relationships_for_entity(db, "DEPARTMENT", dept_id)
    repo.delete_entity(db, dept)
    
    write_registry_audit(
        db=db, entity_type="DEPARTMENT", entity_id=dept_id, event_type="DELETED",
        changed_by=current_user.id, before_json=before_state, change_summary="Department permanently deleted"
    )
    return dept

def delete_role(db: Session, role_id: UUID, current_user):
    role = repo.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(404, detail=ResponseHelper.error(message="Role not found", error_code="NOT_FOUND").model_dump())
    
    err_msg = repo.check_active_references(db, "ROLE", role_id)
    if err_msg:
        raise HTTPException(400, detail=ResponseHelper.error(message=err_msg, error_code="VALIDATION_ERROR").model_dump())
        
    before_state = to_dict(role)
    repo.delete_all_relationships_for_entity(db, "ROLE", role_id)
    repo.delete_entity(db, role)
    
    write_registry_audit(
        db=db, entity_type="ROLE", entity_id=role_id, event_type="DELETED",
        changed_by=current_user.id, before_json=before_state, change_summary="Role permanently deleted"
    )
    return role

def delete_user(db: Session, user_id: UUID, current_user):
    user = repo.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404, detail=ResponseHelper.error(message="User not found", error_code="NOT_FOUND").model_dump())
    
    err_msg = repo.check_active_references(db, "USER", user_id)
    if err_msg:
        raise HTTPException(400, detail=ResponseHelper.error(message=err_msg, error_code="VALIDATION_ERROR").model_dump())
        
    before_state = to_dict(user)
    repo.delete_all_relationships_for_entity(db, "USER", user_id)
    repo.delete_entity(db, user)
    
    write_registry_audit(
        db=db, entity_type="USER", entity_id=user_id, event_type="DELETED",
        changed_by=current_user.id, before_json=before_state, change_summary="User permanently deleted"
    )
    return user

