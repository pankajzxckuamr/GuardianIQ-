from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.models import User, Role, Permission
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token
)
from app.core.config import settings
from jose import jwt, JWTError
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.auth.schemas import TokenResponse, RefreshTokenRequest, RoleResponse, PermissionResponse
from app.shared.responses import StandardResponse
from app.shared.response_utils import ResponseHelper
from app.core.middleware import get_request_id, set_user_context
from typing import List, Any

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"]
)


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

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

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=StandardResponse[dict])
def me(
        current_user: User = Depends(get_current_user)
):
    set_user_context(str(current_user.id), current_user.email)
    
    return ResponseHelper.success(
        data={
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "roles": [
                role.role_code for role in current_user.roles
            ],
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
def logout():
    # Since we are using stateless JWTs, we tell the client to remove the token.
    # A true server-side logout would require a token blocklist in DB/Redis.
    return ResponseHelper.success(
        message="Logged out successfully",
        data=None
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
