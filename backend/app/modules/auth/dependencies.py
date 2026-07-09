from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.auth.models import User


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        raise credentials_exception

    from app.modules.auth.models import TokenBlocklist
    is_blocked = db.query(TokenBlocklist).filter(TokenBlocklist.token == token).first()
    if is_blocked:
        raise HTTPException(
            status_code=401,
            detail="Token has been revoked"
        )

    from app.core.middleware import set_user_context
    set_user_context(str(user.id), user.email)
    return user


def require_permission(permission_code: str):
    def permission_dependency(current_user: User = Depends(get_current_user)):
        for role in current_user.roles:
            for permission in role.permissions:
                if permission.permission_code == permission_code:
                    return current_user
        raise HTTPException(
            status_code=403,
            detail=f"Not enough permissions. Requires: {permission_code}"
        )
    return permission_dependency