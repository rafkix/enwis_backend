from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import (
    BotStartRequest, 
    PhoneRequestSchema, 
    PhoneVerifySchema, 
    TokenResponse, 
    UserRegister, 
    TelegramLoginRequest,
    UserTelegramRegister
)
from app.modules.users.models import User
from app.modules.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

# --- 1. STANDART RO'YXATDAN O'TISH ---
@router.post("/register", response_model=TokenResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    # Servisdagi register funksiyasi (user, token) qaytaradi
    user, token = await service.register(data)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }   

# --- 2. TELEGRAM ORQALI RO'YXATDAN O'TISH (OXIRIDA KOD BILAN) ---
@router.post("/register/telegram", response_model=TokenResponse)
async def register_telegram(data: UserTelegramRegister, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    # Servisdagi register_with_telegram_verify metodini chaqiramiz
    user, token = await service.register_with_telegram_verify(data)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

# --- 3. STANDART LOGIN (USERNAME/PASSWORD) ---
@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user, token = await service.login(form.username, form.password)
    return {
        "access_token": token, 
        "token_type": "bearer",
        "user": user
    }

# --- 6. TELEGRAM LINK GENERATSIYASI ---
@router.post("/phone/request")
async def request_phone_code(data: PhoneRequestSchema):
    # Raqamni faqat raqamlardan iborat qilib tozalaymiz
    clean_phone = "".join(filter(str.isdigit, data.phone))
    return {
        "telegram_url": f"https://t.me/enwis_bot?start={clean_phone}"
    }

# --- 4. TELEGRAM ORQALI LOGIN (KOD BILAN) ---
@router.post("/phone/verify", response_model=TokenResponse)
@router.post("/login/telegram", response_model=TokenResponse)
async def login_telegram(data: TelegramLoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    # verify_phone_code metodi access_token va user obyektini qaytaradi
    return await service.verify_phone_code(data.phone, data.code)

# --- 5. BOT UCHUN ENDPOINT (BOT START) ---
@router.post("/bot/start")
async def bot_start_api(data: BotStartRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.handle_bot_start(data)



# --- 7. PROFIL MA'LUMOTLARINI OLISH ---
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# --- 8. LOGOUT ---
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}