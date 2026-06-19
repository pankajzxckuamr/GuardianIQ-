from typing import Tuple, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, asc, desc, or_
from app.modules.registry.models import (
    RegistryAIModel, RegistryAIAgent, RegistryTool, RegistryWorkflow,
    GuardianUser, RegistryDepartment, RegistryDataSource, RegistryRole,
    RegistryRelationship, RegistryAuditEvent, RegistryAIModelProvider,
    RegistryRegisterAll
)
import math
import sqlalchemy as sa

def resolve_user_uuid(db: Session, user_val) -> Optional[UUID]:
    if not user_val:
        return None
    if isinstance(user_val, UUID):
        return user_val
    if isinstance(user_val, str):
        try:
            return UUID(user_val)
        except ValueError:
            pass
            
    from app.modules.auth.models import User
    if isinstance(user_val, int):
        auth_user = db.query(User).filter(User.id == user_val).first()
        if auth_user:
            g_user = db.execute(select(GuardianUser).filter_by(email=auth_user.email)).scalar_one_or_none()
            if g_user:
                return g_user.id
                
    # Fallback to the first GuardianUser in the seed data
    g_user = db.execute(select(GuardianUser)).scalars().first()
    if g_user:
        return g_user.id
        
    return None

# ---------------------------------------------------------
# AI Models Repository
# ---------------------------------------------------------

def create_model(db: Session, data: dict, created_by: UUID) -> RegistryAIModel:
    created_by = resolve_user_uuid(db, created_by)
    model = RegistryAIModel(**data, created_by=created_by)
    db.add(model)
    db.flush() # flush to get the id without committing
    return model

def get_model_by_id(db: Session, model_id: UUID) -> Optional[RegistryAIModel]:
    res = db.execute(
        select(RegistryAIModel, GuardianUser.full_name, RegistryAIModelProvider.provider_name)
        .outerjoin(GuardianUser, RegistryAIModel.owner_user_id == GuardianUser.id)
        .outerjoin(RegistryAIModelProvider, RegistryAIModel.provider_id == RegistryAIModelProvider.id)
        .filter(RegistryAIModel.id == model_id)
    ).first()
    if res:
        model, owner_name, provider_name = res
        model.owner_name = owner_name
        model.provider_name = provider_name
        return model
    return None

def get_model_by_code(db: Session, code: str) -> Optional[RegistryAIModel]:
    return db.execute(select(RegistryAIModel).filter_by(model_code=code)).scalar_one_or_none()

def list_models(
    db: Session, filters: dict, page: int, page_size: int, sort_by: str, sort_dir: str
) -> Tuple[List[RegistryAIModel], int]:
    
    query = select(RegistryAIModel, GuardianUser.full_name, RegistryAIModelProvider.provider_name).outerjoin(
        GuardianUser, RegistryAIModel.owner_user_id == GuardianUser.id
    ).outerjoin(
        RegistryAIModelProvider, RegistryAIModel.provider_id == RegistryAIModelProvider.id
    )
    
    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.filter(
            or_(
                RegistryAIModel.model_name.ilike(search_term),
                RegistryAIModel.model_code.ilike(search_term)
            )
        )
    
    if filters.get("status"):
        query = query.filter(RegistryAIModel.status == filters["status"])
    if filters.get("model_type"):
        query = query.filter(RegistryAIModel.model_type == filters["model_type"])
    if filters.get("risk_level"):
        query = query.filter(RegistryAIModel.risk_level == filters["risk_level"])
    if filters.get("department_id"):
        query = query.filter(RegistryAIModel.department_id == filters["department_id"])

    # Sorting
    order_column = getattr(RegistryAIModel, sort_by, RegistryAIModel.created_at)
    if sort_dir.lower() == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(asc(order_column))
        
    # Count total
    total = db.execute(select(sa.func.count()).select_from(query.subquery())).scalar_one()

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    results = db.execute(query).all()
    items = []
    for model, owner_name, provider_name in results:
        model.owner_name = owner_name
        model.provider_name = provider_name
        items.append(model)
    return items, total

def update_model(db: Session, model: RegistryAIModel, data: dict, updated_by: UUID) -> RegistryAIModel:
    updated_by = resolve_user_uuid(db, updated_by)
    for key, value in data.items():
        if value is not None and hasattr(model, key):
            setattr(model, key, value)
    model.updated_by = updated_by
    db.flush()
    return model

def change_model_status(db: Session, model: RegistryAIModel, new_status: str, updated_by: UUID) -> RegistryAIModel:
    updated_by = resolve_user_uuid(db, updated_by)
    model.status = new_status
    model.updated_by = updated_by
    db.flush()
    return model


