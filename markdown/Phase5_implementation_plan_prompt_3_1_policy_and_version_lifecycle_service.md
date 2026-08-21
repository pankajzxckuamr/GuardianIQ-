# Implementation Plan - Prompt 3.1: Implement Policy and Version Lifecycle Service (WBS 3.1)

Implement end-to-end Policy & Version lifecycle services, including draft creation, rule validation, activation transitions, automatic version supersession, suspension/retirement, repository-level immutability protection on ACTIVE versions, and audit event publishing via `EventPublisherService`.

## User Review Required

> [!IMPORTANT]
> **Key Architecture & Security Rules**:
> 1. **Repository-Level Immutability**:
>    - `PolicyVersionRepository.update_draft` strictly rejects any modifications to `ACTIVE`, `SUPERSEDED`, or `RETIRED` versions by raising `ValueError`.
> 2. **Canonical Audit Event Publishing**:
>    - Use `EventPublisherService.publish_event(db, event_create, tenant_id=tenant_id)` with standard `GovernanceEventCreate` payloads.
>    - Emitted event types: `POLICY_CREATED`, `POLICY_VERSION_CREATED`, `POLICY_VERSION_ACTIVATED`, `POLICY_SUSPENDED`, `POLICY_RETIRED`.
> 3. **Version Activation & Supersession**:
>    - Activating Version $N$ automatically sets any currently `ACTIVE` version of that policy to `SUPERSEDED`.
>    - The policy's status transitions to `ACTIVE`.

## Open Questions

- None.

## Proposed Changes

### Policy Engine Service Layer

#### [MODIFY] [backend/app/modules/policy_engine/service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/service.py)
- Implement `PolicyService`:
  - `create_policy(tenant_id, owner_user_id, policy_data)`
  - `update_policy_metadata(tenant_id, policy_id, update_data)`
  - `suspend_policy(tenant_id, policy_id, user_id, reason)`
  - `retire_policy(tenant_id, policy_id, user_id, reason)`
- Implement `PolicyVersionService`:
  - `create_draft_version(tenant_id, policy_id, user_id, changelog, rules_data)`
  - `update_draft_version(tenant_id, version_id, changelog, rules_data)`
  - `activate_version(tenant_id, policy_id, version_id, user_id)`
  - `validate_rules(rules_data)`

#### [MODIFY] [backend/app/modules/policy_engine/router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/router.py)
- Expose REST endpoints for version creation, draft updates, version activation, and policy suspension/retirement.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_policy_lifecycle.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_policy_lifecycle.py):
  1. **Lifecycle Progression Test**: `DRAFT` $\rightarrow$ `ACTIVE` (with automatic supersession of older versions) $\rightarrow$ `SUSPENDED` $\rightarrow$ `RETIRED`.
  2. **Active Version Immutability Test**: Verify attempting to update an active version fails with `ValueError`.
  3. **Audit Event Emission Test**: Query `governance_events` table to verify `POLICY_CREATED`, `POLICY_VERSION_CREATED`, `POLICY_VERSION_ACTIVATED` events are emitted with proper correlation IDs.
