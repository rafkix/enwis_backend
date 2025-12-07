from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user_model import User
from app.routers.auth_router import get_current_user
from app.utils.hashing import password_hash, verify_password
from app.schemas.user_schema import UserUpdate, PasswordChange, UserResponse
import os
from datetime import datetime

router = APIRouter(prefix="/users", tags=["Users"])


# 🧩 1. Profilni olish
@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


# 🧩 2. Profilni yangilash (Pydantic orqali)
@router.put("/update", response_model=UserResponse)
async def update_profile(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Faqat kelgan maydonlarni yangilash
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.bio is not None:
        user.bio = payload.bio
    if payload.level is not None:
        user.level = payload.level

    # 🔥 Yodda saqlanadigan joy — ORM orqali update
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user

# 🧩 3. Parolni o‘zgartirish
@router.put("/change_password")
async def change_password(
    data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(data.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    current_user.password = password_hash(data.new_password)
    await db.commit()
    await db.refresh(current_user)

    return {"message": "Password updated successfully"}


@router.post("/upload_avatar")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uploads_dir = "static/avatars"
    os.makedirs(uploads_dir, exist_ok=True)

    filename = f"{current_user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    file_path = os.path.join(uploads_dir, filename)

    # Write file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # ❗ DBga faqat filename yoziladi
    current_user.profile_image = filename

    await db.commit()
    await db.refresh(current_user)

    # ❗ Frontga to‘liq URL qaytariladi
    image_url = f"{request.base_url}static/avatars/{filename}"

    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "username": current_user.username,
        "email": current_user.email,
        "phone": current_user.phone,
        "level": current_user.level,
        "bio": current_user.bio,
        "profile_image": image_url,  # frontendda ishlaydi
        "role": current_user.role,
        "created_at": current_user.created_at,
    }


@router.delete("/delete_me")
async def delete_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()

    return {"message": "User deleted successfully"}

@router.delete("/delere_user/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["admin", "mentor", "teacher"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}
