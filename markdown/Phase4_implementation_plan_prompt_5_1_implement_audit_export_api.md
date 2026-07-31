# Implementation Plan - Prompt 5.1: Implement Audit Export API (WBS 4.5.1)

Implement `AuditExportService` in `backend/app/modules/audit/export_service.py`, expose REST endpoints (`POST /api/v1/audit/export`, `GET /api/v1/audit/export/{id}`) requiring `EXPORT_AUDIT_PACKAGE` permission, log export records to `event_export_log` with SHA-256 manifest hashes via `hashing.py`, and add deferred `POLICY_TRIGGERED`, `APPROVAL_GRANTED`, `APPROVAL_REJECTED` event emission hooks.

## User Review Required

> [!IMPORTANT]
> **Audit Package Manifest & SHA-256 Hashing**:
> Every audit export logs `requested_by`, `scope_json` (`filter_params_json`), `format`, `event_count` (`record_count`), and `export_hash` (`file_hash`) into `event_export_log`.
> **Deferred Event Hooks**:
> - `POLICY_TRIGGERED` emitted in `policy/service.py` when policy triggers.
> - `APPROVAL_GRANTED` / `APPROVAL_REJECTED` emitted in `approval/routes.py` when approval state transitions.

## Proposed Changes

### Backend Implementation

#### [MODIFY] [export_service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/audit/export_service.py)
- Implement `AuditExportService` with `create_export`, `get_export_status`, and `generate_manifest`.
- Use `compute_sha256_hash` from `app.shared.hashing`.
- Save export log entry to `EventExportLog`.

#### [MODIFY] [router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/router.py)
- Add endpoints:
  - `POST /api/v1/audit/export` (`EXPORT_AUDIT_PACKAGE`)
  - `GET /api/v1/audit/export/{id}` (`EXPORT_AUDIT_PACKAGE`)

#### [MODIFY] [service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy/service.py)
- Add `trigger_policy` / `evaluate_policy` logic to publish `POLICY_TRIGGERED` event via `EventPublisherService`.

#### [MODIFY] [routes.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/approval/routes.py)
- Emit `APPROVAL_GRANTED` and `APPROVAL_REJECTED` events via `EventPublisherService` on approval status update.

#### [MODIFY] [phase4_seed.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/seed/phase4_seed.py)
- Seed taxonomy types: `POLICY_TRIGGERED`, `APPROVAL_GRANTED`, `APPROVAL_REJECTED`, `AUDIT_EXPORT_GENERATED`.

#### [NEW] [test_audit_export_api.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_audit_export_api.py)
- Integration unit tests for export generation, manifest hashing, status retrieval, and policy/approval event hooks.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_5_1_implement_audit_export_api.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_5_1_implement_audit_export_api.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated / Unit Test Verification
1. Run `pytest app/tests/test_audit_export_api.py`.
2. Verify export package JSON contains envelope list, cryptographic manifest, and `event_export_log` record with valid SHA-256 hash.
3. Verify `POLICY_TRIGGERED`, `APPROVAL_GRANTED`, `APPROVAL_REJECTED` events emit cleanly.
