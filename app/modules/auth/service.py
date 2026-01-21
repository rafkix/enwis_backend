from datetime import datetime, timedelta, timezone
import random
import re
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

# Yordamchi funksiya
def clean_phone_number(phone: str) -> str:
    return re.sub(r'\D', '', str(phone))

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # 1. STANDART RO'YXATDAN O'TISH
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
                raise HTTPException(status_code=400, detail="Bu email allaqachon ro'yxatdan o'tgan.")
            if existing_user.phone == cleaned_phone:
                raise HTTPException(status_code=400, detail="Bu telefon raqam allaqachon mavjud.")

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

    # 2. TELEGRAM ORQALI RO'YXATDAN O'TISH
    async def register_with_telegram_verify(self, data: UserTelegramRegister) -> Tuple[User, str]:
        cleaned_phone = clean_phone_number(data.phone)
        
        # --- O'ZGARTIRISH: Kodni tekshirish qismini olib tashlaymiz yoki soddalashtiramiz ---
        # Chunki bot registratsiya so'rovini yuborganida kod hali yaratilmagan bo'ladi.
        # Faqat foydalanuvchi mavjudligini tekshiramiz.

        user_check = await self.db.execute(
            select(User).where(
                (User.username == data.username) | 
                (User.phone == cleaned_phone)
            )
        )
        if user_check.scalars().first():
            raise HTTPException(status_code=400, detail="Username yoki telefon band.")

        # Yangi foydalanuvchi yaratish
        # telegram_id ni to'g'ridan-to'g'ri 'data'dan olamiz
        user = User(
            full_name=data.full_name,
            username=data.username,
            email=data.email,
            phone=cleaned_phone,
            age=data.age,
            level=data.level,
            role="student",
            telegram_id=str(data.telegram_id), # Sxemadagi telegram_id ni ishlatamiz
            password=password_hash(data.password),
        )

        self.db.add(user)
        
        # Agar PhoneVerifyCode jadvalida ushbu raqam uchun eski kodlar bo'lsa, ularni tozalash
        await self.db.execute(
            update(PhoneVerifyCode)
            .where(PhoneVerifyCode.phone == cleaned_phone)
            .values(is_used=True)
        )

        await self.db.commit()
        await self.db.refresh(user)

        token = create_user_token(user)
        return user, token
    
    # 3. STANDART LOGIN
    async def login(self, username: str, password: str) -> Tuple[User, str]:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalars().first()

        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username yoki parol xato")

        token = create_user_token(user)
        return user, token

    async def handle_bot_start(self, data: BotStartRequest) -> Dict[str, Any]:
        # 1. Kirib kelgan raqamni tozalaymiz
        input_phone = clean_phone_number(data.phone)
        
        # 2. Foydalanuvchini FAQAT telefon raqami orqali qidiramiz
        user_res = await self.db.execute(
            select(User).where(User.phone == input_phone)
        )
        user = user_res.scalars().first()

        # 3. Kod generatsiya qilish
        # Foydalanuvchi bazada bormi yoki yo'qmi, baribir kod yaratamiz 
        # (chunki u yangi bo'lsa, ro'yxatdan o'tgandan keyin shu kod kerak bo'ladi)
        new_code = str(random.randint(100000, 999999))
        expires = datetime.now(timezone.utc) + timedelta(minutes=5)

        # 4. Eski ishlatilmagan kodlarni yopamiz
        await self.db.execute(
            update(PhoneVerifyCode)
            .where(PhoneVerifyCode.phone == input_phone, PhoneVerifyCode.is_used == False)
            .values(is_used=True)
        )

        # 5. Yangi kodni bazaga saqlaymiz
        new_record = PhoneVerifyCode(
            phone=input_phone,
            code=new_code,
            telegram_id=str(data.telegram_id),
            full_name=data.full_name,
            expires_at=expires,
            is_used=False
        )
        self.db.add(new_record)
        
        # 6. Agar foydalanuvchi topilsa, uning telegram_id sini yangilab qo'yamiz
        if user:
            user.telegram_id = str(data.telegram_id)

        await self.db.commit()

        return {
            "status": "success",
            "is_new_user": user is None, 
            "code": new_code,
            "phone": input_phone
        }
        
        
    async def verify_phone_code(self, phone: str, code: str) -> Dict[str, Any]:
        # 1. Raqamni tozalash (Frontenddan + belgilari bilan kelishi mumkin)
        clean_phone = clean_phone_number(phone)
        
        # Debug uchun log (Terminalda ko'rish uchun)
        print(f"DEBUG: Verify request - Phone: {clean_phone}, Code: {code}")

        # 2. Kodni bazadan qidirish
        # MUHIM: str(code) qiling, ba'zan frontenddan int bo'lib kelishi mumkin
        stmt = select(PhoneVerifyCode).where(
            PhoneVerifyCode.phone == clean_phone,
            PhoneVerifyCode.code == str(code), 
            PhoneVerifyCode.is_used == False
        )
        result = await self.db.execute(stmt)
        verify = result.scalar_one_or_none()

        # 3. Agar kod topilmasa
        if not verify:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Kod noto‘g‘ri yoki allaqachon ishlatilgan"
            )

        # 4. Vaqtni tekshirish (Timezone muammosini hal qilish)
        # Bazadagi vaqtni UTC ga o'tkazib solishtiramiz
        current_time = datetime.now(timezone.utc)
        expires_at = verify.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < current_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Kodning amal qilish muddati tugagan"
            )

        # 5. Userni qidirish
        user_stmt = select(User).where(User.phone == clean_phone)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Foydalanuvchi topilmadi. Avval ro'yxatdan o'ting."
            )

        # 6. Ma'lumotlarni yangilash va kodni yopish
        user.telegram_id = str(verify.telegram_id)
        if verify.full_name and (not user.full_name or user.full_name == "Web User"):
            user.full_name = verify.full_name
            
        verify.is_used = True
        
        # 7. Saqlash
        await self.db.commit()
        await self.db.refresh(user)

        # 8. Token yaratish
        token = create_user_token(user)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }