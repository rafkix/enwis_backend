from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User

from .schemas import (
    VideoShadowingCreate,
    VideoShadowingUpdate,
    VideoShadowingResponse,
)
from .repository import VideoShadowingRepository
from .service import VideoShadowingService

router = APIRouter(
    prefix="/services/video-shadowing",
    tags=["Video Shadowing"]
)

@router.get("/me", response_model=list[VideoShadowingResponse])
async def my_attempts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = VideoShadowingService(VideoShadowingRepository(db))
    return await service.list_user_attempts(user.id) # type: ignore


@router.get("/select/{attempt_id}", response_model=VideoShadowingResponse)
async def get_attempt(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = VideoShadowingService(VideoShadowingRepository(db))
    return await service.get(attempt_id, user.id) # type: ignore

@router.post("/create", response_model=VideoShadowingResponse)
async def create_attempt(
    data: VideoShadowingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = VideoShadowingService(VideoShadowingRepository(db))
    attempt = await service.create(user.id, data) # type: ignore

    await db.commit()
    await db.refresh(attempt)
    return attempt


@router.put("/update/{attempt_id}", response_model=VideoShadowingResponse)
async def update_attempt(
    attempt_id: int,
    data: VideoShadowingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = VideoShadowingService(VideoShadowingRepository(db))
    attempt = await service.update(attempt_id, user.id, data) # type: ignore

    await db.commit()
    await db.refresh(attempt)
    return attempt


@router.delete("/delete/{attempt_id}")
async def delete_attempt(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = VideoShadowingService(VideoShadowingRepository(db))
    await service.delete(attempt_id, user.id) # type: ignore

    await db.commit()
    return {"message": "Deleted successfully"}
