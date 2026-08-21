# Implementation Plan - Prompt 5.1: Build Governance Context Builder and Decision Combiner Integration (WBS 5.1)

Build the unified enterprise `GovernanceContextBuilder` and multi-layered `RuntimeEnforcementEngine` synthesizing layer-by-layer evaluation across Relationship Guards, Hard Boundary Guards (Agent Boundary, Tool Guard, Data Guard, Model Guard), and Dynamic Policy Engine (Binding Resolver + Rule Evaluator), combining results into an authoritative `GovernedRuntimeResponse` with complete trace, reasons, violations, and obligations.

## User Review Required

> [!IMPORTANT]
> **Multi-Layered Governance Enforcement Pipeline**:
> 1. **Layer 1: Context Normalization & Enrichment (`GovernanceContextBuilder`)**:
>    - Builds canonical `GovernedRuntimeRequest` incorporating actor, agent, workflow, model, tool, data requests, environment, and evaluation facts.
> 2. **Layer 2: Hard Boundary Guards**:
>    - **Agent Boundary**: Evaluates status, autonomy rank, kill-switch, sub-agent spawning, and financial transaction thresholds via `AgentBoundaryResolver`.
>    - **Tool Guard**: Evaluates `USES_TOOL` relationship, capability existence, access modes, and parameter constraints via `ToolPermissionGuard`.
>    - **Data Guard**: Evaluates `USES_DATA_SOURCE` relationship, classification ceilings, transformations (`MASK`, `REDACT`, etc.), and record limits via `DataPermissionGuard`.
>    - **Model Guard**: Evaluates `USES_MODEL` relationship, environment compatibility, approved version, and provider data residency via `ModelProviderGuard`.
> 3. **Layer 3: Dynamic Policy Engine**:
>    - Resolves bound policies via `BindingResolver` and evaluates AST/JSON rules via `SafeRuleEvaluator`.
> 4. **Layer 4: Decision Combining & Trace**:
>    - Strictly combines layer decisions: $\text{DENY} > \text{REQUIRE\_APPROVAL} > \text{ESCALATE} > \text{ALLOW\_WITH\_OBLIGATIONS} > \text{ALLOW}$.
>    - Produces a comprehensive layer-by-layer explainability trace and synthesizes all obligations (masking, rate limits, telemetry, approval requirements).

## Open Questions

- None.

## Proposed Changes

### Enforcement Module

#### [MODIFY] [backend/app/modules/enforcement/context_builder.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/context_builder.py)
- Enrich `GovernedRuntimeContextBuilder` with auto-population of metadata and environment parameters.

#### [MODIFY] [backend/app/modules/enforcement/engine.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/engine.py)
- Update `RuntimeEnforcementEngine.enforce(request, tenant_id, as_of)`:
  - Executes Layer 2 (Agent Boundary, Tool Guard, Data Guard, Model Guard).
  - Executes Layer 3 (Policy Engine resolution + Safe Rule evaluation).
  - Executes Layer 4 (Decision Combining with layer-by-layer trace synthesis and obligation aggregation).

#### [MODIFY] [backend/app/modules/enforcement/__init__.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/enforcement/__init__.py)
- Export updated engine and context builder classes.

## Verification Plan

### Automated Tests
- Create [backend/app/tests/test_phase5_enforcement_engine_integration.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_phase5_enforcement_engine_integration.py):
  1. **Multi-Layered Pass Test**: Verify a fully compliant request passes all layers and returns `Decision.ALLOW` with complete trace.
  2. **Agent Boundary Layer Interception**: Verify boundary kill-switch / autonomy limits intercept execution at Layer 2.
  3. **Tool Guard Layer Interception**: Verify unauthorized tool operation intercepts execution at Layer 2.
  4. **Data Guard Transformation Integration**: Verify data masking obligations flow through Layer 2 to final combined result.
  5. **Dynamic Policy Engine Interception**: Verify custom policy rules in Layer 3 block or require approval on requests that passed Layer 2.
  6. **Strict Decision Combiner Precedence**: Verify combined decision precedence across layers.
