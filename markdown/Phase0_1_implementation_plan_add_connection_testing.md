# Implementation Plan - Add Connection Testing Feature for Data Sources

This plan outlines the design and implementation for adding a "Test Connection" button next to the Connection Reference field in the Data Source registration/edit form.

## User Review Required

> [!NOTE]
> **Mock vs Real Testing:** 
> The connection test logic will automatically detect whether the connection URI points to a mockup/demo resource (e.g. containing `.internal` or `careshield.com`) and return a mock successful handshake. For real endpoints (like public APIs or database servers), it will perform active TCP socket/HTTP validation with short timeouts. This ensures mock data works flawlessly while actual connections are verified properly.

## Proposed Changes

---

### [Frontend Component]

We will modify the frontend Data Source form modal to include a "Test Connection" button next to the Connection Reference input and handle the backend API call to display verification messages.

#### [MODIFY] [DataSourceFormModal.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/DataSourceFormModal.tsx)
- Add state variables: `testingConnection` (boolean) and `connectionTestMessage` (string | null, with styling/success indicators).
- Implement a `handleTestConnection` function that sends a POST request to `/api/registry/data-sources/test-connection` with the current `connection_reference` value.
- Wrap the Connection Reference input field in a flex container and place the "Test Connection" button directly beside it.
- Render the test result message below the input field in green (for success) or red (for failure) depending on the result.

#### [MODIFY] [DataSourceFormModal.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/DataSourceFormModal.module.css)
- Add styles for the connection test button and success/failure test result alerts.

#### [MODIFY] [registryService.ts](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/services/registry/registryService.ts)
- Add a new client service function `testConnection(connectionReference: string)` to invoke the new backend endpoint.

---

### [Backend Modules]

We will add a new Pydantic schema, service validation logic, and a FastAPI endpoint.

#### [MODIFY] [schemas.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/schemas.py)
- Create `ConnectionTestPayload` Pydantic model:
  ```python
  class ConnectionTestPayload(BaseModel):
      connection_reference: str
  ```

#### [MODIFY] [routes.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/routes.py)
- Add a new POST route `@data_sources_router.post("/data-sources/test-connection")` that takes `ConnectionTestPayload` and calls the service logic.

#### [MODIFY] [services.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/modules/registry/services.py)
- Implement `test_connection_reference(connection_reference: str) -> dict` with parsing and routing:
  - If a mockup domain (e.g. `careshield.internal`), return a mock successful validation response.
  - If an HTTP/HTTPS URL, perform a lightweight HEAD request using `httpx`.
  - If a Database URI (e.g. `postgresql://`, `mysql://`), perform a TCP socket connection test on the target hostname/port.
  - Return detailed status success/fail messages.

## Verification Plan

### Automated Tests
- Create a unit test `test_data_source_connection_test` in [test_registry.py](file:///c:/Users/aayus/Desktop/GuardianIQ--1/backend/app/tests/test_registry.py) to verify:
  1. Testing a mock HTTP connection returns success.
  2. Testing a mock DB connection returns success.
  3. Testing an invalid connection reference returns validation failure.

### Manual Verification
- Open the Edit Data Source form in the browser.
- Verify that clicking "Test Connection" alongside `https://ehr-stream.careshield.internal/v1/notes` yields a success message.
- Verify that entering an invalid schema or non-resolving domain displays the correct error message.
