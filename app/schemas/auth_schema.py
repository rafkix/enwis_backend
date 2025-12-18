from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    level: Optional[str] = "beginner"
    role: Optional[str] = "student"
    bio: Optional[str] = ""
    profile_image: Optional[str] = "default.jpg"

    google_id: Optional[str] = None
    telegram_id: Optional[str] = None
    auth_provider: Optional[str] = "local"

class UserRegister(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    phone: Optional[str] = None
    age: Optional[int] = None
    level: Optional[str] = "beginner"
    role: Optional[str] = "student"
    password: str

class InitDataSchema(BaseModel):
    init_data: str


class UserCreate(UserBase):
    password: Optional[str] = None


class TelegramRegisterSchema(BaseModel):
    full_name: str
    username: str
    telegram_id: str
    bio: str | None = ""
    profile_image: str | None = "default.png"

class TelegramAuthSchema(BaseModel):
    tgAuthResult: str

class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True