from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User

from .schemas import (
    AudioWritingCreate,
    AudioWritingUpdate,
    AudioWritingResponse,
)
from .repository import AudioWritingRepository
from .service import AudioWritingService

router = APIRouter(prefix="/services/audio-writing", tags=["Audio Writing"])


@router.get("/me", response_model=list[AudioWritingResponse])
async def my_attempts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AudioWritingService(AudioWritingRepository(db))
    return await service.list_user_attempts(user.id) # type: ignore


@router.get("/select/{attempt_id}", response_model=AudioWritingResponse)
async def get_attempt(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AudioWritingService(AudioWritingRepository(db))
    return await service.get(attempt_id, user.id) # type: ignore

@router.post("/create", response_model=AudioWritingResponse)
async def create_attempt(
    data: AudioWritingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AudioWritingService(AudioWritingRepository(db))
    attempt = await service.create(user.id, data) # type: ignore

    await db.commit()
    await db.refresh(attempt)
    return attempt

@router.put("/update/{attempt_id}", response_model=AudioWritingResponse)
async def update_attempt(
    attempt_id: int,
    data: AudioWritingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AudioWritingService(AudioWritingRepository(db))
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
    service = AudioWritingService(AudioWritingRepository(db))
    await service.delete(attempt_id, user.id) # type: ignore

    await db.commit()
    return {"message": "Deleted successfully"}
