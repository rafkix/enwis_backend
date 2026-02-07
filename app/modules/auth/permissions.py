from fastapi import Depends, HTTPException, status
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User


# --------------------------------------------------
# 1. ODDIY LOGIN BO‘LGAN USER
# --------------------------------------------------
def require_user(
    user: User = Depends(get_current_user),
) -> User:
    return user


# --------------------------------------------------
# 2. FAOL USER
# --------------------------------------------------
def require_active_user(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    return user


# --------------------------------------------------
# 3. ROLE TEKSHIRISH (UNIVERSAL)
# --------------------------------------------------
def require_roles(
    *roles: str,
    active_only: bool = True,
):
    """
    Examples:
    Depends(require_roles("admin"))
    Depends(require_roles("admin", "mentor"))
    Depends(require_roles("admin", active_only=False))
    """

    def checker(
        user: User = Depends(get_current_user),
    ) -> User:
        if active_only and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive"
            )

        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )

        return user

    return checker


# --------------------------------------------------
# 4. FAQAT ADMIN
# --------------------------------------------------
def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_active: # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )

    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return user
