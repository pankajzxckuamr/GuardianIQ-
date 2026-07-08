# Implementation Plan - Workflow Scheduler API Enhancements

This plan outlines the changes required to satisfy the 10 test scenarios for the workflow scheduler REST APIs.

## Proposed Changes

### Workflow Scheduler Router

#### [MODIFY] [phase2_scheduler_routes.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/api/phase2_scheduler_routes.py)
- Import `Response` from `fastapi`.
- Inject `response: Response` into all endpoints to allow dynamically setting standard HTTP status codes on errors/success:
  - Update `create_schedule` to return `201 Created` on success.
  - Set `response.status_code = e.status_code` when catching `HTTPException`.
  - Set `response.status_code = 409` when catching `WorkflowScheduleStateError`.
  - Set `response.status_code = 500` for general unhandled exceptions.
- In `list_schedules`, support both `page_size` and `per_page` query parameters to prevent parameter mismatch, defaulting to 20.

### Authorization Decision Service

#### [MODIFY] [decision_service.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/authorization/decision_service.py)
- Commit the transaction immediately when logging `AUTHORIZATION_DENIED` inside `publish_event` to prevent it from being rolled back by the router when raising an `HTTPException(status_code=403)`.

### Test Suite

#### [MODIFY] [test_workflow_scheduler.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_workflow_scheduler.py)
- Update existing assertion on schedule creation success from `200` to `201` to align with the new standard.

## Verification Plan

### Automated Tests
- Run `venv\Scripts\python -m pytest app\tests\test_workflow_scheduler.py`
- Run `venv\Scripts\python -m pytest app\tests\test_authorization.py`
