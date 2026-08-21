# Implementation Plan - Prompt 5.4: Integrate Approval / Exception Hooks (WBS 5.4)

Implement the stable `ApprovalExceptionAdapter` ([backend/app/modules/enforcement/approval_adapter.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/approval_adapter.py)) integrating policy evaluation approval workflows, immutable context hash validation, active policy exceptions, and escalation owner routing.

## User Review Required

> [!IMPORTANT]
> **Key Architecture Decisions & Corrections**:
> 1. **Phase-5 Approval Isolation**:
>    - Avoids legacy `approvals` table (`recommendation_id` NOT NULL FK).
>    - Utilizes dedicated `PolicyApproval` model (`policy_approvals` table) keyed to `request_id`, `policy_id`, `tenant_id`, `required_role`, and `approval_tier`.
> 2. **Post-Approval TOCTOU Immutability Validation**:
>    - Embeds canonical `context_hash` inside `PolicyApproval.metadata_json`.
>    - Validates that the runtime request context executed after approval matches the exact payload approved by the human reviewer (`CONTEXT_TAMPERED_POST_APPROVAL`).
> 3. **Active Policy Exception Bypass**:
>    - Supports looking up effective time-bounded exceptions in `PolicyException` (`policy_exceptions` table) to grant legitimate overrides for specific agents/tools/workflows.
> 4. **Escalation Owner Resolution**:
>    - Reuses `ScheduleNotificationService` / schedule owner lookup pattern for `ESCALATE` decisions without introducing redundant escalation modules.

## Open Questions

- None.

## Proposed Changes

### Enforcement Module

#### [NEW] [backend/app/modules/enforcement/approval_adapter.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/approval_adapter.py)
- Implement `ApprovalExceptionAdapter`:
  - `request_approval(...)`: Creates `PolicyApproval` with `PENDING` status, timeout, and context hash.
  - `record_approval_decision(...)`: Transitions approval to `APPROVED` or `REJECTED`.
  - `check_approval_status(...)`: Validates approval status and verifies post-approval request payload immutability.
  - `lookup_active_exception(...)`: Checks time-bounded, active `PolicyException` overrides.
  - `resolve_escalation_owner(...)`: Resolves notification recipient for `ESCALATE` decisions.

#### [MODIFY] [backend/app/modules/enforcement/__init__.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/__init__.py)
- Export `ApprovalExceptionAdapter`.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_approval_exception_adapter.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_approval_exception_adapter.py):
  1. **Pending Approval Gate**: Verify `check_approval_status` blocks execution when approval is `PENDING` or missing.
  2. **Approved Execution Pass**: Verify `check_approval_status` permits execution once approved by reviewer with matching context hash.
  3. **Tampered Request Post-Approval**: Verify modifying request parameters after approval is granted is rejected (`CONTEXT_TAMPERED_POST_APPROVAL`).
  4. **Active Policy Exception Override**: Verify `lookup_active_exception` finds valid active exception within effective dates and ignores expired ones.
