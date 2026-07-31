# Implementation Plan - Prompt 5.6: Build Event Dashboard Widgets (WBS 4.5.6)

Enhance `frontend/src/pages/DashboardPage.tsx` with live event telemetry widgets (Event Volume, Policy Violations, Blocked Agent Actions, Outbox Lag, Dead Letter Queue, and SLA Breaches) wired to `GET /api/v1/events/metrics`.

## User Review Required

> [!IMPORTANT]
> **Existing Dashboard Integration**: Adds event telemetry metric cards and breakdown panels directly to the existing `DashboardPage.tsx` without creating a duplicate dashboard.
> **Interactive Navigation**: Clicking on metrics routes users directly to corresponding deep views (e.g. Dead Letter Queue card opens `/audit/dead-letter`, Audit Trail card opens `/audit`).

## Proposed Changes

### Audit Service

#### [MODIFY] [auditService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/audit/auditService.ts)
- Add `EventMetrics` interface.
- Add `fetchEventMetrics(token)` function calling `GET /api/v1/events/metrics`.

### Dashboard Page

#### [MODIFY] [DashboardPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/DashboardPage.tsx)
- Integrate `fetchEventMetrics` in `useEffect`.
- Render 6 new telemetry metric cards:
  - **Total Event Volume** (`total_events_count`)
  - **Policy Violations** (`policy_violations_count`)
  - **Blocked Agent Actions** (`blocked_agent_actions_count`)
  - **Outbox Processing Lag** (`outbox_lag_seconds` in seconds)
  - **Dead Letter Queue (DLQ)** (`dead_letter_count` unresolved items)
  - **SLA & Risk Breaches** (`sla_breaches_count`)
- Add category breakdown telemetry bar for quick visual inspection.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_5_6_build_event_dashboard_widgets.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_5_6_build_event_dashboard_widgets.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated Tests
1. Run `npm run build` in `frontend/` to verify zero TypeScript compilation or CSS module errors.
2. Run backend unit tests (`pytest app/tests/test_event_metrics.py`).

### Manual Verification
1. Open `/dashboard`.
2. Verify event telemetry cards display real values from `/api/v1/events/metrics`.
3. Click "Dead Letter Queue" metric card and verify navigation to `/audit/dead-letter`.
