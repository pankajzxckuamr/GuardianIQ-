# Implementation Plan - Prompt 6.1: Build Agent Boundary / Tool / Data Access Tabs (WBS 6.1)

Extend the existing modal state machine in [frontend/src/components/registry/AgentFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/AgentFormModal.tsx) with comprehensive enforcement and boundary management tabs: **Autonomy & Limits**, **Tool Access**, **Data Access**, **Policies**, and **Enforcement History**, supported by reusable widgets under [frontend/src/components/common/](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/).

## User Review Required

> [!IMPORTANT]
> **Key Architecture Decisions & Corrections**:
> 1. **Modal Tab State Machine Extension (No standalone detail page)**:
>    - Extends `activeTab` in `AgentFormModal.tsx`:
>      - `details`: General metadata, execution mode, identification
>      - `relationships`: Model, Tool, Data Source, Workflow graph associations
>      - `autonomy`: Autonomy level, kill switch, rate limits, concurrency limits
>      - `tools`: Tool capability permissions, access modes, parameter constraints
>      - `data`: Data source permissions, classification ceiling, field masking
>      - `policies`: Direct & inherited compliance policies and version strategies
>      - `enforcement`: Recent enforcement decisions, reasons, and correlation traces
>      - `audit`: Entity audit trail
> 2. **Shared Common Widgets Pattern**:
>    - Creates reusable widgets with co-located CSS modules under `frontend/src/components/common/`:
>      - `KillSwitchControl.tsx` + `KillSwitchControl.module.css`
>      - `AutonomyLimitsTab.tsx` + `AutonomyLimitsTab.module.css`
>      - `ToolAccessTab.tsx` + `ToolAccessTab.module.css`
>      - `DataAccessTab.tsx` + `DataAccessTab.module.css`
>      - `AgentPoliciesTab.tsx` + `AgentPoliciesTab.module.css`
>      - `EnforcementHistoryTab.tsx` + `EnforcementHistoryTab.module.css`
> 3. **Permission Checks & Authoritative Backend**:
>    - Uses `/api/v1/agent-boundaries`, `/api/v1/policy-bindings/effective`, and `/api/v1/policies` for persistent enforcement state.

## Open Questions

- None.

## Proposed Changes

### Frontend Enforcement & Common Components

#### [NEW] [frontend/src/components/common/KillSwitchControl.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/KillSwitchControl.tsx) & `.module.css`
- Dedicated kill-switch widget with emergency indicator, confirmation modal, and status feedback.

#### [NEW] [frontend/src/components/common/AutonomyLimitsTab.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/AutonomyLimitsTab.tsx) & `.module.css`
- Configuration form for max autonomy level, allowed access modes, rate limit, max concurrency, sub-agent spawning, and approval threshold.

#### [NEW] [frontend/src/components/common/ToolAccessTab.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/ToolAccessTab.tsx) & `.module.css`
- Tool permissions table displaying bound tools, access modes (`READ`, `WRITE`, `ADMIN`), parameter constraints, and approval requirements.

#### [NEW] [frontend/src/components/common/DataAccessTab.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/DataAccessTab.tsx) & `.module.css`
- Data permissions table displaying data source bindings, classification ceiling, and field masking transformations (`MASK`, `REDACT`, `TOKENIZE`, `HASH`).

#### [NEW] [frontend/src/components/common/AgentPoliciesTab.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/AgentPoliciesTab.tsx) & `.module.css`
- Table of effective direct, inherited, and tenant-mandatory policies with priority and version strategies.

#### [NEW] [frontend/src/components/common/EnforcementHistoryTab.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/EnforcementHistoryTab.tsx) & `.module.css`
- Decision timeline showing recent runtime evaluations, decisions (`ALLOW`, `DENY`, `REQUIRE_APPROVAL`, `ESCALATE`), and violation reason codes.

### Agent Modal Integration

#### [MODIFY] [frontend/src/components/registry/AgentFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/AgentFormModal.tsx)
- Add new tabs to header and render corresponding tab components when editing an agent.

#### [MODIFY] [frontend/src/components/registry/AgentFormModal.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/AgentFormModal.module.css)
- Add tab styling for additional navigation items.

## Verification Plan

### Automated Tests / Builds
- Run `npm run build` in `frontend/` to ensure 100% clean compilation and zero TypeScript errors.
- Run backend pytest suite to verify all agent boundary and enforcement endpoints remain healthy.
