# Implementation Plan - Prompt 3.2: Implement Policy Binding Service (WBS 3.2)

Implement the enterprise `PolicyBindingService` operating on the altered `policy_bindings` table, providing target existence and same-tenant validation, date overlap prevention, version strategy resolution (`LATEST` vs `PINNED`), lifecycle management (`create`, `activate`, `suspend`, `revoke`), event publishing, and cache invalidation via `MemoryCacheService`.

## User Review Required

> [!IMPORTANT]
> **Key Architecture & Security Rules**:
> 1. **Target Entity & Same-Tenant Validation**:
>    - Validate target existence across `agents`, `tools`, `data_sources`, `workflows`, and `ai_models`.
>    - Block cross-tenant target bindings (`ValueError`).
> 2. **Version Strategy Resolution**:
>    - `LATEST`: Resolves to the currently active version of the bound policy dynamically at runtime.
>    - `PINNED`: Requires a valid `pinned_policy_version_id` belonging to the policy.
> 3. **Duplicate Overlap Guard**:
>    - Prevents overlapping active bindings for the same `(policy_id, target_type, target_id)` within intersecting effective date ranges.
> 4. **In-Process Cache Invalidation**:
>    - Integrates `MemoryCacheService().invalidate_tenant(str(tenant_id))` upon any binding creation, status change, or revocation.
> 5. **Audit Event Publishing**:
>    - Emits `POLICY_BINDING_CREATED`, `POLICY_BINDING_UPDATED`, and `POLICY_BINDING_DEACTIVATED` events through `EventPublisherService.publish_event`.

## Open Questions

- None.

## Proposed Changes

### Policy Engine Service & Binding Management

#### [NEW] [backend/app/modules/policy_engine/binding_service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/binding_service.py)
- Implement `PolicyBindingService`:
  - `validate_target_exists(tenant_id, target_type, target_id)`
  - `create_binding(tenant_id, user_id, binding_data, correlation_id=None)`
  - `activate_binding(tenant_id, binding_id, user_id, correlation_id=None)`
  - `suspend_binding(tenant_id, binding_id, user_id, correlation_id=None)`
  - `revoke_binding(tenant_id, binding_id, user_id, correlation_id=None)`
  - `resolve_effective_bindings(tenant_id, target_type, target_id, as_of=None)` (cached with `MemoryCacheService`)

#### [MODIFY] [backend/app/modules/policy_engine/router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/router.py)
- Wire `PolicyBindingService` into `binding_router` for creation, listing, status transitions, and revocation.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_policy_bindings.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_policy_bindings.py):
  1. **Multi-Target Binding Test**: Create bindings for `AGENT`, `TOOL`, `DATA_SOURCE`, `WORKFLOW`, `MODEL`.
  2. **Cross-Tenant Blocking Test**: Attempt to bind Tenant A's policy to Tenant B's agent -> verify rejection with `ValueError`.
  3. **Duplicate Overlap Test**: Attempt to create conflicting active bindings for the same date window -> verify rejection.
  4. **Cache Invalidation & Event Emission Test**: Verify `MemoryCacheService` cache is invalidated on mutation, and `POLICY_BINDING_CREATED`/`DEACTIVATED` audit events are emitted.
