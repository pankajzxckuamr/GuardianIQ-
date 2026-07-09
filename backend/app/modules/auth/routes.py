from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.models import User, Role, Permission
from app.modules.audit.service import create_audit_event
from app.modules.audit.schemas import AuditEventCreate
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token
)
from app.core.config import settings
from jose import jwt, JWTError
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.auth.schemas import TokenResponse, RefreshTokenRequest, RoleResponse, PermissionResponse, ChangePasswordRequest
from app.modules.auth.models import TokenBlocklist
from app.modules.auth.dependencies import oauth2_scheme
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper
from app.core.middleware import get_request_id, set_user_context
from typing import List, Any

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)


@router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    Returns access_token at root level (OAuth2 spec) for Swagger compatibility,
    plus full StandardResponse fields for the frontend.
    """
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user:
        create_audit_event(
            db,
            AuditEventCreate(
                event_type="auth.login_failure",
                entity_type="user",
                action="login",
                event_metadata={
                    "ip_address": request.client.host if request.client else "127.0.0.1",
                    "user_agent": request.headers.get("user-agent") or "Unknown",
                    "status": "failure",
                    "detail": f"Login failed: User not found for email '{form_data.username}'"
                }
            )
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        form_data.password,
        user.hashed_password
    ):
        create_audit_event(
            db,
            AuditEventCreate(
                event_type="auth.login_failure",
                entity_type="user",
                entity_id=str(user.id),
                actor_user_id=user.id,
                action="login",
                event_metadata={
                    "ip_address": request.client.host if request.client else "127.0.0.1",
                    "user_agent": request.headers.get("user-agent") or "Unknown",
                    "status": "failure",
                    "detail": "Login failed: Invalid password supplied"
                }
            )
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    # Check if needs password change (excluding ADMIN, AUDITOR, APPROVER roles)
    needs_password_change = False
    is_excluded = False
    for r in user.roles:
        if r.role_code in ["SUPER_ADMIN", "ADMIN", "GOVERNANCE_ADMIN", "GOVERNANCE_MANAGER", "AUDITOR", "APPROVER"]:
            is_excluded = True
            break
            
    if not is_excluded:
        first_name = user.name.split()[0] if user.name else "User"
        first_name_fn = user.full_name.split()[0] if user.full_name else "User"
        email_prefix = user.email.split("@")[0] if user.email else "User"
        
        default_pwd1 = f"{first_name}@1234!"
        default_pwd2 = f"{first_name_fn}@1234!"
        default_pwd3 = f"{email_prefix}@1234!"
        
        if (verify_password(default_pwd1, user.hashed_password) or 
            verify_password(default_pwd2, user.hashed_password) or 
            verify_password(default_pwd3, user.hashed_password) or 
            verify_password("Admin@1234!", user.hashed_password)):
            needs_password_change = True

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "email": user.email
        }
    )

    # Set user context for logging
    set_user_context(str(user.id), user.email)

    create_audit_event(
        db,
        AuditEventCreate(
            event_type="auth.login_success",
            entity_type="user",
            entity_id=str(user.id),
            actor_user_id=user.id,
            action="login",
            event_metadata={
                "ip_address": request.client.host if request.client else "127.0.0.1",
                "user_agent": request.headers.get("user-agent") or "Unknown",
                "status": "success",
                "detail": "Login successful"
            }
        )
    )

    # ── OAuth2 spec: access_token MUST be at root level so Swagger UI ──
    # ── (and any OAuth2 client) can extract it from the response.     ──
    # We also include StandardResponse fields so the frontend client   ──
    # can consume the same response without special-casing.            ──
    from fastapi.encoders import jsonable_encoder
    return JSONResponse(content=jsonable_encoder({
        # OAuth2 / RFC 6749 required fields at root
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        # StandardResponse envelope fields
        "status": "success",
        "message": "Login successful",
        "request_id": get_request_id(),
        "needs_password_change": needs_password_change,
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "needs_password_change": needs_password_change,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "roles": [role.role_code for role in user.roles]
            }
        }
    }))



@router.get("/me", response_model=StandardResponse[dict])
def me(
        current_user: User = Depends(get_current_user)
):
    set_user_context(str(current_user.id), current_user.email)
    
    role_codes = [role.role_code for role in current_user.roles]
    is_superuser = any(rc in ("SUPER_ADMIN", "ADMIN") for rc in role_codes)

    return ResponseHelper.success(
        data={
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "is_superuser": is_superuser,
            "roles": role_codes,
            "permissions": list(set([
                perm.permission_code 
                for role in current_user.roles 
                for perm in role.permissions
            ]))
        },
        message="Current user information retrieved"
    )


@router.post("/refresh", response_model=StandardResponse[TokenResponse])
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email
        }
    )
    
    new_refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "email": user.email
        }
    )

    set_user_context(str(user.id), user.email)

    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )
    
    return ResponseHelper.success(
        data=token_response,
        message="Token refreshed successfully"
    )


@router.post("/logout", response_model=StandardResponse[dict])
def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        exp = payload.get("exp")
        
        # Add to blocklist
        blocklist_entry = TokenBlocklist(token=token, expires_at=exp)
        db.add(blocklist_entry)
        db.commit()
    except JWTError:
        pass
        
    return ResponseHelper.success(
        message="Logged out successfully",
        data=None
    )


@router.post("/change-password", response_model=StandardResponse[dict])
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.core.security import hash_password
    
    if not payload.new_password or len(payload.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters long"
        )
        
    first_name = current_user.name.split()[0] if current_user.name else "User"
    first_name_fn = current_user.full_name.split()[0] if current_user.full_name else "User"
    email_prefix = current_user.email.split("@")[0] if current_user.email else "User"
    
    if payload.new_password in [f"{first_name}@1234!", f"{first_name_fn}@1234!", f"{email_prefix}@1234!", "Admin@1234!"]:
        raise HTTPException(
            status_code=400,
            detail="New password cannot be the same as the default password."
        )
        
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    
    return ResponseHelper.success(
        message="Password updated successfully",
        data={"user_id": current_user.id}
    )


@router.get("/roles", response_model=StandardResponse[List[RoleResponse]])
def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("policy.read"))
):
    set_user_context(str(current_user.id), current_user.email)
    
    roles = db.query(Role).all()
    return ResponseHelper.list_response(
        items=roles,
        message="Roles retrieved successfully"
    )


@router.get("/permissions", response_model=StandardResponse[List[PermissionResponse]])
def get_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("policy.read"))
):
    set_user_context(str(current_user.id), current_user.email)
    
    permissions = db.query(Permission).all()
    return ResponseHelper.list_response(
        items=permissions,
        message="Permissions retrieved successfully"
    )
