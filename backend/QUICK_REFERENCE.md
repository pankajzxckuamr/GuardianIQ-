# Quick Reference: API Standardization Implementation

## Response Format (All Endpoints)

```json
{
  "status": "success",           // or "error"
  "request_id": "uuid-string",   // auto-generated or from X-Request-ID header
  "message": "Human readable",   // optional
  "data": {}                     // the actual response data
}
```

## Common Response Patterns

### List Endpoint
```python
from app.shared.response_utils import ResponseHelper

@router.get("", response_model=StandardResponse[list[ItemResponse]])
def get_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return ResponseHelper.list_response(
        items=items,
        message="Items retrieved successfully"
    )
```

### Create Endpoint
```python
@router.post("", response_model=StandardResponse[ItemResponse])
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    item = Item(**payload.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return ResponseHelper.created(
        data=item,
        message="Item created successfully"
    )
```

### Paginated Endpoint
```python
@router.get("/paginated", response_model=StandardResponse)
def get_items_paginated(
    skip: int = 0, 
    limit: int = 10,
    db: Session = Depends(get_db)
):
    items = db.query(Item).offset(skip).limit(limit).all()
    total = db.query(Item).count()
    
    return ResponseHelper.paginated(
        items=items,
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )
```

### With User Context
```python
from app.core.middleware import set_user_context

@router.get("/me", response_model=StandardResponse[UserResponse])
def get_current_user(current_user: User = Depends(get_current_user)):
    # Set user context for logging and tracing
    set_user_context(str(current_user.id), current_user.email)
    
    return ResponseHelper.success(
        data=current_user,
        message="Current user retrieved"
    )
```

## Accessing Request ID in Services

```python
from app.core.middleware import get_request_id
import logging

logger = logging.getLogger(__name__)

def my_service():
    request_id = get_request_id()
    logger.info(f"[{request_id}] Processing...", extra={"request_id": request_id})
```

## Client Headers

### Send Custom Request ID
```bash
curl -X GET http://api/items \
  -H "X-Request-ID: my-custom-id-123"
```

### Receive Request ID
```bash
# Response includes:
# X-Request-ID: my-custom-id-123
# X-Request-Time: 1622548800.123456
```

## Error Handling

Errors are automatically standardized:

```json
{
  "status": "error",
  "request_id": "uuid",
  "message": "Invalid input: email is required",
  "data": null
}
```

### Custom Error Response
```python
from fastapi import HTTPException

@router.get("/{item_id}", response_model=StandardResponse[ItemResponse])
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )
    
    return ResponseHelper.success(data=item)
```

## Middleware Stack

```
Request → LoggingMiddleware → ResponseStandardizationMiddleware → RequestIDMiddleware → Route Handler → Response
```

1. **RequestIDMiddleware** (innermost)
   - Generates request ID
   - Sets in context

2. **ResponseStandardizationMiddleware**
   - Wraps responses in StandardResponse
   - Adds request ID to response

3. **LoggingMiddleware** (outermost)
   - Logs request/response with request ID
   - Tracks duration

## Helper Methods

```python
from app.shared.response_utils import ResponseHelper

# Success response with data
ResponseHelper.success(data=obj, message="...")

# Error response
ResponseHelper.error(message="Error occurred", data=None)

# Created response (201)
ResponseHelper.created(data=obj, message="...")

# Paginated list
ResponseHelper.paginated(
    items=items,
    total=100,
    page=1,
    page_size=10
)

# Simple list
ResponseHelper.list_response(items=items, message="...")
```

## Integration Checklist

For new routes:
- [ ] Import `ResponseHelper` from `app.shared.response_utils`
- [ ] Set `response_model=StandardResponse[YourResponse]`
- [ ] Return `ResponseHelper.success()` or `ResponseHelper.created()`
- [ ] Include meaningful messages
- [ ] Add `set_user_context()` if user is available
- [ ] Use proper response methods for list/paginated endpoints

## Testing

### Health Check
```bash
curl -X GET http://localhost:8000/api/health
```

### List Request
```bash
curl -X GET http://localhost:8000/api/items \
  -H "X-Request-ID: test-123"
```

### Create Request
```bash
curl -X POST http://localhost:8000/api/items \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: test-123" \
  -d '{"name": "Test Item"}'
```

All responses will have:
- `status`: "success" or "error"
- `request_id`: From header or auto-generated
- `message`: Descriptive text
- `data`: Response payload or null

## Documentation File
Full implementation details in: `backend/API_STANDARDIZATION.md`
