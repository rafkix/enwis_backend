from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# 🧩 Profilni yangilash
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    level: Optional[str] = None


# 🧩 Parolni o‘zgartirish
class PasswordChange(BaseModel):
    old_password: str
    new_password: str


# 🧩 Foydalanuvchini qaytarish uchun (response)
class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: Optional[EmailStr]
    phone: Optional[str]
    age: Optional[int]
    level: Optional[str]
    role: Optional[str]
    bio: Optional[str]
    profile_image: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
