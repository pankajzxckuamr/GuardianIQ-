# Implementation Plan - Prompt 4.2: Implement Tool Capability & Permission Guard (WBS 4.2)

Implement the enterprise `ToolPermissionGuard` engine validating agent tool invocations against active graph relationships (`USES_TOOL` / `USES`), granular backfilled `tool_capabilities`, agent-level `agent_tool_permissions`, access modes (`READ` cannot execute `WRITE`), parameter constraints/schemas, and approval flags. Replaces the ad hoc blocked-list check in `BoundaryChecker`.

## User Review Required

> [!IMPORTANT]
> **Key Tool Governance & Security Rules**:
> 1. **Prerequisite: Active Relationship Graph Check**:
>    - Validates that the agent has an active `USES_TOOL` or generic `USES` (target_type="TOOL") relationship in `generic_relationships`. If missing or expired $\rightarrow$ `Decision.DENY`.
> 2. **Granular Capability Match from Backfilled Records**:
>    - Resolves `ToolCapability` matching `(tool_id, capability_name == operation)`.
>    - If operation is not registered in `tool_capabilities` $\rightarrow$ `Decision.DENY` (Missing capability).
> 3. **Access Mode & Permission Level Enforcement**:
>    - `READ` access mode cannot execute `WRITE` or `ADMIN` operations.
>    - `AgentToolPermission` controls agent-specific overrides (`is_active == False` $\rightarrow$ `Decision.DENY`).
> 4. **Parameter Schema & Constraint Enforcement**:
>    - Validates parameters against `input_schema_json` (e.g. required fields, parameter ranges, prohibited values).
> 5. **Approval Interception**:
>    - If `ToolCapability.requires_approval == True` or `AgentToolPermission.require_approval == True` $\rightarrow$ `Decision.REQUIRE_APPROVAL`.

## Open Questions

- None.

## Proposed Changes

### Tool Governance Module

#### [NEW] [backend/app/modules/tool_governance/guard.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/tool_governance/guard.py)
- Implement `ToolPermissionGuard`:
  - `evaluate_tool_invocation(tenant_id, agent_id, tool_id, operation, parameters, environment, as_of)`
  - Returns `ToolGuardResult(decision, is_permitted, capability, permission, reason, violations, requires_approval)`

#### [MODIFY] [backend/app/modules/tool_governance/service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/tool_governance/service.py)
- Integrate `ToolPermissionGuard` into `ToolGovernanceService`.

#### [MODIFY] [backend/app/modules/tool_governance/router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/tool_governance/router.py)
- Expose `POST /api/v1/tool-governance/evaluate`.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_tool_permission_guard.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_tool_permission_guard.py):
  1. **Relationship Prerequisite Test**: Verify tool invocation without `USES_TOOL` relationship returns `Decision.DENY`.
  2. **Missing Capability Test**: Verify unregistered tool operation returns `Decision.DENY`.
  3. **Access Mode Test**: Verify `READ` permission attempting to invoke `WRITE` capability returns `Decision.DENY`.
  4. **Approval Flag Test**: Verify capability or permission with `requires_approval=True` returns `Decision.REQUIRE_APPROVAL`.
  5. **Parameter Constraint Test**: Verify parameter constraint violation (e.g. missing required field or exceeding max value) returns `Decision.DENY`.
  6. **Successful Allowed Test**: Verify compliant invocation returns `Decision.ALLOW`.
