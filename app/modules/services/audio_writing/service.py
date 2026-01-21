from fastapi import HTTPException

from .models import AudioWritingAttempt
from .schemas import AudioWritingCreate, AudioWritingUpdate
from .repository import AudioWritingRepository


class AudioWritingService:
    def __init__(self, repo: AudioWritingRepository):
        self.repo = repo

    def calculate_accuracy(self, text: str) -> float:
        # hozircha dummy (keyin AI qo‘shamiz)
        return min(len(text) * 1.5, 100.0)

    async def create(self, user_id: int, data: AudioWritingCreate):
        accuracy = self.calculate_accuracy(data.user_text)

        attempt = AudioWritingAttempt(
            user_id=user_id,
            audio_url=data.audio_url,
            user_text=data.user_text,
            accuracy=accuracy,
        )

        return await self.repo.create(attempt)

    async def get(self, attempt_id: int, user_id: int):
        attempt = await self.repo.get_by_id(attempt_id)
        if not attempt or attempt.user_id != user_id: # type: ignore
            raise HTTPException(404, "Attempt not found")
        return attempt

    async def list_user_attempts(self, user_id: int):
        return await self.repo.get_user_attempts(user_id)

    async def update(self, attempt_id: int, user_id: int, data: AudioWritingUpdate):
        attempt = await self.get(attempt_id, user_id)

        if data.user_text:
            attempt.user_text = data.user_text
            attempt.accuracy = self.calculate_accuracy(data.user_text)

        return attempt

    async def delete(self, attempt_id: int, user_id: int):
        attempt = await self.get(attempt_id, user_id)
        await self.repo.delete(attempt)
