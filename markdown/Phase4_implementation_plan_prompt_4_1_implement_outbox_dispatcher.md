# Implementation Plan - Prompt 4.1: Implement Outbox Dispatcher (WBS 4.4.1)

Implement background `OutboxDispatcher` worker process in `backend/app/modules/events/dispatcher.py` using `FOR UPDATE SKIP LOCKED` polling over `event_outbox`, exponential retry backoff, Dead Letter Queue (DLQ) transition, and standalone health API server.

## User Review Required

> [!IMPORTANT]
> **No Celery Dependency**: Modeled directly after [scheduler_worker.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/workers/scheduler_worker.py#L84), utilizing native DB polling with `SELECT ... FOR UPDATE SKIP LOCKED` to support multi-replica concurrency without Celery constraints.
> **Dead Letter Queue (DLQ) Threshold**: When `retry_count >= max_retries` (default 5), the outbox row transitions to `DEAD_LETTER` and creates an `event_dead_letter` record automatically.
> **Standalone Health Server Port**: Serves `/health/outbox` on port `8082` (`OUTBOX_DISPATCHER_HEALTH_PORT`), avoiding port conflicts with the scheduler worker (`8081`).

## Open Questions

- None.

## Dispatcher Architecture & State Transitions

```
[ PENDING ]  ---> Dispatch Success  ---> [ DISPATCHED ]
     |
  Dispatch Failure
     v
[ FAILED ] (retry_count < max_retries, exponential backoff next_retry_at)
     |
  retry_count >= max_retries
     v
[ DEAD_LETTER ] ---> Insert row into `event_dead_letter`
```

## Proposed Changes

### Backend Implementation

#### [MODIFY] [dispatcher.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/dispatcher.py)
- Implement `OutboxDispatcher` class, polling loop with `SKIP LOCKED`, retry backoff math, DLQ transition, and uvicorn health server on port `8082`.

#### [NEW] [test_outbox_dispatcher.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_outbox_dispatcher.py)
- Unit test suite verifying polling, successful dispatch, exponential retry backoff, and DLQ transition.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_4_1_implement_outbox_dispatcher.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_4_1_implement_outbox_dispatcher.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated / Unit Test Verification
1. Run pytest suite: `pytest app/tests/test_outbox_dispatcher.py`
2. Confirm outbox row status transitions and dead letter creation pass cleanly.
