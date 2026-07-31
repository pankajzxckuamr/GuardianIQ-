# Implementation Plan - Prompt 6.1: E2E Event Publish Flow (WBS 4.6.1 / QA4-001, QA4-002, QA4-003)

Create an end-to-end integration test suite `backend/app/tests/test_e2e_event_publish_flow.py` testing the complete governance event publishing chain from action trigger to transactional outbox dispatch, outbox processing, and Event Explorer API retrieval, as well as fail-closed validation rejection.

## User Review Required

> [!IMPORTANT]
> **E2E Integration Verification**:
> 1. Real API action trigger (`RELATIONSHIP_REVOKED` / `RELATIONSHIP_CREATED`) → `EventPublisherService` → atomic write to `governance_events` and `event_outbox`.
> 2. `OutboxDispatcher` execution → `event_outbox.status` transitions from `PENDING` to `PROCESSED`.
> 3. `GET /api/v1/events` retrieval powering `AuditPage.tsx` Event Explorer.
> 4. Fail-closed atomicity test: Invalid event missing `tenant_id` or `subject` → verified via direct DB count that zero rows are created.

## Proposed Changes

### Tests

#### [NEW] [test_e2e_event_publish_flow.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_e2e_event_publish_flow.py)
- `test_e2e_event_publish_outbox_dispatcher_and_api_explorer_chain` (QA4-001, QA4-002)
- `test_e2e_event_publish_negative_validation_prevents_db_write` (QA4-003)

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_6_1_e2e_event_publish_flow.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_6_1_e2e_event_publish_flow.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated Tests
1. Run `pytest app/tests/test_e2e_event_publish_flow.py -v`.
2. Run full backend test suite (`pytest app/tests/`).