# ---------------------------------------------------------
# AI Agents Repository
# ---------------------------------------------------------

def create_agent(db: Session, data: dict, created_by: UUID) -> RegistryAIAgent:
    created_by = resolve_user_uuid(db, created_by)
    agent = RegistryAIAgent(**data, created_by=created_by)
    db.add(agent)
    db.flush()
    return agent

def get_agent_by_id(db: Session, agent_id: UUID) -> Optional[RegistryAIAgent]:
    res = db.execute(
        select(RegistryAIAgent, GuardianUser.full_name)
        .outerjoin(GuardianUser, RegistryAIAgent.owner_user_id == GuardianUser.id)
        .filter(RegistryAIAgent.id == agent_id)
    ).first()
    if res:
        agent, owner_name = res
        agent.owner_name = owner_name
        agent.provider_name = agent.metadata_json.get("provider_name") if agent.metadata_json else None
        return agent
    return None

def get_agent_by_code(db: Session, code: str) -> Optional[RegistryAIAgent]:
    return db.execute(select(RegistryAIAgent).filter_by(agent_code=code)).scalar_one_or_none()

def list_agents(
    db: Session, filters: dict, page: int, page_size: int, sort_by: str, sort_dir: str
) -> Tuple[List[RegistryAIAgent], int]:
    
    query = select(RegistryAIAgent, GuardianUser.full_name).outerjoin(
        GuardianUser, RegistryAIAgent.owner_user_id == GuardianUser.id
    )
    
    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.filter(
            or_(
                RegistryAIAgent.agent_name.ilike(search_term),
                RegistryAIAgent.agent_code.ilike(search_term)
            )
        )
    
    if filters.get("status"):
        query = query.filter(RegistryAIAgent.status == filters["status"])
    if filters.get("agent_type"):
        query = query.filter(RegistryAIAgent.agent_type == filters["agent_type"])
    if filters.get("risk_level"):
        query = query.filter(RegistryAIAgent.risk_level == filters["risk_level"])
    if filters.get("department_id"):
        query = query.filter(RegistryAIAgent.department_id == filters["department_id"])

    # Sorting
    order_column = getattr(RegistryAIAgent, sort_by, RegistryAIAgent.created_at)
    if sort_dir.lower() == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(asc(order_column))
        
    # Count total
    import sqlalchemy as sa
    total = db.execute(select(sa.func.count()).select_from(query.subquery())).scalar_one()

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    results = db.execute(query).all()
    items = []
    for agent, owner_name in results:
        agent.owner_name = owner_name
        agent.provider_name = agent.metadata_json.get("provider_name") if agent.metadata_json else None
        items.append(agent)
    return items, total

def update_agent(db: Session, agent: RegistryAIAgent, data: dict, updated_by: UUID) -> RegistryAIAgent:
    updated_by = resolve_user_uuid(db, updated_by)
    for key, value in data.items():
        if value is not None and hasattr(agent, key):
            setattr(agent, key, value)
    agent.updated_by = updated_by
    db.flush()
    return agent

def change_agent_status(db: Session, agent: RegistryAIAgent, new_status: str, updated_by: UUID) -> RegistryAIAgent:
    updated_by = resolve_user_uuid(db, updated_by)
    agent.status = new_status
    agent.updated_by = updated_by
    db.flush()
    return agent

# ---------------------------------------------------------
# Tools Repository
# ---------------------------------------------------------

def create_tool(db: Session, data: dict) -> RegistryTool:
    tool = RegistryTool(**data)
    db.add(tool)
    db.flush()
    return tool

def get_tool_by_id(db: Session, tool_id: UUID) -> Optional[RegistryTool]:
    res = db.execute(
        select(RegistryTool, GuardianUser.full_name)
        .outerjoin(GuardianUser, RegistryTool.owner_user_id == GuardianUser.id)
        .filter(RegistryTool.id == tool_id)
    ).first()
    if res:
        tool, owner_name = res
        tool.owner_name = owner_name
        tool.provider_name = tool.metadata_json.get("provider_name") if tool.metadata_json else None
        return tool
    return None

def get_tool_by_code(db: Session, code: str) -> Optional[RegistryTool]:
    return db.execute(select(RegistryTool).filter_by(tool_code=code)).scalar_one_or_none()

