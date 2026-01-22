import logging
import random
import re
from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.modules.auth.schemas import BotStartRequest, UserTelegramRegister
from app.modules.users.models import User
from app.core.hashing import password_hash, verify_password
from app.modules.auth.tokens import create_user_token
from .models import PhoneVerifyCode

# --- YORDAMCHI FUNKSIYALAR ---
def clean_phone_number(phone: str) -> str:
    """Telefon raqamidan faqat raqamlarni ajratib oladi."""
    return re.sub(r'\D', '', str(phone))

def clean_tg_id(tg_id: Any) -> int:
    """Telegram ID raqamidan bo'shliqlarni tozalab, Integerga (BigInt) o'giradi."""
    if tg_id is None:
        return None
    cleaned = re.sub(r'\D', '', str(tg_id))
    return int(cleaned) if cleaned else None

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # 1. STANDART RO'YXATDAN O'TISH (SAYT ORQALI)
    async def register(self, data) -> Tuple[User, str]:
        cleaned_phone = clean_phone_number(data.phone)
        
        query = select(User).where(
            (User.username == data.username) | 
            (User.email == data.email) | 
            (User.phone == cleaned_phone)
        )
        result = await self.db.execute(query)
        existing_user = result.scalars().first()

        if existing_user:
            if existing_user.username == data.username:
                raise HTTPException(status_code=400, detail="Bu username band.")
            if existing_user.email == data.email:
                raise HTTPException(status_code=400, detail="Bu email band.")
            if existing_user.phone == cleaned_phone:
                raise HTTPException(status_code=400, detail="Bu telefon band.")

        user = User(
            full_name=data.full_name,
            username=data.username,
            email=data.email,
            phone=cleaned_phone,
            age=data.age,
            level=data.level,
            role=data.role,
            password=password_hash(data.password),
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        token = create_user_token(user)
        return user, token

    # 2. TELEGRAM ORQALI RO'YXATDAN O'TISH (BOTDAN KELADIGAN SO'ROV)
    async def register_with_telegram_verify(self, data: UserTelegramRegister) -> Tuple[User, str]:
        # Sxemadagi ma'lumotlarni User modeliga o'tkazish
        user = User(
            full_name=data.full_name,
            username=data.username,
            email=data.email,
            phone=re.sub(r'\D', '', data.phone),
            password=password_hash(data.password),
            telegram_id=data.telegram_id,
            age=data.age,
            level=data.level,
            role="student"
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user, create_user_token(user)

    # 3. BOT START (KOD GENERATSIYASI VA SAQLASH)
    async def handle_bot_start(self, data: BotStartRequest):
        clean_phone = re.sub(r'\D', '', data.phone)
        new_code = str(random.randint(100000, 999999))
        
        # Eski kodlarni o'chirish
        await self.db.execute(update(PhoneVerifyCode).where(PhoneVerifyCode.phone == clean_phone).values(is_used=True))
        
        user_res = await self.db.execute(select(User).where(User.phone == clean_phone))
        user = user_res.scalars().first()

        verify_record = PhoneVerifyCode(
            phone=clean_phone,
            code=new_code,
            telegram_id=data.telegram_id,
            full_name=data.full_name,
            user_id=user.id if user else None,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        self.db.add(verify_record)
        await self.db.commit()
        return {"code": new_code, "status": "success"}
    

    # 4. KODNI TASDIQLASH (SAYTDA KIRISH UCHUN)
    async def verify_phone_code(self, phone: str, code: str) -> Dict[str, Any]:
        clean_phone = clean_phone_number(phone)
        
        stmt = select(PhoneVerifyCode).where(
            PhoneVerifyCode.phone == clean_phone,
            PhoneVerifyCode.code == str(code), 
            PhoneVerifyCode.is_used == False
        ).order_by(PhoneVerifyCode.created_at.desc())
        
        result = await self.db.execute(stmt)
        verify = result.scalar_one_or_none()

        if not verify:
            raise HTTPException(status_code=400, detail="Kod noto‘g‘ri yoki allaqachon ishlatilgan")

        # Vaqtni tekshirish
        current_time = datetime.now(timezone.utc)
        expires_at = verify.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < current_time:
            raise HTTPException(status_code=400, detail="Kodning muddati tugagan")

        # Userni qidirish
        user_stmt = select(User).where(User.phone == clean_phone)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi. Avval botda ro'yxatdan o'ting.")

        # Ma'lumotlarni yangilash
        user.telegram_id = verify.telegram_id
        if verify.full_name:
            user.full_name = verify.full_name
            
        verify.is_used = True
        
        await self.db.commit()
        await self.db.refresh(user)

        token = create_user_token(user)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }

    # 5. STANDART LOGIN
    async def login(self, username: str, password: str) -> Tuple[User, str]:
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalars().first()

        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=400, detail="Username yoki parol noto'g'ri")

        token = create_user_token(user)
        return user, token