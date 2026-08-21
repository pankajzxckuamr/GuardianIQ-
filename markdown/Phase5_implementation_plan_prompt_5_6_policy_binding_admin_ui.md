# Implementation Plan - Prompt 5.6: Build Minimal Policy & Binding Administration UI (WBS 5.6)

Implement the Policy & Binding Administration UI in the React frontend ([frontend/src/pages/PoliciesDashboardPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/PoliciesDashboardPage.tsx), [frontend/src/components/policies/](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/policies/), [frontend/src/services/policies/](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/policies/)) providing Policy List, Policy Detail, Active Version Summary, Binding Manager Drawer, and Applicable Policies Panel.

## User Review Required

> [!IMPORTANT]
> **Key Architecture Decisions & Conventions**:
> 1. **Zero External Query Dependencies**:
>    - Uses existing `useRegistryEntity` hook and standard React hooks (`useState`, `useEffect`, `useSearchParams`). No React Query.
> 2. **Full Design System Integration**:
>    - Adheres to GuardianIQ design system (`ModuleLayout`, glassmorphism dark/light tokens, Lucide icons, status badges, and slide-over drawers).
> 3. **Authoritative Backend**:
>    - Communicates with `/api/v1/policies` and `/api/v1/policy-bindings` for policy creation, version activation, policy binding attachment, and effective policy resolution.

## Open Questions

- None.

## Proposed Changes

### Backend API Extensions

#### [MODIFY] [backend/app/modules/policy_engine/router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/policy_engine/router.py)
- Ensure `GET /api/v1/policy-bindings` endpoint exists to list all bindings for a tenant/policy/target.

### Frontend Policy Services & Types

#### [NEW] [frontend/src/types/policy.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/types/policy.ts)
- TypeScript definitions for `Policy`, `PolicyVersion`, `PolicyRule`, `PolicyBinding`, `EffectiveBinding`, `PolicyCreatePayload`, and `PolicyBindingCreatePayload`.

#### [NEW] [frontend/src/services/policies/policyService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/policies/policyService.ts)
- API client functions:
  - `fetchPolicies(category?, status?)`
  - `fetchPolicyDetails(policyId)`
  - `fetchPolicyVersions(policyId)`
  - `createPolicy(payload)`
  - `activatePolicyVersion(policyId, versionId)`
  - `createPolicyBinding(payload)`
  - `fetchEffectiveBindings(targetType, targetId)`
  - `revokePolicyBinding(bindingId)`

### Frontend UI Components & Pages

#### [NEW] [frontend/src/components/policies/PolicyListTable.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/policies/PolicyListTable.tsx)
- Searchable, filterable list of policies with category badges, enforcement mode, active version, status, and quick actions.

#### [NEW] [frontend/src/components/policies/PolicyDetailView.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/policies/PolicyDetailView.tsx)
- Detailed view showing policy metadata, active rules breakdown, version history snapshots, and version activation buttons.

#### [NEW] [frontend/src/components/policies/AttachPolicyDrawer.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/policies/AttachPolicyDrawer.tsx)
- Slide-over drawer to attach a policy to an `AGENT`, `WORKFLOW`, `TOOL`, or `DATA_SOURCE` with version strategy (`LATEST` vs `PINNED`), priority, scope, and mandatory flag.

#### [NEW] [frontend/src/components/policies/ApplicablePoliciesPanel.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/policies/ApplicablePoliciesPanel.tsx)
- Interactive resolution inspector showing direct vs inherited policies for any selected agent, tool, or workflow.

#### [MODIFY] [frontend/src/pages/PoliciesDashboardPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/PoliciesDashboardPage.tsx)
- Wire complete Policy & Binding Administration workspace with tabbed navigation: **Policies**, **Bindings Manager**, and **Effective Resolver**.

## Verification Plan

### Automated Tests / Builds
- Run `npm run build` in `frontend/` to ensure 100% clean TypeScript compilation and zero bundle errors.
- Run backend pytest suite to verify all API endpoints respond properly.