def list_tools(db: Session, filters: dict, page: int, page_size: int, sort_by: str, sort_dir: str) -> Tuple[List[RegistryTool], int]:
    query = select(RegistryTool, GuardianUser.full_name).outerjoin(
        GuardianUser, RegistryTool.owner_user_id == GuardianUser.id
    )
    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.filter(or_(RegistryTool.tool_name.ilike(search_term), RegistryTool.tool_code.ilike(search_term)))
    if filters.get("status"):
        query = query.filter(RegistryTool.status == filters["status"])
    if filters.get("tool_category"):
        query = query.filter(RegistryTool.tool_category == filters["tool_category"])
    if filters.get("access_mode"):
        query = query.filter(RegistryTool.access_mode == filters["access_mode"])
    if filters.get("sensitivity_level"):
        query = query.filter(RegistryTool.sensitivity_level == filters["sensitivity_level"])

    order_column = getattr(RegistryTool, sort_by, RegistryTool.created_at)
    query = query.order_by(desc(order_column) if sort_dir.lower() == "desc" else asc(order_column))
    
    total = db.execute(select(sa.func.count()).select_from(query.subquery())).scalar_one()
    results = db.execute(query.offset((page - 1) * page_size).limit(page_size)).all()
    items = []
    for tool, owner_name in results:
        tool.owner_name = owner_name
        tool.provider_name = tool.metadata_json.get("provider_name") if tool.metadata_json else None
        items.append(tool)
    return items, total

def update_tool(db: Session, tool: RegistryTool, data: dict) -> RegistryTool:
    for key, value in data.items():
        if value is not None and hasattr(tool, key):
            setattr(tool, key, value)
    db.flush()
    return tool

def change_tool_status(db: Session, tool: RegistryTool, new_status: str) -> RegistryTool:
    tool.status = new_status
    db.flush()
    return tool

# ---------------------------------------------------------
# Workflows Repository
# ---------------------------------------------------------

def create_workflow(db: Session, data: dict) -> RegistryWorkflow:
    workflow = RegistryWorkflow(**data)
    db.add(workflow)
    db.flush()
    return workflow

def get_workflow_by_id(db: Session, workflow_id: UUID) -> Optional[RegistryWorkflow]:
    OwnerUser = sa.orm.aliased(GuardianUser)
    ApproverUser = sa.orm.aliased(GuardianUser)
    
    res = db.execute(
        select(RegistryWorkflow, OwnerUser.full_name.label("owner_name"), ApproverUser.full_name.label("approver_name"), ApproverUser.email.label("approver_email"))
        .outerjoin(OwnerUser, RegistryWorkflow.owner_user_id == OwnerUser.id)
        .outerjoin(ApproverUser, RegistryWorkflow.approver_user_id == ApproverUser.id)
        .filter(RegistryWorkflow.id == workflow_id)
    ).first()
    
    if res:
        workflow, owner_name, approver_name, approver_email = res
        workflow.owner_name = owner_name
        workflow.approver_name = approver_name
        workflow.approver_email = approver_email
        return workflow
    return None

def get_workflow_by_code(db: Session, code: str) -> Optional[RegistryWorkflow]:
    return db.execute(select(RegistryWorkflow).filter_by(workflow_code=code)).scalar_one_or_none()

def list_workflows(db: Session, filters: dict, page: int, page_size: int, sort_by: str, sort_dir: str) -> Tuple[List[RegistryWorkflow], int]:
    OwnerUser = sa.orm.aliased(GuardianUser)
    ApproverUser = sa.orm.aliased(GuardianUser)

    query = select(RegistryWorkflow, OwnerUser.full_name.label("owner_name"), ApproverUser.full_name.label("approver_name"), ApproverUser.email.label("approver_email")).outerjoin(
        OwnerUser, RegistryWorkflow.owner_user_id == OwnerUser.id
    ).outerjoin(
        ApproverUser, RegistryWorkflow.approver_user_id == ApproverUser.id
    )

    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.filter(or_(RegistryWorkflow.workflow_name.ilike(search_term), RegistryWorkflow.workflow_code.ilike(search_term)))
    if filters.get("status"):
        query = query.filter(RegistryWorkflow.status == filters["status"])
    if filters.get("workflow_type"):
        query = query.filter(RegistryWorkflow.workflow_type == filters["workflow_type"])
    if filters.get("business_criticality"):
        query = query.filter(RegistryWorkflow.business_criticality == filters["business_criticality"])
    if filters.get("approval_required") is not None:
        query = query.filter(RegistryWorkflow.approval_required == filters["approval_required"])

    order_column = getattr(RegistryWorkflow, sort_by, RegistryWorkflow.created_at)
    query = query.order_by(desc(order_column) if sort_dir.lower() == "desc" else asc(order_column))
    
    total = db.execute(select(sa.func.count()).select_from(query.subquery())).scalar_one()
    results = db.execute(query.offset((page - 1) * page_size).limit(page_size)).all()
    
    items = []
    for workflow, owner_name, approver_name, approver_email in results:
        workflow.owner_name = owner_name
        workflow.approver_name = approver_name
        workflow.approver_email = approver_email
        items.append(workflow)
        
    return items, total

