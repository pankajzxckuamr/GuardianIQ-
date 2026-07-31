# Implementation Plan - Prompt 4.2: Implement Processing Log & Dead-Letter APIs (WBS 4.4.2)

Implement idempotent consumer handling & `event_processing_log` tracking in `consumers.py`, and expose Dead Letter Queue (DLQ) review & audit-trailed retry REST APIs in `router.py`.

## User Review Required

> [!IMPORTANT]
> **Consumer Idempotency**: Prior to executing consumer handlers, `BaseEventConsumer` checks `event_processing_log`. If the `(consumer_id, event_id)` pair has already been processed with `SUCCESS`/`PROCESSED`, the execution is recorded as `SKIPPED` without duplicating timeline entries.
> **Audit Trailed DLQ Retry**: Calling `POST /api/v1/events/dead-letter/{id}/retry` re-queues the outbox row to `PENDING`, marks the DLQ entry `RESOLVED` with `resolved_by = current_user.id`, and **emits an immutable audit governance event** (`DEAD_LETTER_EVENT_RETRIED`).

## Open Questions

- None.

## API & Processing Specification

1. **Consumer Idempotency & Logging** (`consumers.py`):
   - Check existing `event_processing_log` entries for `(consumer_id, event_id)`.
   - Log execution status (`SUCCESS`, `FAILED`, `SKIPPED`), `processed_at`, and `execution_time_ms`.
2. **`GET /api/v1/events/dead-letter`**: `require_permission("VIEW_DEAD_LETTER")` — Paginated DLQ items with `tenant_id` isolation.
3. **`POST /api/v1/events/dead-letter/{id}/retry`**: `require_permission("RETRY_DEAD_LETTER")` — Re-queues outbox record, resolves DLQ item, and emits audit trail event.

## Proposed Changes

### Backend Implementation

#### [MODIFY] [consumers.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/consumers.py)
- Implement `BaseEventConsumer` class with idempotency checking and `event_processing_log` recording.

#### [MODIFY] [router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/router.py)
- Implement `GET /api/v1/events/dead-letter` and `POST /api/v1/events/dead-letter/{id}/retry` REST endpoints.

#### [NEW] [test_dead_letter_apis.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_dead_letter_apis.py)
- Test suite verifying consumer idempotency, DLQ listing API, and audit-trailed retry API.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_4_2_implement_processing_log_and_dead_letter_apis.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_4_2_implement_processing_log_and_dead_letter_apis.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated / Unit Test Verification
1. Run pytest suite: `pytest app/tests/test_dead_letter_apis.py`
2. Confirm idempotency skipping, DLQ listing 200 OK, outbox re-queueing, and audit event emission pass cleanly.
