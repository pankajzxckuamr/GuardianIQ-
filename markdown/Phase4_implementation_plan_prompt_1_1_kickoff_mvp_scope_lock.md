# Implementation Plan - Prompt 1.1: Kickoff and MVP Scope Lock (WBS 4.1.1, 4.1.2)

Establish Phase 4 MVP Scope Lock and produce a signed-off scope note defining the exact boundaries for Phase 4 Event-Driven Governance Architecture.

## User Review Required

> [!IMPORTANT]
> **MVP Scope Boundaries**: Confirming exact IN-SCOPE and OUT-OF-SCOPE components for Phase 4 MVP to prevent scope creep.

## Open Questions

- None.

## Scope Lock Summary

### In-Scope Deliverables (Phase 4 MVP Sprint)
1. **`governance_events` Event Store**: Immutable database table storing structured governance events.
2. **`event_outbox` + Outbox Dispatcher**: Reliable transactional outbox table and polling/dispatching worker mechanism.
3. **`EventPublisherService`**: Central service interface for transactional event publishing across modules.
4. **Event Query REST APIs**: `/api/v1/events` endpoint suite supporting filtering, pagination, search, and details.
5. **Audit Timeline Reconstruction**: Backend service to construct unified chronological audit trails for entities (agents, workflows, models).
6. **Event Explorer UI**: Built directly into the existing [AuditPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/AuditPage.tsx) (`/audit` route).
7. **Dead Letter Queue (DLQ) Review**: UI tab/view and API endpoints to inspect, retry, or archive failed outbox messages.
8. **Audit Export**: Export audit timelines and event query results to CSV/JSON format.

### Out-of-Scope Items (Deferred to Future Phases)
1. **Full Event Replay**: Replaying state from event log streams.
2. **External Message Broker Infra**: Dedicated Kafka / AWS EventBridge infrastructure setup.
3. **Full Compliance Automation Engine**: Automatic dynamic compliance enforcement engines beyond core event tracking.
4. **`WorkflowRun`/`WorkflowRunStep` Schema Changes**: Adding direct FK relations for agents/tools inside execution run tables.

## Proposed Changes

### Documentation & Scope Artifacts

#### [NEW] [Phase4_MVP_Scope_Lock_Note.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_MVP_Scope_Lock_Note.md)
- Signed-off document recording WBS 4.1.1 and 4.1.2 MVP scope lock, architectural principles, in-scope deliverables, and out-of-scope boundaries.

#### [NEW] [Phase4_implementation_plan_prompt_1_1_kickoff_mvp_scope_lock.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_1_1_kickoff_mvp_scope_lock.md)
- Standardized task implementation plan saved to the project `markdown/` repository directory.

## Verification Plan

### Manual Verification
- Review signed-off scope note in [Phase4_MVP_Scope_Lock_Note.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/docs/Phase%204/Phase4_MVP_Scope_Lock_Note.md).
- Validate alignment with Phase 4 scope specification (`docs/Phase 4/Phase4-scope.pdf`) and WBS deliverables.
