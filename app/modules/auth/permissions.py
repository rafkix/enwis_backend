from fastapi import Depends, HTTPException, status
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User

ADMIN_ROLES = {"admin", "teacher", "mentor"}

def require_auth(user: User = Depends(get_current_user)) -> User:
    """
    Faqat login bo‘lgan user
    """
    return user

def require_roles(*roles: str):
    """
    Masalan:
    Depends(require_roles("admin"))
    Depends(require_roles("admin", "mentor"))
    """

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        return user

    return checker

def require_active_user(
    user: User = Depends(get_current_user)
) -> User:
    if not user.is_active: # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked"
        )
    return user

def require_admin(
    user: User = Depends(get_current_user)
) -> User:
    if user.role != "admin": # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

def require_active_admin(
    user: User = Depends(get_current_user)
) -> User:
    if not user.is_active or user.role != "admin": # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user
