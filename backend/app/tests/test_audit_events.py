import unittest
from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.registry.models import GuardianUser
from app.modules.audit.models import AuditEvent
from app.modules.audit.event_codes import WorkflowEventCode
from app.modules.audit.event_service import GovernanceEventService

class AuditEventsIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.service = GovernanceEventService()

        # Login/setup references to get an active GuardianUser and User mapping
        from app.modules.registry.seed import seed_registry_data
        seed_registry_data(self.db)

        # Retrieve admin user UUID from guardian_users
        admin_guardian = self.db.query(GuardianUser).filter(GuardianUser.email == "admin@guardianiq.com").first()
        self.assertIsNotNone(admin_guardian, "Admin user not found in guardian_users")
        self.admin_uuid = admin_guardian.id

        admin_user = self.db.query(User).filter(User.email == "admin@guardianiq.com").first()
        self.assertIsNotNone(admin_user)
        self.admin_int_id = admin_user.id

        self.events_to_cleanup = []

    def tearDown(self):
        try:
            for event_id in self.events_to_cleanup:
                self.db.query(AuditEvent).filter(AuditEvent.id == event_id).delete()
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Cleanup failed: {e}")
        self.db.close()

    async def test_publish_event_success_and_resolve_actor(self):
        entity_id = uuid4()
        event_payload = {"test_key": "test_value"}
        
        # Publish event
        await self.service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_SCHEDULE_CREATED,
            entity_type="workflow_schedules",
            entity_id=entity_id,
            actor_type="USER",
            actor_id=self.admin_uuid,
            action_type="CREATE",
            event_summary="Workflow schedule created successfully",
            event_payload=event_payload,
            db=self.db
        )

        # Retrieve the event
        event = self.db.query(AuditEvent).filter(
            AuditEvent.event_type == WorkflowEventCode.WORKFLOW_SCHEDULE_CREATED.value
        ).order_by(AuditEvent.created_at.desc()).first()

        self.assertIsNotNone(event)
        self.events_to_cleanup.append(event.id)
        
        self.assertEqual(event.event_type, "WORKFLOW_SCHEDULE_CREATED")
        self.assertEqual(event.entity_type, "workflow_schedules")
        self.assertEqual(event.actor_user_id, self.admin_int_id)
        self.assertEqual(event.action, "CREATE")
        
        # Verify metadata holds original UUIDs
        meta = event.event_metadata
        self.assertIsNotNone(meta)
        self.assertEqual(meta["entity_id"], str(entity_id))
        self.assertEqual(meta["actor_id"], str(self.admin_uuid))
        self.assertEqual(meta["actor_type"], "USER")
        self.assertEqual(meta["event_summary"], "Workflow schedule created successfully")
        self.assertEqual(meta["payload"], event_payload)

    async def test_publish_batch_success(self):
        entity_id1 = uuid4()
        entity_id2 = uuid4()
        
        events = [
            {
                "event_code": WorkflowEventCode.WORKFLOW_RUN_QUEUED,
                "entity_type": "workflow_runs",
                "entity_id": entity_id1,
                "actor_type": "SYSTEM",
                "actor_id": None,
                "action_type": "QUEUE",
                "event_summary": "Workflow run queued",
                "event_payload": {"run_no": 1}
            },
            {
                "event_code": WorkflowEventCode.WORKFLOW_RUN_STARTED,
                "entity_type": "workflow_runs",
                "entity_id": entity_id2,
                "actor_type": "USER",
                "actor_id": self.admin_uuid,
                "action_type": "START",
                "event_summary": "Workflow run started",
                "event_payload": {"run_no": 2}
            }
        ]

        await self.service.publish_batch(events, db=self.db)

        # Retrieve events
        inserted_events = self.db.query(AuditEvent).filter(
            AuditEvent.event_type.in_(["WORKFLOW_RUN_QUEUED", "WORKFLOW_RUN_STARTED"])
        ).order_by(AuditEvent.created_at.desc()).limit(2).all()

        self.assertEqual(len(inserted_events), 2)
        for e in inserted_events:
            self.events_to_cleanup.append(e.id)

        # Check mapping for second event (USER actor)
        user_event = [e for e in inserted_events if e.event_type == "WORKFLOW_RUN_STARTED"][0]
        self.assertEqual(user_event.actor_user_id, self.admin_int_id)
        self.assertEqual(user_event.event_metadata["entity_id"], str(entity_id2))

        # Check mapping for first event (SYSTEM actor)
        sys_event = [e for e in inserted_events if e.event_type == "WORKFLOW_RUN_QUEUED"][0]
        self.assertIsNone(sys_event.actor_user_id)
        self.assertEqual(sys_event.event_metadata["entity_id"], str(entity_id1))

    async def test_get_timeline_sorted(self):
        entity_id = uuid4()
        
        # Publish two events sequentially for the same entity
        await self.service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_RUN_STARTED,
            entity_type="workflow_runs",
            entity_id=entity_id,
            actor_type="SYSTEM",
            actor_id=None,
            action_type="START",
            event_summary="Run started",
            event_payload={},
            db=self.db
        )
        
        await self.service.publish_event(
            event_code=WorkflowEventCode.WORKFLOW_RUN_COMPLETED,
            entity_type="workflow_runs",
            entity_id=entity_id,
            actor_type="SYSTEM",
            actor_id=None,
            action_type="COMPLETE",
            event_summary="Run completed",
            event_payload={},
            db=self.db
        )

        timeline = await self.service.get_timeline(entity_type="workflow_runs", entity_id=entity_id, db=self.db)
        self.assertEqual(len(timeline), 2)
        for e in timeline:
            self.events_to_cleanup.append(e.id)

        # Verify timeline is in ascending order
        self.assertEqual(timeline[0].event_type, "WORKFLOW_RUN_STARTED")
        self.assertEqual(timeline[1].event_type, "WORKFLOW_RUN_COMPLETED")
        self.assertTrue(timeline[0].created_at <= timeline[1].created_at)

    def test_no_update_or_delete_methods(self):
        # Verify that class contains only publish_event, publish_batch, and get_timeline
        methods = [attr for attr in dir(GovernanceEventService) if not attr.startswith("__")]
        self.assertIn("publish_event", methods)
        self.assertIn("publish_batch", methods)
        self.assertIn("get_timeline", methods)
        
        # Assert no delete or update methods exist
        self.assertNotIn("update", methods)
        self.assertNotIn("delete", methods)
        self.assertNotIn("update_event", methods)
        self.assertNotIn("delete_event", methods)

if __name__ == "__main__":
    unittest.main()
