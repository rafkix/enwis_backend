from pydantic import BaseModel
from datetime import datetime


class DailyVocabBase(BaseModel):
    word: str
    uz_translation: str
    level: str

class DailyVocabCreate(DailyVocabBase):
    pass

class DailyVocabUpdate(BaseModel):
    uz_translation: str | None = None
    level: str | None = None

class DailyVocabResponse(DailyVocabBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Definition(BaseModel):
    definition: str
    example: str | None = None

class DictionaryResponse(BaseModel):
    word: str
    phonetic: str | None = None
    part: str | None = None
    audio: str | None = None

    definitions: list[Definition]
    synonyms: list[str] = []
    antonyms: list[str] = []
    origin: str | None = None
