# Implementation Plan - Prompt 6.3: E2E Dead-Letter / Retry Flow (WBS 4.6.3 / QA4-006)

Create an end-to-end integration test suite `backend/app/tests/test_e2e_dead_letter_retry_flow.py` verifying consumer failure retry attempts, DLQ threshold transition, API list retrieval, UI retry action re-queuing, and mandatory retry audit logging.

## User Review Required

> [!IMPORTANT]
> **Complete DLQ Lifecycle Verification**:
> 1. Consumer failure simulation → `OutboxDispatcher` retries with exponential backoff.
> 2. Max retries exceeded → transition to `DEAD_LETTER` status and row created in `event_dead_letter`.
> 3. API Retrieval: `GET /api/v1/events/dead-letter` returns item for Dead Letter Review UI.
> 4. Manual Retry: `POST /api/v1/events/dead-letter/{id}/retry` re-queues outbox entry (`PENDING`, `retry_count = 0`), resolves DLQ record (`RESOLVED`), and emits `DEAD_LETTER_EVENT_RETRIED` audit event.

## Proposed Changes

### Tests

#### [NEW] [test_e2e_dead_letter_retry_flow.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_e2e_dead_letter_retry_flow.py)
- `test_e2e_dead_letter_failure_dlq_transition_and_audited_retry_flow` (QA4-006)

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_6_3_e2e_dead_letter_retry_flow.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_6_3_e2e_dead_letter_retry_flow.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated Tests
1. Run `pytest app/tests/test_e2e_dead_letter_retry_flow.py -v`.
2. Run full backend test suite (`pytest app/tests/`).
