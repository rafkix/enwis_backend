import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_

from app.core.security import hash_password, verify_password
from app.modules.users.models import User
from app.modules.auth.schemas import (
    UserRegister,
    UserTelegramRegister,
    BotStartRequest,
    TelegramLoginRequest,
)
from .models import PhoneVerifyCode


# =========================
# HELPERS
# =========================
def clean_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    return re.sub(r"\D", "", phone)


def generate_code() -> str:
    return str(secrets.randbelow(900000) + 100000)


# =========================
# AUTH SERVICE
# =========================
class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------------------------------
    # REGISTER (EMAIL / PASSWORD)
    # -------------------------------------------------
    async def register(self, data: UserRegister) -> User:
        phone = clean_phone(data.phone)

        conditions = [
            User.username == data.username,
            User.email == data.email,
        ]
        if phone:
            conditions.append(User.phone == phone)

        res = await self.db.execute(select(User).where(or_(*conditions)))
        if res.scalar_one_or_none():
            raise HTTPException(400, "Username, email yoki telefon band")

        user = User(
            full_name=data.full_name,
            username=data.username,
            email=data.email,
            phone=phone,
            password=hash_password(data.password),
            role="student",
            level="beginner",
            is_active=True,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    # -------------------------------------------------
    # LOGIN (USERNAME / EMAIL / PHONE)
    # -------------------------------------------------
    async def login(self, login: str, password: str) -> User:
        phone = clean_phone(login)

        stmt = select(User).where(
            or_(
                User.username == login,
                User.email == login,
                User.phone == phone,
            )
        )
        res = await self.db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user or not verify_password(password, user.password):
            raise HTTPException(400, "Login yoki parol noto‘g‘ri")

        if not user.is_active:
            raise HTTPException(403, "User bloklangan")

        return user

    # -------------------------------------------------
    # TELEGRAM BOT /start
    # -------------------------------------------------
    async def handle_bot_start(self, data: BotStartRequest):
        phone = clean_phone(data.phone)
        if not phone:
            raise HTTPException(status_code=400, detail="Telefon raqam majburiy")

        telegram_id = int(data.telegram_id)
        code = generate_code()

        # 1️⃣ Eski kodlarni yopish
        await self.db.execute(
            update(PhoneVerifyCode)
            .where(PhoneVerifyCode.phone == phone, PhoneVerifyCode.is_used == False)
            .values(is_used=True)
        )

        # 2️⃣ Userni topish
        res = await self.db.execute(select(User).where(User.phone == phone))
        user = res.scalar_one_or_none()

        # 3️⃣ Yangi verify code (Timezone tuzatildi)
        verify = PhoneVerifyCode(
            phone=phone,
            code=code,
            telegram_id=telegram_id,
            full_name=data.full_name,
            user_id=user.id if user else None,
            is_used=False,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        self.db.add(verify)

        # 4️⃣ User bo'lsa bog'lash
        if user and user.telegram_id != telegram_id:
            user.telegram_id = telegram_id

        await self.db.commit()
        return {"status": "ok", "is_new_user": user is None, "code": code}

    async def verify_phone_code(self, data: TelegramLoginRequest):
        phone = clean_phone(data.phone)
        code = data.code

        result = await self.db.execute(
            select(PhoneVerifyCode)
            .where(
                PhoneVerifyCode.phone == phone,
                PhoneVerifyCode.code == code,
                PhoneVerifyCode.is_used == False
            )
            .order_by(PhoneVerifyCode.id.desc())
        )
        verify = result.scalar_one_or_none()

        if not verify:
            raise HTTPException(400, detail="Kod noto‘g‘ri yoki ishlatilgan")

        # ✅ TIME CHECK tuzatildi (Timezone-aware comparison)
        current_time = datetime.now(timezone.utc)
        if verify.expires_at.replace(tzinfo=timezone.utc) < current_time:
            raise HTTPException(400, detail="Tasdiqlash kodi muddati tugagan")

        # Userni tekshirish (Yangi user bo'lsa bu yerda to'xtaydi)
        if not verify.user_id:
            # Bu joyda registratsiya sahifasiga yuborish kerak bo'ladi
            raise HTTPException(status_code=404, detail="Foydalanuvchi ro'yxatdan o'tmagan")

        user = await self.db.get(User, verify.user_id)
        if not user:
            raise HTTPException(404, detail="Foydalanuvchi topilmadi")

        # Hammasi yaxshi bo'lsa, keyin kodni ishlatildi deb belgilaymiz
        verify.is_used = True
        await self.db.commit()
        return user


    # -------------------------------------------------
    # TELEGRAM REGISTER
    # -------------------------------------------------
    async def telegram_register(self, data: UserTelegramRegister) -> User:
        phone = clean_phone(data.phone)

        res = await self.db.execute(
            select(User).where(
                or_(
                    User.phone == phone,
                    User.telegram_id == data.telegram_id,
                )
            )
        )
        user = res.scalar_one_or_none()

        if user:
            if user.telegram_id:
                raise HTTPException(400, "Telegram allaqachon bog‘langan")
            user.telegram_id = data.telegram_id
            await self.db.commit()
            await self.db.refresh(user)
            return user

        if not data.password:
            raise HTTPException(400, "Parol majburiy")

        res = await self.db.execute(
            select(User).where(
                or_(
                    User.username == data.username,
                    User.email == data.email,
                )
            )
        )
        if res.scalar_one_or_none():
            raise HTTPException(400, "Username yoki email band")

        user = User(
            full_name=data.full_name,
            username=data.username,
            email=data.email,
            phone=phone,
            telegram_id=data.telegram_id,
            password=hash_password(data.password),
            role="student",
            level="beginner",
            is_active=True,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user