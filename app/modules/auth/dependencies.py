import logging
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import decode_token
from app.modules.users.models import User

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token: str | None = None

    # 1️⃣ Cookie'dan qidirish
    token = request.cookies.get("access_token")

    # 2️⃣ Header'dan qidirish (Cookie'da bo'lmasa)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    # 3️⃣ Token topilmasa
    if not token:
        # Debug uchun terminalda ko'rish (ixtiyoriy)
        logging.warning("Hech qanday token topilmadi")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # 4️⃣ Tokenni dekod qilish
    try:
        # Muhim: token_type kodingizning qolgan qismiga mos bo'lishi kerak
        user_id = decode_token(token, token_type="access")
    except Exception as e:
        logging.error(f"AUTH ERROR (Decode): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # 5️⃣ Foydalanuvchini bazadan qidirish
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
    except Exception as e:
        logging.error(f"DATABASE ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    if not user:
        logging.warning(f"User topilmadi: ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user