# Phase 5 Implementation Plan — Prompt 7.1: Security and Negative-Path Validation

## 1. Goal Description
Implement and execute a comprehensive security, RBAC, and negative-path validation suite verifying strict cross-tenant isolation (specifically including the altered `policy_bindings` table), agent spoof prevention, inactive/expired permission handling, unauthorized admin mutation blocking, secrets/payload sanitization in events and logs, and service-only authoritative evaluation validation.

---

## 2. Key Objectives & Threat Vectors Addressed
1. **Cross-Tenant Isolation & Table Partitioning**:
   - Verify that all Phase 5 entities (`governance_policies`, `policy_versions`, `policy_rules`, `agent_boundaries`, `approval_requests`) and crucially the altered `policy_bindings` table reject cross-tenant reads, writes, and binding evaluation.
   - Prevent Tenant A from evaluating or inheriting Tenant B's policies or bindings.
2. **Internal System-Actor Bypass Containment**:
   - Verify that any `SYSTEM`-actor bypasses used by internal policy-engine hooks are strictly scoped to internal in-process invocation and cannot be triggered or spoofed by external API requests or untrusted JWT headers.
3. **Agent & Identity Spoofing Prevention**:
   - Verify that runtime requests asserting mismatched actor roles, unassigned agent IDs, or unauthorized caller contexts are blocked at the gateway before model or tool invocation.
4. **Inactive & Expired Permission Handling**:
   - Verify that revoked bindings (`status="REVOKED"`), suspended policies (`status="SUSPENDED"`), or inactive rules (`is_active=False`) are completely ignored during runtime evaluation.
5. **Unauthorized Admin Changes (RBAC)**:
   - Ensure non-admin / non-governance-manager roles receive 403 Forbidden when attempting to create/modify policies, alter bindings, or toggle emergency kill switches.
6. **No Secret & Raw Payload Leakage**:
   - Verify that raw sensitive parameters (passwords, tokens, raw unmasked PII/SSNs) are sanitized/masked before publishing to `governance_events` and audit logs.

---

## 3. Proposed Changes & Affected Files

### Backend Test Suite
#### [NEW] [test_phase5_security_and_negative_validation.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_security_and_negative_validation.py)
Create dedicated test suite covering:
1. `test_security_cross_tenant_policy_and_binding_isolation`: Validates strict tenant boundaries across `governance_policies`, `policy_versions`, `policy_rules`, `agent_boundaries`, and shared `policy_bindings`.
2. `test_security_system_actor_external_spoof_prevention`: Ensures external HTTP endpoints reject unauthorized spoofing of `SYSTEM` actor identities.
3. `test_security_agent_identity_spoofing_blocked`: Verifies that requests asserting fake or unauthorized agent identifiers fail gateway validation.
4. `test_security_inactive_and_revoked_policy_enforcement`: Tests that revoked bindings, suspended policies, and inactive rules fail closed.
5. `test_security_rbac_unauthorized_policy_mutations_blocked`: Verifies 403 Forbidden on policy creation, binding revocation, and kill switch activation without proper permissions.
6. `test_security_payload_sanitization_no_secret_leakage`: Confirms runtime events and evaluation traces do not leak secrets or unmasked PII payloads.

---

## 4. Verification Plan
- Run automated security test suite:
  ```powershell
  pytest app/tests/test_phase5_security_and_negative_validation.py -v
  ```
- Run full Phase 5 regression suite:
  ```powershell
  pytest app/tests/ -k "phase5" -v
  ```
