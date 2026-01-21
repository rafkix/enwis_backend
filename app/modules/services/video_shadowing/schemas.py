from pydantic import BaseModel
from datetime import datetime


class VideoShadowingCreate(BaseModel):
    video_url: str
    user_audio_url: str | None = None


class VideoShadowingUpdate(BaseModel):
    user_audio_url: str | None = None


class VideoShadowingResponse(BaseModel):
    id: int
    video_url: str
    user_audio_url: str | None
    pronunciation_score: float
    fluency_score: float
    overall_score: float
    created_at: datetime

    class Config:
        from_attributes = True
