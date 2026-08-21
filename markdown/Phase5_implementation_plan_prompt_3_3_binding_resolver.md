# Implementation Plan - Prompt 3.3: Implement Binding Resolver (WBS 3.3)

Implement the enterprise `BindingResolver` engine that evaluates hierarchical policy bindings across Direct, Workflow, Department/BU, and Tenant/Global scopes. Resolve exact version snapshots (`LATEST` vs `PINNED`), apply specificity overrides, compute deterministic resolution SHA-256 hashes, and provide an explainable resolution trace.

## User Review Required

> [!IMPORTANT]
> **Key Hierarchy & Relationship Resolution Rules**:
> 1. **Scope Specificity Precedence Hierarchy**:
>    - `DIRECT` (Agent, Tool, Data Source, Model) > `WORKFLOW` (`PARTICIPATES_IN_WORKFLOW`, `GOVERNED_BY`) > `DEPARTMENT` > `TENANT` / `GLOBAL`.
>    - If the same policy is bound at multiple scopes, the more specific binding overrides the generic one.
> 2. **Relationship Literal Normalization**:
>    - Support specific literals (`USES_MODEL`, `USES_TOOL`, `USES_DATA_SOURCE`, `PARTICIPATES_IN_WORKFLOW`, `GOVERNED_BY`) **and** the generic `"USES"` literal (disambiguated by `target_type`).
>    - Strict rule: Do NOT look for `REQUIRES_APPROVAL` graph relationships (approval routing is computed by Decision Combiner).
> 3. **Version Selection**:
>    - `LATEST`: Resolves dynamically to the `ACTIVE` version snapshot as of `as_of`.
>    - `PINNED`: Resolves to the specified `pinned_policy_version_id`.
> 4. **Deterministic Resolution Hash & Explainability Trace**:
>    - Computes SHA-256 `resolution_hash` over the sorted sequence of `(policy_id, version_id, rule_ids)`.
>    - Generates a human-readable and auditable `resolution_trace` explaining every binding's resolution path.

## Open Questions

- None.

## Proposed Changes

### Policy Engine Resolver Module

#### [NEW] [backend/app/modules/policy_engine/resolver.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/resolver.py)
- Implement `BindingResolver`:
  - `resolve_runtime_policies(tenant_id, agent_id, tool_ids, data_source_ids, model_id, workflow_id, as_of)`
  - `_resolve_direct_bindings(tenant_id, target_type, target_id, as_of)`
  - `_resolve_graph_relationships(tenant_id, agent_id, as_of)`
  - `_resolve_global_and_tenant_bindings(tenant_id, as_of)`
  - `_select_policy_versions(tenant_id, bindings, as_of)`
  - `_compute_resolution_hash(resolved_policies)`

#### [MODIFY] [backend/app/modules/policy_engine/service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/service.py)
- Integrate `BindingResolver` for runtime evaluation preparation.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_binding_resolver.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_binding_resolver.py):
  1. **Hierarchical Scope Precedence Test**: Prove Direct Agent binding overrides Workflow-inherited binding for the same policy.
  2. **Relationship Literal Normalization Test**: Verify both `USES_TOOL` and `USES` (target_type="TOOL") resolve correctly.
  3. **Version Selection Test**: Verify `LATEST` picks active version while `PINNED` picks the pinned version.
  4. **Resolution Hash & Trace Test**: Prove SHA-256 resolution hash is deterministic and trace accurately lists resolution reasons.
