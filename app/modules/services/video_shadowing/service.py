from fastapi import HTTPException

from .models import VideoShadowingAttempt
from .schemas import VideoShadowingCreate, VideoShadowingUpdate
from .repository import VideoShadowingRepository


class VideoShadowingService:
    def __init__(self, repo: VideoShadowingRepository):
        self.repo = repo

    def calculate_scores(self) -> tuple[float, float, float]:
        # hozircha dummy (keyin AI + Whisper + timing)
        pronunciation = 70.0
        fluency = 75.0
        overall = (pronunciation + fluency) / 2
        return pronunciation, fluency, overall

    async def create(self, user_id: int, data: VideoShadowingCreate):
        pronunciation, fluency, overall = self.calculate_scores()

        attempt = VideoShadowingAttempt(
            user_id=user_id,
            video_url=data.video_url,
            user_audio_url=data.user_audio_url,
            pronunciation_score=pronunciation,
            fluency_score=fluency,
            overall_score=overall,
        )

        return await self.repo.create(attempt)

    async def get(self, attempt_id: int, user_id: int):
        attempt = await self.repo.get_by_id(attempt_id)
        if not attempt or attempt.user_id != user_id: # type: ignore
            raise HTTPException(404, "Attempt not found")
        return attempt

    async def list_user_attempts(self, user_id: int):
        return await self.repo.get_user_attempts(user_id)

    async def update(self, attempt_id: int, user_id: int, data: VideoShadowingUpdate):
        attempt = await self.get(attempt_id, user_id)

        if data.user_audio_url:
            attempt.user_audio_url = data.user_audio_url # type: ignore
            p, f, o = self.calculate_scores()
            attempt.pronunciation_score = p # type: ignore
            attempt.fluency_score = f # type: ignore
            attempt.overall_score = o # type: ignore

        return attempt

    async def delete(self, attempt_id: int, user_id: int):
        attempt = await self.get(attempt_id, user_id)
        await self.repo.delete(attempt)
