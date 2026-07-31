# Implementation Plan - Prompt 4.4: Integrate Event Publisher with Existing Modules (WBS 4.4.4)

Add **additive** integration calls to `EventPublisherService.publish_event(...)` across existing module call sites (`relationship`, `workflow_execution`, `agent_runtime`) without modifying or removing existing `audit_events` legacy writes.

## User Review Required

> [!IMPORTANT]
> **Additive Hooks Only**: Legacy `audit_events` logging remains untouched. Added calls to `EventPublisherService.publish_event(...)` run alongside existing logging.
> **No Table Schema Changes**: For `WORKFLOW_RUN_COMPLETED`, `agent_id` and `ai_model_id` are resolved dynamically at runtime via `WorkflowScheduleAgentAssignment` (keyed on `schedule_id`).
> **Deferred Policy & Approval Hooks**: Policy (`policy/service.py`) and Approval (`approval/routes.py`) event emission hooks are explicitly deferred to Day 5 (Prompt 5.1).

## Target Integration Call Sites & Event Taxonomy

1. **Relationship Audit Service** (`relationship/audit_service.py`):
   - `publish_relationship_created`: Emits `RELATIONSHIP_CREATED` (`Category: Relationship`).
   - `publish_relationship_revoked`: Emits `RELATIONSHIP_REVOKED` or `RELATIONSHIP_DELETED` (`Category: Relationship`).
2. **Workflow Execution Service** (`workflow_execution/service.py`):
   - `start_run`: Emits `WORKFLOW_RUN_STARTED` (`Category: Workflow`).
   - `complete_run`: Emits `WORKFLOW_RUN_COMPLETED` (`Category: Workflow`, resolving `agent_id` via `schedule.agent_assignments`).
3. **Agent Runtime Boundary Checker** (`agent_runtime/boundary_checker.py`):
   - `_publish_failure`: Emits `UNAUTHORIZED_ACCESS_BLOCKED` or `BOUNDARY_BREACH_ATTEMPTED` (`Category: Violation`).

## Proposed Changes

### Backend Implementation

#### [MODIFY] [audit_service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/relationship/audit_service.py)
- Add `EventPublisherService` additive calls to `publish_relationship_created` and `publish_relationship_revoked`.

#### [MODIFY] [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/workflow_execution/service.py)
- Add `EventPublisherService` additive calls to `start_run` and `complete_run`.

#### [MODIFY] [boundary_checker.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_runtime/boundary_checker.py)
- Add `EventPublisherService` additive call to `_publish_failure`.

#### [NEW] [test_event_publisher_integration.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_event_publisher_integration.py)
- Test suite verifying that 5 distinct operational flows publish real `governance_events` and `event_outbox` rows.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_4_4_integrate_event_publisher_with_existing_modules.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_4_4_integrate_event_publisher_with_existing_modules.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated / Unit Test Verification
1. Run pytest suite: `pytest app/tests/test_event_publisher_integration.py`
2. Confirm 5 distinct operational flows publish valid `governance_events` rows cleanly.
