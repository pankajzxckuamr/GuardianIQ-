# Phase 5 Implementation Plan — Prompt 7.3: Regression and Defect Closure

## 1. Goal Description
Execute comprehensive regression testing and defect closure across all core and Phase 5 modules. Verify that runtime governance interceptors in `invoke_agent` (from 5.2) integrate seamlessly with workflow scheduler and orchestrator executions without breaking background job runs. Validate the broader backend test suite across registry, workflow, relationship, and event services, document zero open Critical defects, and record deferred items (such as pre-existing relationship effective date bypasses in legacy registry services).

---

## 2. Regression Testing Scope

### Core Regression Verification Paths
1. **Scheduled Workflow Execution (R-10)**:
   - Re-run workflow execution, scheduler, and runner test suites to ensure `invoke_agent` governance interception in `StepExecutor` cleanly handles allowed and blocked agent invocations without unhandled exceptions.
2. **Registry & Entity Management**:
   - Verify agent, tool, data source, and AI model registration, updates, and lookups remain functional.
3. **Relationship & Policy Binding Operations**:
   - Verify graph relationships and multi-target policy bindings remain stable.
4. **Phase 5 Full Governance Suite**:
   - Execute all 82 Phase 5 tests (AST policy engine, policy bindings, agent runtime boundaries, tool/data/model guards, enforcement gateway, simulation, and security/resilience suites).

### Scope Boundaries & Deferred Items
- Per specification correction: legacy call sites (`RegistryCheckService`, `ValidationEngine`, registry router) that ignore effective dates will be formally recorded as deferred known items for the 7.4 backlog and not modified during this sprint.

---

## 3. Implementation Steps

### 1. Test Suite Execution & Defect Verification
- Run workflow execution and scheduling tests:
  ```powershell
  pytest app/tests/ -k "workflow" -v
  ```
- Run registry and relationship tests:
  ```powershell
  pytest app/tests/ -k "registry or relationship" -v
  ```
- Run full Phase 5 governance suite:
  ```powershell
  pytest app/tests/ -k "phase5" -v
  ```
- Run complete repository test suite to identify and resolve any latent defect.

### 2. Defect Resolution & Fixes (if any discovered)
- Resolve any high/critical failures in runtime integration paths.

### 3. Deliverable: Regression and Defect Closure Report
- Create `c:\Users\aayus\Desktop\GuardianIQ--1\markdown\Phase5_regression_report_prompt_7_3.md` documenting:
  - Total tests executed and pass rates.
  - Verification of R-10 (workflow runner + governed `invoke_agent`).
  - Closed defects status (Zero Critical, High resolved).
  - Deferred backlog items.

---

## 4. Verification Plan
- Execute automated regression suite across backend.
- Validate zero breaking errors in workflow agent execution.