def update_workflow(db: Session, workflow: RegistryWorkflow, data: dict) -> RegistryWorkflow:
    for key, value in data.items():
        if value is not None and hasattr(workflow, key):
            setattr(workflow, key, value)
    db.flush()
    return workflow

def change_workflow_status(db: Session, workflow: RegistryWorkflow, new_status: str) -> RegistryWorkflow:
    workflow.status = new_status
    db.flush()
    return workflow

# ---------------------------------------------------------
# Summary Endpoint Aggregation
# ---------------------------------------------------------

def get_registry_summary(db: Session) -> dict:
    summary = {}

    def get_counts(model_cls, group_cols):
        result = {"total": db.execute(select(sa.func.count()).select_from(model_cls)).scalar_one()}
        for col_name in group_cols:
            col = getattr(model_cls, col_name)
            rows = db.execute(select(col, sa.func.count()).group_by(col)).all()
            result[f"by_{col_name}"] = {str(k): v for k, v in rows if k is not None}
        return result

    summary["models"] = get_counts(RegistryAIModel, ["status", "risk_level"])
    summary["agents"] = get_counts(RegistryAIAgent, ["status", "risk_level"])
    summary["tools"] = get_counts(RegistryTool, ["status", "sensitivity_level"])
    summary["workflows"] = get_counts(RegistryWorkflow, ["status", "business_criticality"])
    summary["users"] = get_counts(GuardianUser, ["status"])
    summary["departments"] = get_counts(RegistryDepartment, ["status"])
    summary["data_sources"] = get_counts(RegistryDataSource, ["status", "classification"])

    return summary

# ---------------------------------------------------------
# Departments Repository
# ---------------------------------------------------------

def create_department(db: Session, data: dict) -> RegistryDepartment:
    dept = RegistryDepartment(**data)
    db.add(dept)
    db.flush()
    return dept

def get_department_by_id(db: Session, dept_id: UUID) -> Optional[RegistryDepartment]:
    return db.execute(select(RegistryDepartment).filter_by(id=dept_id)).scalar_one_or_none()

def get_department_by_code(db: Session, code: str) -> Optional[RegistryDepartment]:
    return db.execute(select(RegistryDepartment).filter_by(department_code=code)).scalar_one_or_none()

def list_departments(db: Session, filters: dict, page: int, page_size: int, sort_by: str, sort_dir: str) -> Tuple[List[RegistryDepartment], int]:
    query = select(RegistryDepartment)
    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.filter(or_(RegistryDepartment.department_name.ilike(search_term), RegistryDepartment.department_code.ilike(search_term)))
    if filters.get("status"):
        query = query.filter(RegistryDepartment.status == filters["status"])

    order_column = getattr(RegistryDepartment, sort_by, RegistryDepartment.created_at)
    query = query.order_by(desc(order_column) if sort_dir.lower() == "desc" else asc(order_column))
    
    total = db.execute(select(sa.func.count()).select_from(query.subquery())).scalar_one()
    items = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return items, total

def update_department(db: Session, dept: RegistryDepartment, data: dict) -> RegistryDepartment:
    for key, value in data.items():
        if value is not None and hasattr(dept, key):
            setattr(dept, key, value)
    db.flush()
    return dept

def change_department_status(db: Session, dept: RegistryDepartment, new_status: str) -> RegistryDepartment:
    dept.status = new_status
    db.flush()
    return dept

def lookup_departments(db: Session) -> List[RegistryDepartment]:
    return db.execute(select(RegistryDepartment).filter_by(status="ACTIVE")).scalars().all()

# ---------------------------------------------------------
# Roles Repository
# ---------------------------------------------------------

def create_role(db: Session, data: dict) -> RegistryRole:
    role = RegistryRole(**data)
    db.add(role)
    db.flush()
    return role

def get_role_by_id(db: Session, role_id: UUID) -> Optional[RegistryRole]:
    return db.execute(select(RegistryRole).filter_by(id=role_id)).scalar_one_or_none()

def get_role_by_code(db: Session, code: str) -> Optional[RegistryRole]:
    return db.execute(select(RegistryRole).filter_by(role_code=code)).scalar_one_or_none()

