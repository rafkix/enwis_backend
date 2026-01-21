from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.modules.education.words.models import SRSStage


# ------------------------------
# CATEGORY
# ------------------------------

class WordCategoryBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    language: str = "en"
    icon: Optional[str] = None
    is_active: bool = True


class WordCategoryCreate(BaseModel):
    title: str
    description: Optional[str]
    language: Optional[str]
    icon: Optional[str]
    is_active: Optional[bool]


class WordCategoryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class WordCategoryOut(WordCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ------------------------------
# WORD EXAMPLE
# ------------------------------

class WordExampleBase(BaseModel):
    text: str
    translation: Optional[str] = None
    source: Optional[str] = None
    is_preferred: bool = False


class WordExampleCreate(WordExampleBase):
    pass


class WordExampleOut(WordExampleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------------------
# WORD AUDIO
# ------------------------------

class WordAudioBase(BaseModel):
    provider: Optional[str] = None
    url: str
    duration: Optional[float] = None
    meta_data: Optional[dict] = None


class WordAudioCreate(WordAudioBase):
    pass


class WordAudioOut(WordAudioBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------------------
# WORD SYNONYM
# ------------------------------

class WordSynonymBase(BaseModel):
    synonym: str
    type: Optional[str] = None   # near/exact/antonym


class WordSynonymCreate(WordSynonymBase):
    pass


class WordSynonymOut(WordSynonymBase):
    id: int

    class Config:
        from_attributes = True


# ------------------------------
# WORD ITEM
# ------------------------------

class WordBase(BaseModel):
    lemma: str
    pos: Optional[str] = None
    base_language: str = "en"
    meaning: Optional[str] = None
    transcription: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[list] = None
    meta_data: Optional[dict] = None


class WordCreate(WordBase):
    examples: Optional[List[WordExampleCreate]] = None
    audios: Optional[List[WordAudioCreate]] = None
    synonyms: Optional[List[WordSynonymCreate]] = None
    categories: Optional[List[int]] = None


class WordUpdate(BaseModel):
    lemma: Optional[str] = None
    pos: Optional[str] = None
    meaning: Optional[str] = None
    transcription: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[list] = None
    meta_data: Optional[dict] = None


class WordOut(WordBase):
    id: int
    example_count: int
    created_at: datetime
    updated_at: datetime

    examples: List[WordExampleOut] = []
    audios: List[WordAudioOut] = []
    synonyms: List[WordSynonymOut] = []
    categories: list = []

    class Config:
        from_attributes = True


# ------------------------------
# USER WORD (SRS)
# ------------------------------

class UserWordBase(BaseModel):
    user_notes: Optional[str] = None
    user_translation: Optional[str] = None


class UserWordAdd(BaseModel):
    word_id: int


class UserWordUpdate(UserWordBase):
    pass


class UserWordOut(BaseModel):
    id: int
    user_id: int
    word_id: int
    stage: SRSStage
    efactor: float
    interval_days: int
    repetitions: int
    last_reviewed_at: Optional[datetime]
    next_review_at: Optional[datetime]
    streak: int

    word: WordOut

    class Config:
        from_attributes = True


# ------------------------------
# REVIEW ATTEMPT
# ------------------------------

class ReviewAttempt(BaseModel):
    word_id: int
    quality: int = Field(..., ge=0, le=5)  # SM-2 quality response 0–5
