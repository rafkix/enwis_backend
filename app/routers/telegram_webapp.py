from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user_model import User
from app.schemas.auth_schema import TelegramAuthSchema
from app.utils.telegram import decode_telegram_payload, verify_telegram_auth
from app.utils.jwt_handler import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/telegram")
async def telegram_auth(
    payload: TelegramAuthSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        data = decode_telegram_payload(payload.tgAuthResult)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Telegram payload")

    if not verify_telegram_auth(data.copy()):
        raise HTTPException(status_code=401, detail="Telegram authentication failed")

    telegram_id = str(data["id"])
    username = data.get("username")
    full_name = data.get("first_name")
    photo = data.get("photo_url")

    # 🔍 USER BOR-MI?
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalars().first()

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            profile_image=photo,
            auth_provider="telegram"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token({"user_id": user.id})

    return {
        "access_token": token,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "full_name": user.full_name,
            "photo": user.profile_image
        }
    }