def list_roles(db: Session, filters: dict, page: int, page_size: int, sort_by: str, sort_dir: str) -> Tuple[List[RegistryRole], int]:
    query = select(RegistryRole)
    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.filter(or_(RegistryRole.role_name.ilike(search_term), RegistryRole.role_code.ilike(search_term)))
    if filters.get("status"):
        query = query.filter(RegistryRole.status == filters["status"])

    order_column = getattr(RegistryRole, sort_by, RegistryRole.created_at)
    query = query.order_by(desc(order_column) if sort_dir.lower() == "desc" else asc(order_column))
    
    total = db.execute(select(sa.func.count()).select_from(query.subquery())).scalar_one()
    items = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return items, total

def update_role(db: Session, role: RegistryRole, data: dict) -> RegistryRole:
    for key, value in data.items():
        if value is not None and hasattr(role, key):
            setattr(role, key, value)
    db.flush()
    return role

def change_role_status(db: Session, role: RegistryRole, new_status: str) -> RegistryRole:
    role.status = new_status
    db.flush()
    return role

def lookup_roles(db: Session) -> List[RegistryRole]:
    return db.execute(select(RegistryRole)).scalars().all()

# ---------------------------------------------------------
# Guardian Users Repository
# ---------------------------------------------------------

def create_user(db: Session, data: dict) -> GuardianUser:
    user = GuardianUser(**data)
    db.add(user)
    db.flush()
    return user

def get_user_by_id(db: Session, user_id: UUID) -> Optional[GuardianUser]:
    return db.execute(select(GuardianUser).filter_by(id=user_id)).scalar_one_or_none()

def get_user_by_email(db: Session, email: str) -> Optional[GuardianUser]:
    return db.execute(select(GuardianUser).filter_by(email=email)).scalar_one_or_none()

def list_users(db: Session, filters: dict, page: int, page_size: int, sort_by: str, sort_dir: str) -> Tuple[List[GuardianUser], int]:
    query = select(GuardianUser)
    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.filter(or_(GuardianUser.full_name.ilike(search_term), GuardianUser.email.ilike(search_term)))
    if filters.get("status"):
        query = query.filter(GuardianUser.status == filters["status"])

    order_column = getattr(GuardianUser, sort_by, GuardianUser.created_at)
    query = query.order_by(desc(order_column) if sort_dir.lower() == "desc" else asc(order_column))
    
    total = db.execute(select(sa.func.count()).select_from(query.subquery())).scalar_one()
    items = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return items, total

def update_user(db: Session, user: GuardianUser, data: dict) -> GuardianUser:
    for key, value in data.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    db.flush()
    return user

def change_user_status(db: Session, user: GuardianUser, new_status: str) -> GuardianUser:
    user.status = new_status
    db.flush()
    return user

def lookup_users(db: Session) -> List[GuardianUser]:
    return db.execute(select(GuardianUser)).scalars().all()

# ---------------------------------------------------------
# Data Sources Repository
# ---------------------------------------------------------

def create_data_source(db: Session, data: dict) -> RegistryDataSource:
    source = RegistryDataSource(**data)
    db.add(source)
    db.flush()
    return source

def get_data_source_by_id(db: Session, source_id: UUID) -> Optional[RegistryDataSource]:
    return db.execute(select(RegistryDataSource).filter_by(id=source_id)).scalar_one_or_none()

def get_data_source_by_code(db: Session, code: str) -> Optional[RegistryDataSource]:
    return db.execute(select(RegistryDataSource).filter_by(source_code=code)).scalar_one_or_none()

def list_data_sources(db: Session, filters: dict, page: int, page_size: int, sort_by: str, sort_dir: str) -> Tuple[List[RegistryDataSource], int]:
    query = select(RegistryDataSource)
    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.filter(or_(RegistryDataSource.source_name.ilike(search_term), RegistryDataSource.source_code.ilike(search_term)))
    if filters.get("status"):
        query = query.filter(RegistryDataSource.status == filters["status"])

    order_column = getattr(RegistryDataSource, sort_by, RegistryDataSource.created_at)
    query = query.order_by(desc(order_column) if sort_dir.lower() == "desc" else asc(order_column))
    
    total = db.execute(select(sa.func.count()).select_from(query.subquery())).scalar_one()
    items = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return items, total

def update_data_source(db: Session, source: RegistryDataSource, data: dict) -> RegistryDataSource:
    for key, value in data.items():
        if value is not None and hasattr(source, key):
            setattr(source, key, value)
    db.flush()
    return source

def change_data_source_status(db: Session, source: RegistryDataSource, new_status: str) -> RegistryDataSource:
    source.status = new_status
    return source

# ---------------------------------------------------------
# Relationships Repository
# ---------------------------------------------------------

