import inspect
import sqlalchemy as sa
from sqlalchemy.future import select
from uuid import UUID
from app.modules.audit.models import AuditEvent
from app.modules.registry.models import GuardianUser
from app.modules.auth.models import User
from app.modules.audit.event_codes import WorkflowEventCode

async def execute_statement(db, stmt):
    res = db.execute(stmt)
    if inspect.isawaitable(res):
        return await res
    return res

async def commit_session(db):
    if hasattr(db, "commit") and inspect.iscoroutinefunction(db.commit):
        await db.commit()
    else:
        db.commit()

class GovernanceEventService:
    async def publish_event(
        self,
        event_code: WorkflowEventCode,
        entity_type: str,
        entity_id: UUID,
        actor_type: str,   # USER, SYSTEM, MACHINE_ACTOR
        actor_id: UUID | None,
        action_type: str,
        event_summary: str,
        event_payload: dict,
        db
    ) -> None:
        """Inserts a single event into the legacy audit_events table. No update or delete allowed."""
        # Resolve actor_id (UUID of GuardianUser) to integer User.id by mapping their email address
        int_actor_id = None
        if actor_id:
            guardian_stmt = select(GuardianUser.email).where(GuardianUser.id == actor_id)
            guardian_res = await execute_statement(db, guardian_stmt)
            email = guardian_res.scalar()
            
            if email:
                user_stmt = select(User.id).where(User.email == email)
                user_res = await execute_statement(db, user_stmt)
                int_actor_id = user_res.scalar()

        # Build metadata structure to hold UUID values and rich payload
        meta = {
            "entity_id": str(entity_id) if entity_id else None,
            "actor_type": actor_type,
            "actor_id": str(actor_id) if actor_id else None,
            "event_summary": event_summary,
            "payload": event_payload or {}
        }

        # Create record. entity_id column is left as None because it expects an Integer,
        # and UUID values are preserved inside event_metadata.
        event_type_str = event_code.value if hasattr(event_code, "value") else str(event_code)
        audit_event = AuditEvent(
            event_type=event_type_str,
            entity_type=entity_type,
            entity_id=None,
            actor_user_id=int_actor_id,
            action=action_type,
            event_metadata=meta
        )
        db.add(audit_event)
        await commit_session(db)

    async def publish_batch(self, events: list[dict], db) -> None:
        """Inserts a batch of events into the audit_events table."""
        records = []
        for evt in events:
            event_code = evt.get("event_code")
            entity_type = evt.get("entity_type")
            entity_id = evt.get("entity_id")
            actor_type = evt.get("actor_type")
            actor_id = evt.get("actor_id")
            action_type = evt.get("action_type")
            event_summary = evt.get("event_summary")
            event_payload = evt.get("event_payload", {})

            int_actor_id = None
            if actor_id:
                guardian_stmt = select(GuardianUser.email).where(GuardianUser.id == actor_id)
                guardian_res = await execute_statement(db, guardian_stmt)
                email = guardian_res.scalar()
                
                if email:
                    user_stmt = select(User.id).where(User.email == email)
                    user_res = await execute_statement(db, user_stmt)
                    int_actor_id = user_res.scalar()

            meta = {
                "entity_id": str(entity_id) if entity_id else None,
                "actor_type": actor_type,
                "actor_id": str(actor_id) if actor_id else None,
                "event_summary": event_summary,
                "payload": event_payload
            }

            event_type_str = event_code.value if hasattr(event_code, "value") else str(event_code)
            records.append(AuditEvent(
                event_type=event_type_str,
                entity_type=entity_type,
                entity_id=None,
                actor_user_id=int_actor_id,
                action=action_type,
                event_metadata=meta
            ))
        
        db.add_all(records)
        await commit_session(db)

    async def get_timeline(self, entity_type: str, entity_id: UUID, db) -> list:
        """Retrieves events for the given entity sorted chronologically."""
        stmt = (
            select(AuditEvent)
            .where(
                AuditEvent.entity_type == entity_type,
                sa.or_(
                    sa.func.cast(AuditEvent.entity_id, sa.String) == str(entity_id),
                    sa.func.json_extract_path_text(AuditEvent.event_metadata, 'entity_id') == str(entity_id)
                )
            )
            .order_by(AuditEvent.created_at.asc())
        )
        res = await execute_statement(db, stmt)
        return list(res.scalars().all())
