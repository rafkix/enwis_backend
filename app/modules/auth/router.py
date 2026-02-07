import logging
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Response,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import (
    AuthResponse,
    BotStartRequest,
    PhoneRequestSchema,
    TelegramLoginRequest,
    UserRegister,
    UserTelegramRegister,
)
from app.modules.users.models import User
from app.modules.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

# --- SOZLAMALAR ---
# Muammoni hal qilish uchun COOKIE_NAME ni dependencies.py bilan bir xil qiling
COOKIE_NAME = "access_token" 
COOKIE_DOMAIN = None          
COOKIE_MAX_AGE = 60 * 60 * 24 
COOKIE_SECURE = False         # Lokal muhitda False bo'lishi shart

def set_auth_cookie(response: Response, token: str):
    """
    Cookie'ni brauzerga yuborish. 
    Agar frontend va backend boshqa portlarda bo'lsa (masalan :3000 va :8000), 
    samesite="lax" ba'zan muammo berishi mumkin.
    """
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        domain=COOKIE_DOMAIN,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",       # Localhost uchun 'lax' eng ma'quli
        max_age=COOKIE_MAX_AGE,
    )

@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(response: Response, data: UserRegister, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.register(data)
    token = create_access_token(user.id)
    set_auth_cookie(response, token)
    return {"user": user, "access_token": token}

@router.post("/register/telegram", response_model=AuthResponse, status_code=201)
async def register_telegram(response: Response, data: UserTelegramRegister, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.telegram_register(data)
    token = create_access_token(user.id)
    set_auth_cookie(response, token)
    return {"user": user, "access_token": token}

@router.post("/login", response_model=AuthResponse)
async def login(response: Response, form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.login(form.username, form.password)
    token = create_access_token(user.id)
    set_auth_cookie(response, token)
    return {"user": user, "access_token": token}

@router.post("/phone/verify", response_model=AuthResponse)
async def phone_verify(response: Response, data: TelegramLoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.verify_phone_code(data)
    token = create_access_token(user.id)
    set_auth_cookie(response, token)
    return {"user": user, "access_token": token}

@router.post("/bot/start")
async def bot_start(data: BotStartRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.handle_bot_start(data)

@router.post("/phone/request")
async def request_phone_code(data: PhoneRequestSchema):
    clean_phone = "".join(filter(str.isdigit, data.phone))
    return {"telegram_url": f"https://t.me/enwis_bot?start={clean_phone}"}

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, domain=COOKIE_DOMAIN)
    return {"message": "Logged out successfully"}