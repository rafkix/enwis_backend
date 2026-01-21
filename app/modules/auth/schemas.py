from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# --- REGISTRATION MODELS ---

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=100)
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    age: Optional[int] = Field(None, ge=10, le=100)
    level: Optional[str] = "beginner"
    role: Optional[str] = "student"

class UserTelegramRegister(BaseModel):
    # Bu model foydalanuvchi botdan kod olib kelib, 
    # birinchi marta ro'yxatdan o'tayotganida ishlatiladi
    phone: str
    full_name: str
    username: str
    password: str
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    level: Optional[str] = "beginner"
    role: Optional[str] = "student"
    telegram_id: int

# --- AUTH & BOT REQUESTS ---

class BotStartRequest(BaseModel):
    phone: str
    telegram_id: str
    full_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class TelegramLoginRequest(BaseModel):
    phone: str
    code: str

# --- RESPONSE MODELS ---

# Saytdan telefon raqamini kiritib, botga link so'ralganda ishlatiladi
class PhoneRequestSchema(BaseModel):
    phone: str

# Saytda botdan olingan kodni kiritib, tasdiqlashda ishlatiladi
class PhoneVerifySchema(BaseModel):
    phone: str
    code: str

class UserProfileResponse(BaseModel):
    """Foydalanuvchi ma'lumotlarini qaytarish uchun xavfsiz sxema"""
    id: int
    full_name: str
    username: str
    email: Optional[str] = None
    phone: str
    role: str
    telegram_id: Optional[str] = None

    class Config:
        from_attributes = True # SQLAlchemy modelidan o'qiy olish uchun

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # Frontendga foydalanuvchini darhol tanitish uchun 'user' obyektini qaytaramiz
    user: Optional[UserProfileResponse] = None