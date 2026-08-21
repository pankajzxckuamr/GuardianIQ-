# Implementation Plan - Prompt 6.3 / 6.4: QA Automated Test Suite & E2E Integration Scenarios (WBS 6.3 / 6.4)

Implement the end-to-end integration test suite ([backend/app/tests/test_phase5_e2e_pilot_scenarios.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_e2e_pilot_scenarios.py)) validating all Phase 5 acceptance criteria, including backfilled tool capabilities (`_backfilled: true`), TOCTOU replay prevention, fail-closed safety, and multi-tenant isolation.

## User Review Required

> [!IMPORTANT]
> **Key Test Specifications & Pilot Flow Matrix**:
> 1. **Pilot Flow 1 (Permitted Action)**: Fully authorized agent action passes Layer 1–4, returns `ALLOW`, and issues short-lived execution token.
> 2. **Pilot Flow 2 (Missing WRITE Permission / Backfilled Tool Check)**: Tests against `tool_capabilities` records including heuristically-inferred entries with `_backfilled: true`. Ensures READ capability denies WRITE operation.
> 3. **Pilot Flow 3 (High-Value Approval Flow)**: Action exceeding approval threshold returns `REQUIRE_APPROVAL`, persists `PolicyApproval` record, and validates execution after approval.
> 4. **Pilot Flow 4 (Restricted Data to Prohibited Model)**: Data classification ceiling and model deployment environment mismatch blocked before LLM invocation.
> 5. **Pilot Flow 5 (Data Masking Obligations)**: Field-level PII transformation applied (MASK/REDACT/TOKENIZE) before exposure to tool/agent.
> 6. **Pilot Flow 6 (Permission Revoked / TOCTOU)**: Request altered or authorization revoked post-approval is rejected by token hash verification.
> 7. **Pilot Flow 7 (Emergency Kill Switch)**: Active agent blocked across runtime gateway when kill switch is engaged.
> 8. **Pilot Flow 8 (Policy Engine Fail-Closed)**: Error or timeout during rule evaluation fails closed to `DENY`.
> 9. **Pilot Flow 9 (Tenant Partition & Isolation)**: Cross-tenant boundary, policy, and tool evaluation strictly blocked.

## Open Questions

- None.

## Proposed Changes

### Automated E2E Test Suite

#### [NEW] [backend/app/tests/test_phase5_e2e_pilot_scenarios.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_e2e_pilot_scenarios.py)
- Implements 9 comprehensive E2E integration test cases matching Q-001–Q-022 in the QA acceptance catalog:
  - `test_e2e_flow_1_permitted_action`
  - `test_e2e_flow_2_missing_write_permission_with_backfilled_capabilities`
  - `test_e2e_flow_3_high_value_approval_lifecycle`
  - `test_e2e_flow_4_restricted_data_prohibited_model_blocked`
  - `test_e2e_flow_5_data_masking_transformation_obligations`
  - `test_e2e_flow_6_toctou_permission_revoked_after_approval`
  - `test_e2e_flow_7_kill_switch_immediate_block`
  - `test_e2e_flow_8_policy_engine_fail_closed_on_error`
  - `test_e2e_flow_9_strict_tenant_isolation`

## Verification Plan

### Automated Tests
- Run `.\venv\Scripts\python.exe -m pytest app/tests/test_phase5_e2e_pilot_scenarios.py -v`
- Run complete Phase 5 test suite: `.\venv\Scripts\python.exe -m pytest app/tests/ -k "phase5" -v`
- Run complete project test suite to ensure zero regressions across Phase 1–5.
