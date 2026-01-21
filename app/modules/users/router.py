from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.education.tasks.models import Task, UserTask
from app.modules.auth.dependencies import get_current_user
from app.modules.education.tasks.schemas import UserTaskOut
from app.modules.users.models import User
from app.modules.auth.permissions import require_active_user
from app.modules.users.schemas import UserUpdate, PasswordChange, UserResponse
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/get_me", response_model=UserResponse)
async def me(
    current_user: User = Depends(require_active_user),
):
    return current_user

@router.get("/user/my", response_model=list[UserTaskOut])
async def my_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(
        select(UserTask).where(UserTask.user_id == current_user.id)
    )
    return res.scalars().all()


@router.post("/update/profile/photo", response_model=UserResponse)
async def upload_profile_photo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_active_user),
):
    if file.content_type not in ("image/png", "image/jpeg"):
        raise HTTPException(status_code=400, detail="Invalid image format")

    repo = UserRepository(db)
    service = UserService(repo)

    photo_path = await service.save_profile_photo(current_user, file) # type: ignore
    current_user.profile_photo = photo_path

    await db.commit()
    await db.refresh(current_user)

    return current_user

@router.put("/update/profiel", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_active_user),
):
    repo = UserRepository(db)
    service = UserService(repo)

    await service.update_profile(current_user, data)
    await db.commit()
    await db.refresh(current_user)

    return current_user

@router.put("/update/change_password")
async def change_password(
    data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_active_user),
):
    repo = UserRepository(db)
    service = UserService(repo)

    try:
        await service.change_password(current_user, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()
    return {"message": "Password updated successfully"}


@router.delete("/delete/me")
async def delete_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_active_user),
):
    repo = UserRepository(db)
    service = UserService(repo)

    await service.delete_self(current_user)
    await db.commit()

    return {"message": "Account deleted"}
