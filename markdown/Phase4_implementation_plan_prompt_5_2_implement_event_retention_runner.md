# Implementation Plan - Prompt 5.2: Implement Retention and Classification Controls (WBS 4.5.2)

Implement `EventSecurityService` in `backend/app/modules/events/security.py` and `PayloadRedactorService` in `backend/app/shared/redaction.py`. Enforce classification clearance checks reusing `DataClassification` from `registry/constants.py` and ABAC clearance evaluation from `abac_service.py`. Enforce payload redaction for secret keys and clearance-restricted fields.

## User Review Required

> [!IMPORTANT]
> **DataClassification Enum Reuse**: Reuses existing `DataClassification` enum (`PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`) from `registry/constants.py`.
> **ABAC Scoping Reuse**: Calls into `abac_service.py` clearance-rank methods rather than reimplementing clearance comparisons.
> **Consolidated Redactor**: `PayloadRedactorService` extends secret-key list from `registry/audit_service.py`'s `sanitize()`.

## Proposed Changes

### Shared Utilities

#### [NEW] [redaction.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/shared/redaction.py)
- Implement `PayloadRedactorService` with `redact_secrets(payload)` and `redact_by_clearance(payload, user_clearance_rank, event_classification_rank)`.

### Event Security Module

#### [NEW] [security.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/security.py)
- Implement `EventSecurityService` with:
  - `can_view_event(user, event, db) -> bool`
  - `mask_payload(user, event, db) -> dict`
  - `filter_events_by_scope(user, events, db) -> list`

### Tests

#### [NEW] [test_event_security.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_event_security.py)
- Unit tests verifying classification clearance checks, secret redaction, and ABAC-based event filtering.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_5_2_implement_event_retention_runner.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_5_2_implement_event_retention_runner.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated Tests
1. Run `pytest app/tests/test_event_security.py`.
2. Verify secret keys (`password`, `token`, `secret`, `api_key`, `ssn`) are masked to `[REDACTED]`.
3. Verify `CONFIDENTIAL` / `RESTRICTED` events are hidden or masked for `INTERNAL` clearance users.
4. Run full backend test suite (`pytest app/tests/`).
