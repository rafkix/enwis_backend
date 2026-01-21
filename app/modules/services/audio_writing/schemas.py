from pydantic import BaseModel, Field
from datetime import datetime


class AudioWritingCreate(BaseModel):
    audio_url: str
    user_text: str


class AudioWritingUpdate(BaseModel):
    user_text: str | None = None


class AudioWritingResponse(BaseModel):
    id: int
    audio_url: str
    user_text: str
    accuracy: float
    created_at: datetime

    class Config:
        from_attributes = True
