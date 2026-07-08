# GuardianIQ Phase 3 Implementation Plan

This document outlines the execution plan for Phase 3, driven by the findings in Volume 1 (Architecture), Volume 2A (UX Foundation), and the Phase 3 Project Plan.

## Summary of Understanding

- **Volume 1 (Relationship Architecture)**: Establishes the relationship semantic layer connecting AI assets, workflows, policies, and audits. It mandates specific physical schemas (`generic_relationships`, `object_responsibilities`, etc.), validation rules, graph traversals, and API structures.
- **Volume 2A (UX Foundation)**: Defines the developer-ready UI/UX standards, navigation hierarchy, component patterns, and page templates (e.g., Dashboards, Relationship Explorer, Details View). It ensures context travels with the user across different screens.
- **Phase 3 Plan (Excel)**: Outlines a concrete 1-week execution sprint to establish end-to-end readiness (DB → API → UI → QA). It defines the daily schedule and RACI matrix (Aayush driving DB, Pankaj driving Backend, Poorvith driving Frontend, and PM overseeing).

## Proposed Changes

### Database & Repositories (Owner: Aayush)
- Write DDL migrations for Phase 3 tables: `generic_relationships`, `object_responsibilities`, `relationship_validation_results`, `relationship_graph_snapshots`, `policy_bindings`, `evidence_links`.
- Create composite indexes and constraints for time-aware and scoped relationship resolution.
- Generate seed data for relationship types, lifecycle states, and responsibility types.
- Ensure all DB layers include `tenant_id` and handle soft deletes.

### Backend Services & APIs (Owner: Pankaj)
- Implement SQLAlchemy ORM models and Pydantic schemas.
- Build the `RelationshipService` (CRUD), `ResponsibilityService` (owner/approver assignments), and `ValidationEngine` (mandatory rules like duplicate edges, scope validation).
- Implement Graph and Resolver APIs (`GraphService`, `RelationshipResolverService`) for governance context, timeline generation, and downstream impact analysis.
- Connect the `RelationshipAuditService` to ensure all APIs publish audit events and enforce authorization checks.

### Frontend UI & UX (Owner: Poorvith)
- Define the React route/module structure in `src/app/pages/` according to Volume 2A standards.
- Build the core pages using the defined Page Templates:
  - **Relationship Explorer** (List View template).
  - **Create Relationship Wizard** (Wizard template).
  - **Object Relationship Panel** (Details View embedded).
  - **Graph View MVP** (Explorer View template).
- Integrate backend APIs, observing standard response envelopes and permission-aware button rendering.

### Integration & QA (Owners: Pankaj & PM)
- Create screen/API/DB mapping matrix.
- Execute End-to-End integration for the Relationship Creation Flow (UI → API → DB → Audit).
- Execute API, DB, and UI negative/positive tests per the Validation Rules (RV-001 through RV-090).
- Prepare a Developer Handover Pack with DB scripts, API specs, and test evidence for final sign-off.

## Verification Plan

### Automated Tests
- Run Backend Unit and Integration tests on Repository functions, Validation Engine rules, and API endpoints.
- Ensure no unbounded graph queries execute without depth limits.

### Manual Verification
- End-to-end manual QA on UI functional flows (Wizard creation, object linkage, etc.).
- Final UAT walkthrough involving all team members to verify Definition of Done.
