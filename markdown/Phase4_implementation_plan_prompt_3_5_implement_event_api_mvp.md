# Implementation Plan - Prompt 3.5: Implement Event API MVP (WBS 4.3.5)

Implement REST API endpoints under `/api/v1/events` with permission guards, standardized response wrappers, and API test suite.

## User Review Required

> [!IMPORTANT]
> **New Permission Codes (UPPERCASE_SNAKE_CASE)**: `CREATE_EVENT`, `VIEW_EVENTS`, `VIEW_AUDIT_TIMELINE` integrated via `require_permission` dependency in [dependencies.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/auth/dependencies.py#L60).
> **Standardized Response Envelope**: All endpoints wrap response objects using `ResponseHelper.success` / `ResponseHelper.error` from [response_utils.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/shared/response_utils.py#L12) with auto-populated `request_id`.

## Open Questions

- None.

## API Endpoint Specification

1. **`POST /api/v1/events`**: `require_permission("CREATE_EVENT")` — Ingest governance event.
2. **`GET /api/v1/events`**: `require_permission("VIEW_EVENTS")` — Search events with paginated filters.
3. **`GET /api/v1/events/{event_id}`**: `require_permission("VIEW_EVENTS")` — Fetch single event by UUID.
4. **`GET /api/v1/events/subject/{entity_type}/{entity_id}`**: `require_permission("VIEW_AUDIT_TIMELINE")` — Subject timeline reconstruction.
5. **`GET /api/v1/events/correlation/{correlation_id}`**: `require_permission("VIEW_AUDIT_TIMELINE")` — Correlation trace stream.

## Proposed Changes

### Backend Implementation

#### [MODIFY] [router.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/events/router.py)
- Implement 5 REST API routes with `ResponseHelper` standard envelopes.

#### [MODIFY] [main.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/main.py)
- Include `events_router` into FastAPI application.

#### [NEW] [test_event_api_routes.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_event_api_routes.py)
- API test suite executing HTTP GET/POST calls across `/api/v1/events` routes.

### Documentation Artifacts

#### [NEW] [Phase4_implementation_plan_prompt_3_5_implement_event_api_mvp.md](file:///c:/Users/aayus/Desktop/GuardianIQ--1/markdown/Phase4_implementation_plan_prompt_3_5_implement_event_api_mvp.md)
- Implementation plan saved in `markdown/`.

## Verification Plan

### Automated / API Test Verification
1. Run pytest suite: `pytest app/tests/test_event_api_routes.py`
2. Confirm 200 OK responses, standard envelope formatting (`status`, `request_id`, `data`), and 404/403 status codes.
