from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    level: Optional[str] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: Optional[EmailStr]
    phone: Optional[str]
    level: Optional[str]
    role: Optional[str]
    bio: Optional[str]
    profile_image: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
