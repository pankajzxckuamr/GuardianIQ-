# Implementation Plan - Prompt 4.1: Implement Agent Boundary Resolver (WBS 4.1)

Implement the enterprise `AgentBoundaryResolver` engine resolving active agent runtime boundaries and enforcing status checks, autonomy levels, kill switch activation, allowed access modes, sub-agent spawning permissions, rate/concurrency limits, and transaction approval thresholds. Designed for direct internal integration with `AgentRuntimeService.invoke_agent` and `BoundaryChecker` in Task 5.2.

## User Review Required

> [!IMPORTANT]
> **Key Boundary Enforcement Rules**:
> 1. **Kill Switch & Status Enforcement**:
>    - If `Agent.status != "ACTIVE"` or `AgentRuntimeBoundary.is_active == False` $\rightarrow$ Immediate `Decision.DENY` (Action completely blocked).
> 2. **Autonomy Level Boundary Rules**:
>    - Hierarchical rank: `READ_ONLY` (1) < `RECOMMEND_ONLY` (2) < `HUMAN_SUPERVISED` (3) < `SEMI_AUTONOMOUS` (4) < `AUTONOMOUS` (5).
>    - If requested operation is autonomous execution but `max_autonomy_level` is `RECOMMEND_ONLY` or `HUMAN_SUPERVISED` $\rightarrow$ intercepted with `Decision.REQUIRE_APPROVAL` or `Decision.DENY`.
> 3. **Access Mode Verification**:
>    - Requested access mode (e.g. `WRITE`, `EXECUTE`, `ADMIN`) must exist in `allowed_access_modes_json`.
> 4. **Threshold Interception**:
>    - If transaction amount exceeds `require_approval_threshold` $\rightarrow$ `Decision.REQUIRE_APPROVAL`.
> 5. **Sub-Agent Spawning Permission**:
>    - If agent attempts to spawn sub-agents without `allow_sub_agent_spawn == True` $\rightarrow$ `Decision.DENY`.
> 6. **Seamless Runtime Integration**:
>    - Exposes a unified `resolve_and_enforce(tenant_id, agent_id, request_context, as_of)` method ready for 5.2 invocation inside `AgentRuntimeService.invoke_agent`.

## Open Questions

- None.

## Proposed Changes

### Agent Boundary Module

#### [NEW] [backend/app/modules/agent_boundary/resolver.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_boundary/resolver.py)
- Implement `AgentBoundaryResolver`:
  - `resolve_boundary(tenant_id, agent_id, as_of)`
  - `enforce_boundary(boundary, agent, request_context)`
  - `resolve_and_enforce(tenant_id, agent_id, request_context, as_of)`
  - Returns `BoundaryResolutionResult(decision, boundary, is_permitted, reason, violations, requires_approval)`

#### [MODIFY] [backend/app/modules/agent_boundary/service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_boundary/service.py)
- Integrate `AgentBoundaryResolver` into `AgentBoundaryService`.

#### [MODIFY] [backend/app/modules/agent_boundary/router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_boundary/router.py)
- Expose boundary check endpoint `POST /api/v1/agent-boundaries/{agent_id}/evaluate`.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_agent_boundary_resolver.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_agent_boundary_resolver.py):
  1. **Kill Switch Test**: Verify inactive boundary (`is_active=False`) or inactive agent returns `Decision.DENY`.
  2. **Autonomy Level Test**: Verify requested `AUTONOMOUS` execution is intercepted as `REQUIRE_APPROVAL` when boundary is `RECOMMEND_ONLY` or `HUMAN_SUPERVISED`.
  3. **Access Mode Test**: Verify unauthorized access mode (e.g. `WRITE` when only `READ_ONLY` allowed) returns `Decision.DENY`.
  4. **Sub-Agent Spawn Test**: Verify sub-agent spawn is denied when `allow_sub_agent_spawn=False`.
  5. **Transaction Threshold Test**: Verify exceeding `require_approval_threshold` returns `Decision.REQUIRE_APPROVAL`.
