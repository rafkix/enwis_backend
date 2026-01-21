from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import VideoShadowingAttempt


class VideoShadowingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, attempt: VideoShadowingAttempt):
        self.db.add(attempt)
        await self.db.flush()
        return attempt

    async def get_by_id(self, attempt_id: int):
        result = await self.db.execute(
            select(VideoShadowingAttempt)
            .where(VideoShadowingAttempt.id == attempt_id)
        )
        return result.scalar_one_or_none()

    async def get_user_attempts(self, user_id: int):
        result = await self.db.execute(
            select(VideoShadowingAttempt)
            .where(VideoShadowingAttempt.user_id == user_id)
            .order_by(VideoShadowingAttempt.created_at.desc())
        )
        return result.scalars().all()

    async def delete(self, attempt: VideoShadowingAttempt):
        await self.db.delete(attempt)
