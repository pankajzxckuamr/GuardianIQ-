# Implementation Plan - Prompt 5.5: Build Audit Export Panel (WBS 4.5.5)

Build the Audit Export panel at `/audit/export` with a reusable shared `ExportModal` component, export parameter configuration form (subject, correlation_id, date range, event_type, classification, format, justification reason), integration with `POST /api/v1/audit/export`, and export package status/history view via `GET /api/v1/audit/export/{id}`.

## User Review Required

> [!IMPORTANT]
> **Shared Export Dialog**: Creates `frontend/src/components/common/ExportModal.tsx` & `.module.css` for configuring and submitting audit export requests with input validation and loading states.
> **Cryptographic Package Verification**: Displays the SHA-256 `export_hash` and manifest metadata for compliance auditing.

## Proposed Changes

### Shared Components

#### [NEW] [ExportModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/ExportModal.tsx)
#### [NEW] [ExportModal.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/ExportModal.module.css)
- Reusable modal dialog with input fields for subject filter, correlation ID, date range, event type, classification, export format, and justification reason.

### Audit Service

#### [MODIFY] [auditService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/audit/auditService.ts)
- Add `AuditExportPayload` and `AuditExportResult` interfaces.
- Add `createAuditExport(token, payload)` and `getAuditExportStatus(token, id)`.

### Frontend Pages

#### [MODIFY] [AuditExportPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/AuditExportPage.tsx)
#### [NEW] [AuditExportPage.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/AuditExportPage.module.css)
- Full Audit Export dashboard displaying export package configuration launcher, recent generated package list, manifest metadata inspector, and SHA-256 integrity verification details.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_5_5_build_audit_export_panel.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_5_5_build_audit_export_panel.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated Tests
1. Run `npm run build` in `frontend/` to verify zero TypeScript or CSS module compilation errors.
2. Run backend integration tests (`pytest app/tests/test_audit_export_api.py`).

### Manual Verification
1. Navigate to `/audit/export`.
2. Click "Generate Export Package" to open `ExportModal`.
3. Fill out filter criteria and click "Export Audit Package".
4. Confirm generated package displays in history table with valid SHA-256 `export_hash`.
