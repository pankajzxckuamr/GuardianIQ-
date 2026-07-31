# Implementation Plan - Prompt 7.2: Verify Event Immutability and Access Control (WBS 4.7.2 / QA4-005, QA4-009)

Create an integration test suite `backend/app/tests/test_event_immutability_and_access_control.py` verifying append-only immutability enforcement, 405 HTTP method rejection for UPDATE/DELETE, tenant isolation without existence leakage, RBAC permission enforcement, and ABAC clearance/department scoping.

## User Review Required

> [!IMPORTANT]
> **Immutability & Access Control Scope**:
> - **Immutability Check**: Verify `EventRepository` exposes 0 mutation/deletion methods; HTTP PUT/PATCH/DELETE requests against event routes return `405 Method Not Allowed`.
> - **Tenant Isolation**: Cross-tenant query returns `404 Not Found` (zero data/existence leakage).
> - **RBAC Authorization**: Requests without required permissions (`VIEW_EVENTS`, `VIEW_AUDIT_TIMELINE`, `EXPORT_AUDIT_PACKAGE`) return `403 Forbidden` without payload leakage.
> - **ABAC & Security Scoping**: Verify clearance level comparison, department scoping via `abac_service.py`, and payload redactor masking (`***MASKED***`).

## Proposed Changes

### Tests

#### [NEW] [test_event_immutability_and_access_control.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_event_immutability_and_access_control.py)
- `test_governance_event_immutability_enforcement`
- `test_tenant_isolation_zero_existence_leakage`
- `test_rbac_permission_denial_no_payload_leak`
- `test_abac_department_clearance_and_payload_redaction`

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_7_2_verify_event_immutability_and_access_control.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_7_2_verify_event_immutability_and_access_control.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated Tests
1. Run `pytest app/tests/test_event_immutability_and_access_control.py -v`.
2. Run full backend test suite (`pytest app/tests/`).
