# Implementation Plan - Prompt 5.3: Implement Exact-Request Authorization / TOCTOU Protection (WBS 5.3)

Implement cryptographically verifiable runtime authorizations and Time-of-Check to Time-of-Use (TOCTOU) protection inside `RuntimeAuthorizationService` ([backend/app/modules/enforcement/authorization_service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/authorization_service.py)).

## User Review Required

> [!IMPORTANT]
> **Key TOCTOU & Authorization Mechanisms**:
> 1. **Canonical Hashing**:
>    - Uses existing `backend/app/shared/hashing.py` utilities (`compute_sha256_hash`, `compute_canonical_event_hash`) to calculate:
>      - `context_hash`: Canonical representation of runtime request parameters (`tenant_id`, `agent_id`, `model_id`, `tool_id`, `operation`, `facts`, `data_requests`).
>      - `relationship_hash`: Canonical hash of active agent graph relationships (`USES_TOOL`, `USES_MODEL`, `USES_DATA_SOURCE`).
>      - `policy_hash`: Canonical hash of resolved policy version IDs and rule checksums.
> 2. **Short-Lived Authorization Tokens**:
>    - Issues `RuntimeAuthorization` records with strict TTL (default 300s), status lifecycle (`ISSUED` $\rightarrow$ `CONSUMED` / `EXPIRED` / `REVOKED`), and linked approval/request IDs.
> 3. **Just-In-Time Verification & Single-Use Consumption**:
>    - Immediately before execution, verifies:
>      - Token expiration (`AUTHORIZATION_EXPIRED`).
>      - Single-use consumption status (`AUTHORIZATION_REPLAY_DETECTED`).
>      - Request immutability: Recomputed `context_hash` must match issued token hash (`CONTEXT_HASH_TAMPERED`).
>      - Graph relationship integrity: Recomputed `relationship_hash` must match issued token (`RELATIONSHIP_GRAPH_ALTERED`).
>    - Atomically transitions token status to `CONSUMED` upon successful verification.

## Open Questions

- None.

## Proposed Changes

### Enforcement Module

#### [MODIFY] [backend/app/modules/enforcement/authorization_service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/authorization_service.py)
- Implement `compute_context_hash`, `compute_relationship_hash`, `compute_policy_hash` using `app.shared.hashing`.
- Implement `issue_authorization` to mint short-lived `RuntimeAuthorization` envelopes with embedded cryptographic hashes.
- Implement `verify_and_consume_authorization` to perform pre-execution TOCTOU checks (tamper detection, replay prevention, expiration enforcement).

#### [MODIFY] [backend/app/modules/enforcement/engine.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/engine.py)
- Integrate authorization token issuance into `RuntimeEnforcementEngine.enforce(...)` for permitted executions (`ALLOW` / `ALLOW_WITH_OBLIGATIONS`).

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_runtime_authorization_toctou.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_runtime_authorization_toctou.py):
  1. **Tampered Request Rejection**: Issue authorization for a request, modify a parameter (e.g. change `tool_parameters` or `facts.operation`), verify `verify_and_consume_authorization` fails with tamper rejection.
  2. **Replay Attack Prevention**: Issue authorization, consume it once successfully, attempt second consumption, verify replay rejection.
  3. **Expired Authorization Rejection**: Issue authorization with expired TTL or past timestamp, verify expiration rejection.
  4. **Full End-to-End TOCTOU Verification**: Issue valid authorization, verify and consume successfully, confirming atomic status transition to `CONSUMED`.