def create_relationship(db: Session, data: dict) -> RegistryRelationship:
    # Filter out metadata_json since the DB model registry_relationships doesn't have it
    filtered_data = {k: v for k, v in data.items() if k != "metadata_json"}
    rel = RegistryRelationship(**filtered_data)
    db.add(rel)
    db.flush()
    return rel

def get_relationship_by_id(db: Session, rel_id: UUID) -> Optional[RegistryRelationship]:
    return db.execute(select(RegistryRelationship).filter_by(id=rel_id)).scalar_one_or_none()

def check_duplicate_relationship(db: Session, source_type: str, source_id: UUID, target_type: str, target_id: UUID, rel_type: str) -> bool:
    count = db.execute(select(sa.func.count()).select_from(RegistryRelationship).filter_by(
        source_entity_type=source_type, source_entity_id=source_id,
        target_entity_type=target_type, target_entity_id=target_id,
        relationship_type=rel_type, status="ACTIVE"
    )).scalar()
    return count > 0

def list_relationships_for_entity(db: Session, entity_type: str, entity_id: UUID):
    outgoing = db.execute(select(RegistryRelationship).filter_by(source_entity_type=entity_type, source_entity_id=entity_id, status="ACTIVE")).scalars().all()
    incoming = db.execute(select(RegistryRelationship).filter_by(target_entity_type=entity_type, target_entity_id=entity_id, status="ACTIVE")).scalars().all()
    return outgoing, incoming

def change_relationship_status(db: Session, rel: RegistryRelationship, new_status: str) -> RegistryRelationship:
    rel.status = new_status
    db.flush()
    return rel

# ---------------------------------------------------------
# Audit Repository
# ---------------------------------------------------------

def list_audit_events(db: Session, entity_type: str, entity_id: UUID, event_type: Optional[str], page: int, page_size: int) -> Tuple[List[dict], int]:
    query = select(RegistryAuditEvent, GuardianUser).outerjoin(GuardianUser, RegistryAuditEvent.changed_by == GuardianUser.id).filter(
        RegistryAuditEvent.entity_type == entity_type,
        RegistryAuditEvent.entity_id == entity_id
    )
    if event_type:
        query = query.filter(RegistryAuditEvent.event_type == event_type)
        
    query = query.order_by(desc(RegistryAuditEvent.created_at))
    total = db.execute(select(sa.func.count()).select_from(query.subquery())).scalar_one()
    
    results = db.execute(query.offset((page - 1) * page_size).limit(page_size)).all()
    
    items = []
    for audit, user in results:
        audit_dict = {
            "id": audit.id,
            "entity_type": audit.entity_type,
            "entity_id": audit.entity_id,
            "event_type": audit.event_type,
            "changed_by": audit.changed_by,
            "changed_by_name": user.full_name if user else None,
            "changed_by_email": user.email if user else None,
            "before_json": audit.before_json,
            "after_json": audit.after_json,
            "change_summary": audit.change_summary,
            "created_at": audit.created_at
        }
        items.append(audit_dict)
    
    return items, total

# ---------------------------------------------------------
# Search Repository
# ---------------------------------------------------------

def global_search(db: Session, term: str) -> dict:
    search_term = f"%{term}%"
    
    def search_table(model, name_col, code_col, entity_type_str):
        query = select(model.id, getattr(model, name_col).label('name'), getattr(model, code_col).label('code'), model.status).filter(
            or_(getattr(model, name_col).ilike(search_term), getattr(model, code_col).ilike(search_term))
        ).limit(5)
        results = db.execute(query).all()
        return [{"id": r.id, "name": r.name, "code": r.code, "entity_type": entity_type_str, "status": r.status} for r in results]

    return {
        "models": search_table(RegistryAIModel, "model_name", "model_code", "MODEL"),
        "agents": search_table(RegistryAIAgent, "agent_name", "agent_code", "AGENT"),
        "tools": search_table(RegistryTool, "tool_name", "tool_code", "TOOL"),
        "workflows": search_table(RegistryWorkflow, "workflow_name", "workflow_code", "WORKFLOW"),
        "users": search_table(GuardianUser, "full_name", "email", "USER"),
        "data_sources": search_table(RegistryDataSource, "source_name", "source_code", "DATA_SOURCE")
    }

