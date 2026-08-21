# Implementation Plan - Prompt 6.2: Build Enforcement Simulation and Decision Detail (WBS 6.2)

Implement the non-authoritative Enforcement Simulation and Multi-Layered Decision Detail workspace ([frontend/src/pages/EnforcementSimulationPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/EnforcementSimulationPage.tsx), [backend/app/modules/enforcement/router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/router.py)) to simulate runtime evaluations across boundary, tool, data, model, and AST policy layers with zero target side-effects.

## User Review Required

> [!IMPORTANT]
> **Key Architecture Decisions & Non-Authoritative Guarantees**:
> 1. **Zero Side-Effect Simulation**:
>    - Uses `RuntimeEnforcementEngine.enforce(...)` under non-blocking mode without triggering mock or real Claude/tool execution adapters.
> 2. **Multi-Layered Trace Inspection**:
>    - Displays comprehensive layer-by-layer breakdown:
>      - Layer 1: Hard Runtime Boundaries (Agent active status, kill-switch, max autonomy)
>      - Layer 2: Entity Capability Guards (Tool permission, Data classification & field masking, Model compatibility)
>      - Layer 3: Dynamic AST Policy Engine (Effective policy version resolution, matched rule expressions)
>      - Layer 4: Decision Combiner (Precedence combination: DENY > REQUIRE_APPROVAL > ESCALATE > ALLOW_WITH_OBLIGATIONS > ALLOW)
> 3. **Actionable Remediation Guidance**:
>    - Displays actionable remediation hints and obligations (e.g. missing relationships, required approvals, or data masking requirements).

## Open Questions

- None.

## Proposed Changes

### Backend Simulation API

#### [NEW] [backend/app/modules/enforcement/router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/router.py)
- Expose `POST /api/v1/enforce/simulate`:
  - Builds `GovernedRuntimeRequest` via `GovernedRuntimeContextBuilder`.
  - Runs `RuntimeEnforcementEngine(db).enforce(request)`.
  - Returns complete `GovernedRuntimeResponse` with trace, matched rules, and remediation hints.

#### [MODIFY] [backend/app/main.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/main.py)
- Register enforcement simulation router.

### Frontend Simulation Page & Service

#### [NEW] [frontend/src/services/enforcement/enforcementService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/enforcement/enforcementService.ts)
- API client function `simulateEnforcement(payload)` communicating with `/api/v1/enforce/simulate`.

#### [NEW] [frontend/src/pages/EnforcementSimulationPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/EnforcementSimulationPage.tsx)
- Non-authoritative simulation workspace featuring:
  - Input request payload builder (Agent, Actor, Tool, Data Source, Model, Operation, Facts).
  - Pre-set simulation scenarios (e.g., *Blocked by Kill Switch*, *Data Masking Applied*, *Require Approval over Threshold*, *Valid Execution*).
  - Final decision overview card.
  - Interactive multi-layer verification trace.
  - Matched AST rules breakdown.
  - Obligations and remediation panel.

#### [MODIFY] [frontend/src/routes/AppRouter.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/routes/AppRouter.tsx)
- Register `/enforcement/simulate` route.

## Verification Plan

### Automated Tests / Builds
- Run `npm run build` in `frontend/` to ensure 100% clean compilation.
- Create [backend/app/tests/test_phase5_simulation_endpoint.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_simulation_endpoint.py) testing the simulation endpoint across permit, obligation, and deny scenarios.
- Run full backend test matrix.
