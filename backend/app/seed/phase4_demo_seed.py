import logging
import random
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal
from app.modules.events.service import EventPublisherService
from app.modules.events.schemas import GovernanceEventCreate
from app.modules.auth.models import User
from app.core.middleware import set_user_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_demo_governance_events():
    db: Session = SessionLocal()
    try:
        user_res = db.query(User).first()
        if not user_res:
            logger.warning("No user found to use as tenant. Please seed users first.")
            return

        tenant_id = user_res.id
        set_user_context(str(tenant_id), user_res.email)

        publisher = EventPublisherService()

        # Generate some past events
        now = datetime.now(timezone.utc)
        
        events_to_create = [
            {
                "type": "WORKFLOW_RUN_STARTED",
                "category": "Workflow",
                "classification": "INTERNAL",
                "risk": "LOW"
            },
            {
                "type": "POLICY_VIOLATED",
                "category": "Violation",
                "classification": "CONFIDENTIAL",
                "risk": "HIGH"
            },
            {
                "type": "UNAUTHORIZED_ACCESS_BLOCKED",
                "category": "Violation",
                "classification": "RESTRICTED",
                "risk": "CRITICAL"
            },
            {
                "type": "SLA_BREACHED",
                "category": "Workflow",
                "classification": "INTERNAL",
                "risk": "MEDIUM"
            },
            {
                "type": "AGENT_ACTION_BLOCKED",
                "category": "Agent",
                "classification": "CONFIDENTIAL",
                "risk": "HIGH"
            },
            {
                "type": "USER_LOGIN",
                "category": "Identity",
                "classification": "CONFIDENTIAL",
                "risk": "LOW"
            },
            {
                "type": "APPROVAL_REQUESTED",
                "category": "Approval",
                "classification": "CONFIDENTIAL",
                "risk": "LOW"
            }
        ]

        logger.info(f"Seeding 20 demo governance events for tenant {tenant_id}...")
        
        for i in range(20):
            template = random.choice(events_to_create)
            occurred_at = now - timedelta(hours=random.randint(1, 72), minutes=random.randint(0, 59))
            
            event_data = GovernanceEventCreate(
                event_type=template["type"],
                event_category=template["category"],
                event_version="1.0",
                occurred_at=occurred_at,
                source_service="demo_seeder",
                actor_json={"user_id": str(tenant_id), "roles": ["ADMIN"]},
                subject_json={"entity_type": "demo_entity", "entity_id": str(uuid4())},
                risk_context_json={"risk_level": template["risk"]},
                classification=template["classification"],
                payload_json={"demo": True, "iteration": i}
            )
            
            # Using private method to bypass strict request context checks in some middlewares
            enriched = publisher.enrich_event(event_data, tenant_id)
            event_model = publisher.append_event(db, enriched)
            
            # Add to outbox as well to match real flow
            from app.modules.events.models import EventOutbox
            outbox_entry = EventOutbox(
                event_id=event_model.event_id,
                tenant_id=tenant_id,
                destination="internal_bus",
                payload_json=event_model.payload_json,
                status="PENDING",
                retry_count=0,
                max_retries=5
            )
            db.add(outbox_entry)

        db.commit()
        logger.info("Successfully seeded demo governance events!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding demo events: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_governance_events()
