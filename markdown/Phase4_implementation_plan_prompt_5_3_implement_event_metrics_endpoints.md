# Implementation Plan - Prompt 5.3: Implement Event Metrics Endpoints (WBS 4.5.3)

Implement dashboard metrics service and REST endpoint `GET /api/v1/events/metrics` providing aggregated governance event statistics (counts by type/category, policy violations, SLA breaches, blocked agent actions, outbox lag seconds, and dead-letter count) with strict manual tenant isolation.

## User Review Required

> [!IMPORTANT]
> **Strict Tenant Isolation**: Every aggregation query explicitly passes `tenant_id` filter (e.g., `GovernanceEvent.tenant_id == tenant_id`, `EventOutbox.tenant_id == tenant_id`, `EventDeadLetter.tenant_id == tenant_id`).
> **Metrics Aggregations**:
> - `total_events_count`
> - `events_by_type` (grouped dict)
> - `events_by_category` (grouped dict)
> - `policy_violations_count` (`event_category == 'Violation'` or `POLICY_VIOLATION_DETECTED`)
> - `sla_breaches_count` (`SLA_BREACHED` / `SLA_VIOLATED`)
> - `blocked_agent_actions_count` (`UNAUTHORIZED_ACCESS_BLOCKED` / `AGENT_ACTION_BLOCKED`)
> - `outbox_lag_seconds` (max pending lag in outbox)
> - `dead_letter_count` (unresolved DLQ items count)

## Proposed Changes

### Backend Implementation

#### [MODIFY] [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/service.py)
- Add `EventMetricsService` class with `get_dashboard_metrics(db, tenant_id)`.

#### [MODIFY] [router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/router.py)
- Expose `GET /api/v1/events/metrics` endpoint requiring `VIEW_EVENTS` permission code.
- Ensure route is declared before `GET /{event_id}` to prevent route matching collisions.

#### [NEW] [test_event_metrics.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_event_metrics.py)
- Integration unit tests verifying metrics calculations and tenant isolation.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_5_3_implement_event_metrics_endpoints.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_5_3_implement_event_metrics_endpoints.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated Tests
1. Run `pytest app/tests/test_event_metrics.py`.
2. Verify all metric fields are returned with correct tenant-isolated aggregation counts.
3. Run full backend test suite (`pytest app/tests/`).
