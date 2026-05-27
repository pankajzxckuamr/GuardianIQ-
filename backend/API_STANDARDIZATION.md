# API Standardization & Middleware Implementation

## Overview
This document describes the centralized middleware and request standardization implementation for the GuardianIQ API.

## Components Implemented

### 1. **Centralized Middleware** (`app/core/middleware.py`)

#### RequestIDMiddleware
- **Purpose**: Generates unique request IDs and propagates them through the request lifecycle
- **Features**:
  - Auto-generates UUID for each request (or uses existing X-Request-ID header)
  - Stores request ID in context variable for access throughout the request
  - Adds X-Request-ID response header for client tracking
  - Adds X-Request-Time response header for timing information

#### ResponseStandardizationMiddleware
- **Purpose**: Automatically wraps all successful API responses in StandardResponse format
- **Features**:
  - Detects and wraps raw JSON responses
  - Skips already-wrapped responses to avoid double-wrapping
  - Maintains original status codes
  - Automatically includes request ID in all responses

#### LoggingMiddleware
- **Purpose**: Structured logging with request ID propagation
- **Features**:
  - Logs request entry and exit
  - Includes request ID in all log entries
  - Tracks request duration
  - Logs HTTP status codes
  - User context awareness (when set)

### 2. **StandardResponse Format**

All API responses follow this format:

```json
{
  "status": "success|error",
  "request_id": "uuid",
  "message": "Optional human-readable message",
  "data": {}
}
```

### 3. **Response Utilities** (`app/shared/response_utils.py`)

Helper class `ResponseHelper` provides convenient methods:

```python
ResponseHelper.success(data, message)      # Success response
ResponseHelper.error(message, data)         # Error response
ResponseHelper.created(data, message)       # 201 Created
ResponseHelper.paginated(items, total, page, page_size)  # Paginated list
ResponseHelper.list_response(items, message)  # List response
```

### 4. **Request ID Propagation**

Available functions in `app/core/middleware.py`:

```python
get_request_id() -> str              # Get current request ID
set_user_context(user_id, email)     # Set user info for logging
get_user_context() -> dict           # Get user info from context
```

## Implementation Details

### Middleware Order
Middleware is applied in this order in `main.py`:
1. **LoggingMiddleware** (outermost) - Logs request/response
2. **ResponseStandardizationMiddleware** - Wraps responses
3. **RequestIDMiddleware** (innermost) - Generates request ID

This ensures:
- Request IDs are available for logging
- All responses are standardized
- Proper lifecycle management

### Route Updates
All route files have been updated to:
1. Use `StandardResponse[T]` as response_model
2. Use `ResponseHelper` for creating responses
3. Include meaningful messages

#### Updated Routes:
- `app/modules/auth/routes.py` - Uses ResponseHelper
- `app/modules/audit/routes.py` - Standardized responses
- `app/modules/department/routes.py` - Standardized responses
- `app/modules/policy/routes.py` - Standardized responses
- `app/modules/datasource/routes.py` - Standardized responses

### Exception Handling
Exception handlers in `app/core/exceptions.py` automatically:
- Include request ID in error responses
- Use StandardResponse format
- Handle validation errors
- Handle HTTP exceptions
- Catch-all for unexpected errors

## Usage Examples

### In Route Handlers
```python
from app.shared.response_utils import ResponseHelper
from app.core.middleware import get_request_id, set_user_context

@router.get("", response_model=StandardResponse[list[UserResponse]])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    
    # Set user context for logging (if available)
    set_user_context(current_user.id, current_user.email)
    
    return ResponseHelper.list_response(
        items=users,
        message="Users retrieved successfully"
    )
```

### Accessing Request ID in Services
```python
from app.core.middleware import get_request_id

def service_function():
    request_id = get_request_id()  # Available in any service called during request
    logger.info(f"[{request_id}] Processing...", extra={"request_id": request_id})
```

### Client-Side Usage
```bash
# Request
curl -X GET http://api/users \
  -H "X-Request-ID: custom-id-123"

# Response
{
  "status": "success",
  "request_id": "custom-id-123",  # Or auto-generated
  "message": "Users retrieved successfully",
  "data": [...]
}

# Headers
X-Request-ID: custom-id-123
X-Request-Time: 1622548800.123456
```

## Best Practices

1. **Always use ResponseHelper**: Ensures consistency across all endpoints
2. **Include messages**: Provide meaningful messages for each response
3. **Set user context**: Call `set_user_context()` when user info is available for better logging
4. **Use proper status codes**: ResponseHelper.created() for 201, etc.
5. **Request ID tracking**: Use X-Request-ID header from client for distributed tracing
6. **Logging**: Always include request ID in logs for traceability

## Configuration

### Environment Variables (if needed in future)
```
LOG_LEVEL=INFO
REQUEST_TIMEOUT=30
```

## Files Modified/Created

### Created:
- `app/core/middleware.py` - Centralized middleware
- `app/shared/response_utils.py` - Response utilities

### Updated:
- `app/core/logging.py` - Logging configuration
- `app/core/exceptions.py` - Exception handlers with new middleware integration
- `app/main.py` - Middleware registration
- `app/modules/auth/routes.py` - Uses ResponseHelper
- `app/modules/audit/routes.py` - Standardized responses
- `app/modules/department/routes.py` - Standardized responses
- `app/modules/policy/routes.py` - Standardized responses
- `app/modules/datasource/routes.py` - Standardized responses

## Testing the Implementation

### Health Check
```bash
curl -X GET http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "success",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "GuardianIQ backend running",
  "data": {"status": "healthy"}
}
```

### Error Response
```bash
curl -X GET http://localhost:8000/api/invalid
```

Expected response:
```json
{
  "status": "error",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Not Found",
  "data": null
}
```

## Future Enhancements

1. **Request/Response Logging**: Add middleware to log request/response bodies for debugging
2. **Rate Limiting**: Integrate rate limiting middleware with request ID tracking
3. **Request Validation Schema**: Create JSON schema validation with request ID in errors
4. **Distributed Tracing**: Enhanced support for OpenTelemetry
5. **API Versioning**: Header-based or URL-path API version support
