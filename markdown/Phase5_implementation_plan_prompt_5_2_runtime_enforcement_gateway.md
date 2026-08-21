# Implementation Plan - Prompt 5.2: Implement Runtime Enforcement Gateway (WBS 5.2)

Rewire the server-side mandatory pre-execution checkpoint inside `AgentRuntimeService.invoke_agent` (`backend/app/modules/agent_runtime/service.py`) and `BoundaryChecker` to route runtime execution through the complete Context Builder $\rightarrow$ Hard Boundary Guards (Agent, Tool, Data, Model) $\rightarrow$ Binding Resolver $\rightarrow$ Rule Evaluator $\rightarrow$ Decision Combiner pipeline.

## User Review Required

> [!IMPORTANT]
> **Key Runtime Enforcement Routing Rules**:
> 1. **Live Production Call Site Integration**:
>    - Preserves `AgentRuntimeService.invoke_agent(run_id, assignment, context, db)` signature so all upstream schedulers, workflows, and routes continue working seamlessly.
> 2. **Canonical Governance Request Construction**:
>    - Builds normalized `GovernedRuntimeRequest` from `assignment` and `context` (`agent_id`, `schedule.workflow_id`, `model_id`, `requested_tool`, `tool_parameters`, `data_requests`, `facts`).
> 3. **Authoritative Decision Routing**:
>    - **`DENY`**: Immediately halts execution, publishes violation audit events (`UNAUTHORIZED_ACCESS_BLOCKED`), and raises `BoundaryViolationError`.
>    - **`REQUIRE_APPROVAL`**: Intercepts execution before tool/model invocation and returns an `APPROVAL_REQUIRED` structured gate envelope with approval requirements and trace.
>    - **`ESCALATE`**: Routes to escalation adapter and returns `ESCALATED` response.
>    - **`ALLOW` / `ALLOW_WITH_OBLIGATIONS`**: Invokes the gated model / tool adapter path, attaches data transformation and governance obligations, updates `WorkflowRunStep`, and returns the governed output.

## Open Questions

- None.

## Proposed Changes

### Agent Runtime Module

#### [MODIFY] [backend/app/modules/agent_runtime/service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_runtime/service.py)
- Wire `RuntimeEnforcementEngine` and `GovernedRuntimeContextBuilder` directly inside `AgentRuntimeService.invoke_agent`.
- Handle `DENY`, `REQUIRE_APPROVAL`, `ESCALATE`, and `ALLOW_WITH_OBLIGATIONS` decision routing.

#### [MODIFY] [backend/app/modules/agent_runtime/boundary_checker.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/agent_runtime/boundary_checker.py)
- Update `BoundaryChecker.check` to leverage `RuntimeEnforcementEngine`.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_runtime_enforcement_gateway.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_runtime_enforcement_gateway.py):
  1. **Gateway DENY Interception**: Verify `AgentRuntimeService.invoke_agent` raises `BoundaryViolationError` when boundary or tool guard returns `DENY`.
  2. **Gateway REQUIRE_APPROVAL Interception**: Verify `AgentRuntimeService.invoke_agent` intercepts requests needing approval without executing model/tool.
  3. **Gateway ALLOW & Execution Pass**: Verify compliant request executes through the gateway, applies data masking/obligations, and logs completion.
