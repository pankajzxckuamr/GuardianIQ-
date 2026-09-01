from typing import Optional
from uuid import UUID
from sqlalchemy import event, insert
from app.shared.mixins import GovernableMixin
from app.modules.registry.models import RegistryAuditEvent
from app.core.middleware import get_user_context

def get_current_actor_id() -> Optional[UUID]:
    try:
        ctx = get_user_context()
        if ctx and ctx.get("user_id"):
            return UUID(ctx["user_id"])
    except Exception:
        pass
    return None

def after_insert_listener(mapper, connection, target: GovernableMixin):
    actor_id = get_current_actor_id()
    object_type = getattr(target, "__object_type__", target.__class__.__name__.upper())
    connection.execute(
        insert(RegistryAuditEvent).values(
            event_type=f"{object_type}_CREATED",
            entity_type=object_type.lower(),
            entity_id=str(target.id) if target.id else None,
            actor_user_id=actor_id,
            action="CREATED",
            event_metadata={
                "change_summary": f"Created {object_type} entity",
                "before_json": None,
                "after_json": target.metadata_json or {}
            }
        )
    )

def after_update_listener(mapper, connection, target: GovernableMixin):
    actor_id = get_current_actor_id()
    object_type = getattr(target, "__object_type__", target.__class__.__name__.upper())
    connection.execute(
        insert(RegistryAuditEvent).values(
            event_type=f"{object_type}_UPDATED",
            entity_type=object_type.lower(),
            entity_id=str(target.id) if target.id else None,
            actor_user_id=actor_id,
            action="UPDATED",
            event_metadata={
                "change_summary": f"Updated {object_type} entity",
                "before_json": None,
                "after_json": target.metadata_json or {}
            }
        )
    )

def setup_audit_listeners():
    from app.modules.agent.models import Agent
    from app.modules.ai_model.models import AIModel
    from app.modules.datasource.models import DataSource
    from app.modules.department.models import Department
    from app.modules.registry.models import Tool, Workflow
    
    models = [Agent, AIModel, DataSource, Department, Tool, Workflow]
    for model in models:
        event.listen(model, "after_insert", after_insert_listener)
        event.listen(model, "after_update", after_update_listener)
