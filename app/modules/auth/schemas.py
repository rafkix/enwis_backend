from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# --- REGISTRATION ---
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
    phone: str
    full_name: str
    username: str
    password: str
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    level: Optional[str] = "beginner"
    role: Optional[str] = "student"
    telegram_id: int

# --- REQUESTS ---
class BotStartRequest(BaseModel):
    phone: str
    telegram_id: int
    full_name: str

class TelegramLoginRequest(BaseModel):
    phone: str
    code: str

class PhoneRequestSchema(BaseModel):
    phone: str

# --- RESPONSES ---
class UserProfileResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: Optional[str] = None
    phone: str
    role: str
    telegram_id: Optional[int] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserProfileResponse] = None