def get_entity_name(db: Session, entity_type: str, entity_id: UUID) -> str:
    table_map = {
        "MODEL": (RegistryAIModel, "model_name"),
        "AGENT": (RegistryAIAgent, "agent_name"),
        "TOOL": (RegistryTool, "tool_name"),
        "WORKFLOW": (RegistryWorkflow, "workflow_name"),
        "DATA_SOURCE": (RegistryDataSource, "source_name"),
        "USER": (GuardianUser, "full_name"),
        "DEPARTMENT": (RegistryDepartment, "department_name"),
        "ROLE": (RegistryRole, "role_name")
    }
    if entity_type not in table_map: return "Unknown"
    model, name_col = table_map[entity_type]
    result = db.execute(select(getattr(model, name_col)).filter(model.id == entity_id)).scalar_one_or_none()
    return result or "Unknown"


# ---------------------------------------------------------
# Deletion and Cascade Helpers
# ---------------------------------------------------------

def delete_entity(db: Session, entity) -> None:
    db.delete(entity)
    db.flush()

def delete_all_relationships_for_entity(db: Session, entity_type: str, entity_id: UUID) -> None:
    db.execute(
        sa.delete(RegistryRelationship).filter(
            or_(
                sa.and_(RegistryRelationship.source_entity_type == entity_type, RegistryRelationship.source_entity_id == entity_id),
                sa.and_(RegistryRelationship.target_entity_type == entity_type, RegistryRelationship.target_entity_id == entity_id)
            )
        )
    )
    db.flush()

def check_active_references(db: Session, entity_type: str, entity_id: UUID) -> Optional[str]:
    if entity_type == "DEPARTMENT":
        if db.execute(select(sa.func.count()).select_from(RegistryDepartment).filter(RegistryDepartment.parent_department_id == entity_id, RegistryDepartment.status != "RETIRED")).scalar() > 0:
            return "This department is referenced as a parent department by other departments."
        if db.execute(select(sa.func.count()).select_from(GuardianUser).filter(GuardianUser.department_id == entity_id, GuardianUser.status != "RETIRED")).scalar() > 0:
            return "This department is referenced by active users."
        if db.execute(select(sa.func.count()).select_from(RegistryAIModel).filter(RegistryAIModel.department_id == entity_id, RegistryAIModel.status != "RETIRED")).scalar() > 0:
            return "This department is referenced by registered AI models."
        if db.execute(select(sa.func.count()).select_from(RegistryAIAgent).filter(RegistryAIAgent.department_id == entity_id, RegistryAIAgent.status != "RETIRED")).scalar() > 0:
            return "This department is referenced by registered AI agents."
        if db.execute(select(sa.func.count()).select_from(RegistryWorkflow).filter(RegistryWorkflow.department_id == entity_id, RegistryWorkflow.status != "RETIRED")).scalar() > 0:
            return "This department is referenced by registered workflows."
        if db.execute(select(sa.func.count()).select_from(RegistryDataSource).filter(RegistryDataSource.department_id == entity_id, RegistryDataSource.status != "RETIRED")).scalar() > 0:
            return "This department is referenced by registered data sources."

    elif entity_type == "ROLE":
        if db.execute(select(sa.func.count()).select_from(GuardianUser).filter(GuardianUser.role_id == entity_id, GuardianUser.status != "RETIRED")).scalar() > 0:
            return "This role is assigned to active users."

    elif entity_type == "USER":
        if db.execute(select(sa.func.count()).select_from(RegistryAIModel).filter(RegistryAIModel.owner_user_id == entity_id, RegistryAIModel.status != "RETIRED")).scalar() > 0:
            return "This user is the owner of registered AI models."
        if db.execute(select(sa.func.count()).select_from(RegistryAIAgent).filter(RegistryAIAgent.owner_user_id == entity_id, RegistryAIAgent.status != "RETIRED")).scalar() > 0:
            return "This user is the owner of registered AI agents."
        if db.execute(select(sa.func.count()).select_from(RegistryTool).filter(RegistryTool.owner_user_id == entity_id, RegistryTool.status != "RETIRED")).scalar() > 0:
            return "This user is the owner of registered tools."
        if db.execute(select(sa.func.count()).select_from(RegistryWorkflow).filter(RegistryWorkflow.owner_user_id == entity_id, RegistryWorkflow.status != "RETIRED")).scalar() > 0:
            return "This user is the owner of registered workflows."
        if db.execute(select(sa.func.count()).select_from(RegistryDataSource).filter(RegistryDataSource.owner_user_id == entity_id, RegistryDataSource.status != "RETIRED")).scalar() > 0:
            return "This user is the owner of registered data sources."
        if db.execute(select(sa.func.count()).select_from(RegistryDepartment).filter(or_(RegistryDepartment.business_owner_user_id == entity_id, RegistryDepartment.escalation_owner_user_id == entity_id), RegistryDepartment.status != "RETIRED")).scalar() > 0:
            return "This user is referenced as a business or escalation owner for departments."

    return None

