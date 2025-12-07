import hmac
import hashlib
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user_model import User
from app.schemas.auth_schema import TelegramRegisterSchema
from app.utils.jwt_handler import create_access_token
from app.utils.hashing import password_hash
from app import config

router = APIRouter(prefix="/auth", tags=["Authentication"])

def check_telegram_auth(data: dict) -> bool:
    """
    Telegram Login Widget HMAC tekshiruvi
    """

    bot_token = config.TELEGRAM_BOT_TOKEN.encode()
    secret_key = hashlib.sha256(bot_token).digest()

    check_hash = data.pop("hash")
    data_list = [f"{k}={v}" for k, v in sorted(data.items())]
    data_string = "\n".join(data_list)

    h = hmac.new(secret_key, data_string.encode(), hashlib.sha256).hexdigest()

    return h == check_hash


@router.post("/telegram_register")
async def telegram_register(payload: TelegramRegisterSchema, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump()

    if not check_telegram_auth(data.copy()):
        raise HTTPException(status_code=401, detail="Invalid Telegram authentication")

    # Username bor-yo‘qligi
    existing = await db.execute(select(User).where(User.username == payload.username))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = password_hash("telegram_default_password")

    new_user = User(
        full_name=payload.full_name,
        username=payload.username,
        telegram_id=payload.telegram_id,
        profile_image=payload.profile_image,
        bio=payload.bio,
        password=hashed_pw,
        auth_provider="telegram"
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token({"user_id": new_user.id})

    return {
        "message": "Telegram registration successful",
        "access_token": token,
        "user": payload
    }
    