# Implementation Plan - Prompt 2.3: Create Backend Module Skeletons (WBS 2.3)

Scaffold modular backend architecture across `policy_engine`, `agent_boundary`, `tool_governance`, `data_governance`, and internal `enforcement` engine. Wire dependency injection and register public routes in `main.py`.

## User Review Required

> [!IMPORTANT]
> **Key Architecture & Router Wiring Guard Rules**:
> 1. **Public Routers (4 Modules)**:
>    - `policy_engine.router`: `/api/v1/policies`, `/api/v1/policy-versions`, `/api/v1/policy-rules`, `/api/v1/policy-exceptions`, `/api/v1/policy-bindings`.
>    - `agent_boundary.router`: `/api/v1/agent-boundaries`.
>    - `tool_governance.router`: `/api/v1/tool-governance`.
>    - `data_governance.router`: `/api/v1/data-governance`.
> 2. **Internal-Only `enforcement` Engine (Zero Public Router)**:
>    - Per the specification corrections, `enforcement` is scaffolded as an **internal service** (`context_builder.py`, `decision_combiner.py`, `authorization_service.py`, `engine.py`).
>    - It is **not** exposed as a public API router (it will be intercepted from within `AgentRuntimeService.invoke_agent` in Task 5.2).
> 3. **Shared Enums & Schemas**:
>    - All modules import enums directly from `app.modules.policy_engine.enums`.
> 4. **Application Compilation & Startup**:
>    - Verify `FastAPI` boots, OpenAPI schema generates, and all 4 routers register without circular dependencies.

## Open Questions

- None.

## Proposed Changes

### Module Skeletons

#### 1. Policy Engine Module (`backend/app/modules/policy_engine/`)
- [NEW] `repository.py`: `PolicyRepository`, `PolicyVersionRepository`, `PolicyRuleRepository`, `PolicyBindingRepository`, `PolicyExceptionRepository`.
- [NEW] `service.py`: `PolicyService`, `PolicyVersionService`, `PolicyBindingService`.
- [NEW] `router.py`: REST routes for policies, versions, rules, bindings, exceptions.

#### 2. Agent Boundary Module (`backend/app/modules/agent_boundary/`)
- [NEW] `schemas.py`: Schemas for `AgentRuntimeBoundaryCreate`, `AgentRuntimeBoundaryResponse`, etc.
- [NEW] `repository.py`: `AgentBoundaryRepository`.
- [NEW] `service.py`: `AgentBoundaryService`.
- [NEW] `router.py`: REST routes for `/api/v1/agent-boundaries`.

#### 3. Tool Governance Module (`backend/app/modules/tool_governance/`)
- [NEW] `schemas.py`: Schemas for `ToolCapabilityCreate`, `AgentToolPermissionCreate`, etc.
- [NEW] `repository.py`: `ToolGovernanceRepository`.
- [NEW] `service.py`: `ToolGovernanceService`.
- [NEW] `router.py`: REST routes for `/api/v1/tool-governance`.

#### 4. Data Governance Module (`backend/app/modules/data_governance/`)
- [NEW] `schemas.py`: Schemas for `DataSourceFieldCreate`, `AgentDataPermissionCreate`, etc.
- [NEW] `repository.py`: `DataGovernanceRepository`.
- [NEW] `service.py`: `DataGovernanceService`.
- [NEW] `router.py`: REST routes for `/api/v1/data-governance`.

#### 5. Enforcement Engine (Internal Service) (`backend/app/modules/enforcement/`)
- [NEW] `__init__.py`: Exports internal services.
- [NEW] `context_builder.py`: `GovernedRuntimeContextBuilder`.
- [NEW] `decision_combiner.py`: `EnforcementDecisionCombiner`.
- [NEW] `authorization_service.py`: `RuntimeAuthorizationService`.
- [NEW] `engine.py`: `RuntimeEnforcementEngine`.

#### 6. Application Startup & Router Registration
- [MODIFY] `backend/app/main.py`: Include routers for `policy_engine`, `agent_boundary`, `tool_governance`, and `data_governance`.

## Verification Plan

### Automated Tests
- Test FastAPI app initialization and OpenAPI schema generation.
- Add test in `backend/app/tests/test_phase5_module_skeletons.py` verifying:
  - All 4 routers respond to GET/OPTIONS requests.
  - Enforcement internal engine can be instantiated.
  - Zero circular import errors.