def create_register_all(db: Session, data: dict, created_by: UUID) -> RegistryRegisterAll:
    created_by = resolve_user_uuid(db, created_by)
    reg_all = RegistryRegisterAll(**data, created_by=created_by)
    db.add(reg_all)
    db.flush()
    return reg_all

def get_register_all_by_id(db: Session, reg_all_id: UUID) -> Optional[RegistryRegisterAll]:
    query = (
        select(
            RegistryRegisterAll,
            RegistryDepartment.department_name,
            RegistryRole.role_name,
            GuardianUser.full_name.label("user_name"),
            RegistryDataSource.source_name.label("data_source_name"),
            RegistryAIModel.model_name,
            RegistryAIAgent.agent_name,
            RegistryTool.tool_name,
            RegistryWorkflow.workflow_name
        )
        .outerjoin(RegistryDepartment, RegistryRegisterAll.department_id == RegistryDepartment.id)
        .outerjoin(RegistryRole, RegistryRegisterAll.role_id == RegistryRole.id)
        .outerjoin(GuardianUser, RegistryRegisterAll.user_id == GuardianUser.id)
        .outerjoin(RegistryDataSource, RegistryRegisterAll.data_source_id == RegistryDataSource.id)
        .outerjoin(RegistryAIModel, RegistryRegisterAll.model_id == RegistryAIModel.id)
        .outerjoin(RegistryAIAgent, RegistryRegisterAll.agent_id == RegistryAIAgent.id)
        .outerjoin(RegistryTool, RegistryRegisterAll.tool_id == RegistryTool.id)
        .outerjoin(RegistryWorkflow, RegistryRegisterAll.workflow_id == RegistryWorkflow.id)
        .filter(RegistryRegisterAll.id == reg_all_id)
    )
    res = db.execute(query).first()
    if res:
        reg, dept, role, user, ds, model, agent, tool, wf = res
        reg.department_name = dept
        reg.role_name = role
        reg.user_name = user
        reg.data_source_name = ds
        reg.model_name = model
        reg.agent_name = agent
        reg.tool_name = tool
        reg.workflow_name = wf
        return reg
    return None

def list_register_all(
    db: Session, filters: dict, page: int, page_size: int, sort_by: str, sort_dir: str
) -> Tuple[List[RegistryRegisterAll], int]:
    query = (
        select(
            RegistryRegisterAll,
            RegistryDepartment.department_name,
            RegistryRole.role_name,
            GuardianUser.full_name.label("user_name"),
            RegistryDataSource.source_name.label("data_source_name"),
            RegistryAIModel.model_name,
            RegistryAIAgent.agent_name,
            RegistryTool.tool_name,
            RegistryWorkflow.workflow_name
        )
        .outerjoin(RegistryDepartment, RegistryRegisterAll.department_id == RegistryDepartment.id)
        .outerjoin(RegistryRole, RegistryRegisterAll.role_id == RegistryRole.id)
        .outerjoin(GuardianUser, RegistryRegisterAll.user_id == GuardianUser.id)
        .outerjoin(RegistryDataSource, RegistryRegisterAll.data_source_id == RegistryDataSource.id)
        .outerjoin(RegistryAIModel, RegistryRegisterAll.model_id == RegistryAIModel.id)
        .outerjoin(RegistryAIAgent, RegistryRegisterAll.agent_id == RegistryAIAgent.id)
        .outerjoin(RegistryTool, RegistryRegisterAll.tool_id == RegistryTool.id)
        .outerjoin(RegistryWorkflow, RegistryRegisterAll.workflow_id == RegistryWorkflow.id)
    )
    
    if filters.get("search"):
        search_term = f"%{filters['search']}%"
        query = query.filter(RegistryRegisterAll.name.ilike(search_term))
        
    if filters.get("workflow_id"):
        query = query.filter(RegistryRegisterAll.workflow_id == filters["workflow_id"])

    order_column = getattr(RegistryRegisterAll, sort_by, RegistryRegisterAll.created_at)
    if sort_dir.lower() == "desc":
        query = query.order_by(desc(order_column))
    else:
        query = query.order_by(asc(order_column))

    total = db.execute(select(sa.func.count()).select_from(query.subquery())).scalar_one()

    results = db.execute(query.offset((page - 1) * page_size).limit(page_size)).all()
    items = []
    for reg, dept, role, user, ds, model, agent, tool, wf in results:
        reg.department_name = dept
        reg.role_name = role
        reg.user_name = user
        reg.data_source_name = ds
        reg.model_name = model
        reg.agent_name = agent
        reg.tool_name = tool
        reg.workflow_name = wf
        items.append(reg)
    return items, total


