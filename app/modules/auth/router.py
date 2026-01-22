import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import (
    BotStartRequest,
    PhoneRequestSchema, 
    TokenResponse,
    TelegramLoginRequest,
    UserRegister,
    UserTelegramRegister
)
from app.modules.users.models import User
from app.modules.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

# --- 1. STANDART RO'YXATDAN O'TISH ---
@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Standart email va parol orqali ro'yxatdan o'tish"""
    service = AuthService(db)
    user, token = await service.register(data)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }   

# --- 2. TELEGRAM ORQALI RO'YXATDAN O'TISH (BOTDAN KELADIGAN SO'ROV) ---
@router.post("/register/telegram", response_model=TokenResponse)
async def register_telegram(data: UserTelegramRegister, db: AsyncSession = Depends(get_db)):
    """
    Bot orqali ro'yxatdan o'tish so'rovi yuborilganda ishlaydi.
    TokenResponse qaytaradi, shunda bot registratsiyadan so'ng foydalanuvchiga kod bera oladi.
    """
    try:
        service = AuthService(db)
        user, token = await service.register_with_telegram_verify(data)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Telegram Register API Error: {str(e)}")
        # Takroriy ma'lumot xatolarini ushlash
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Username, Email yoki Telefon raqam allaqachon band."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Ro'yxatdan o'tishda ichki xatolik yuz berdi."
        )

# --- 3. STANDART LOGIN (USERNAME/PASSWORD) ---
@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Username va parol orqali saytga kirish"""
    service = AuthService(db)
    user, token = await service.login(form.username, form.password)
    return {
        "access_token": token, 
        "token_type": "bearer",
        "user": user
    }

# --- 4. TELEGRAM ORQALI LOGIN / VERIFY (SAYT UCHUN) ---
@router.post("/phone/verify", response_model=TokenResponse)
@router.post("/login/telegram", response_model=TokenResponse)
async def login_telegram_verify(data: TelegramLoginRequest, db: AsyncSession = Depends(get_db)):
    """Foydalanuvchi saytda telefon va botdan olgan kodini kiritganda ishlaydi."""
    try:
        service = AuthService(db)
        return await service.verify_phone_code(data.phone, data.code)
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Telegram Verify Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Kod tasdiqlashda tizim xatosi yuz berdi."
        )

# --- 5. BOT UCHUN ENDPOINT (BOT START) ---
@router.post("/bot/start")
async def bot_start_api(data: BotStartRequest, db: AsyncSession = Depends(get_db)):
    """Botda /start bosilganda yangi kod generatsiya qilish va qaytarish"""
    try:
        service = AuthService(db)
        return await service.handle_bot_start(data)
    except Exception as e:
        logging.error(f"Bot Start API Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Bot start jarayonida xatolik."
        )

# --- 6. TELEGRAM LINK GENERATSIYASI (SAYT UCHUN) ---
@router.post("/phone/request")
async def request_phone_code(data: PhoneRequestSchema):
    """Saytda raqam kiritilganda botga yo'naltiruvchi deep-link beradi"""
    # Raqamdan faqat raqamlarni qoldiramiz
    clean_phone = "".join(filter(str.isdigit, data.phone))
    return {
        "telegram_url": f"https://t.me/enwis_bot?start={clean_phone}"
    }

# --- 7. PROFIL MA'LUMOTLARINI OLISH ---
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Hozirgi tizimga kirgan foydalanuvchi profilini qaytaradi"""
    return current_user

# --- 8. LOGOUT ---
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Tizimdan chiqish (Sessiyani yakunlash)"""
    return {"message": "Tizimdan muvaffaqiyatli chiqildi."}