import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from .models import ListeningQuestionType

# --- BASE (Umumiy) ---
class OptionBase(BaseModel):
    value: str
    label: str

class ListeningSubmission(BaseModel):
    exam_id: str
    user_answers: Dict[str, str]

# app/modules/services/cefr/listening/schemas.py ichida bo'lishi shart:
class ListeningResultCreate(BaseModel):
    exam_id: str
    total_questions: int
    correct_answers: int
    standard_score: float
    user_answers: Dict[str, str]

class ListeningResultResponse(BaseModel):
    id: int
    exam_id: str
    # 'Optional' va default qiymatlar qo'shildi (Validation error'ni oldini oladi)
    total_questions: Optional[int] = 0
    correct_answers: Optional[int] = 0
    standard_score: float = 0.0
    cefr_level: Optional[str] = "N/A"
    created_at: datetime.datetime 

    class Config:
        from_attributes = True
        populate_by_name = True

# --- EXAM SCHEMAS ---
class ListeningQuestionBase(BaseModel):
    questionNumber: int = Field(..., alias="question_number")
    type: ListeningQuestionType
    question: Optional[str] = None
    correctAnswer: str = Field(..., alias="correct_answer")
    options: Optional[List[OptionBase]] = None

class ListeningPartBase(BaseModel):
    partNumber: int = Field(..., alias="part_number")
    title: str
    instruction: str
    taskType: str = Field(..., alias="task_type")
    audioLabel: str = Field(..., alias="audio_label")
    context: Optional[str] = None
    passage: Optional[str] = None
    mapImage: Optional[str] = Field(None, alias="map_image")
    options: Optional[List[OptionBase]] = None 

class ListeningExamBase(BaseModel):
    id: str 
    title: str
    isDemo: bool = Field(False, alias="is_demo")
    isFree: bool = Field(False, alias="is_free")
    sections: str
    level: str
    duration: int
    totalQuestions: int = Field(..., alias="total_questions")

# --- CREATE & UPDATE ---
class ListeningQuestionCreate(ListeningQuestionBase):
    pass

class ListeningPartCreate(ListeningPartBase):
    questions: List[ListeningQuestionCreate]

class ListeningExamCreate(ListeningExamBase):
    parts: List[ListeningPartCreate]

class ListeningExamUpdate(BaseModel):
    title: Optional[str] = None
    isDemo: Optional[bool] = Field(None, alias="is_demo")
    isFree: Optional[bool] = Field(None, alias="is_free")
    level: Optional[str] = None
    duration: Optional[int] = None

# --- RESPONSE (Detailed) ---
class ListeningQuestionResponse(ListeningQuestionBase):
    id: int
    class Config:
        from_attributes = True
        populate_by_name = True

class ListeningPartResponse(ListeningPartBase):
    id: int
    questions: List[ListeningQuestionResponse]
    class Config:
        from_attributes = True
        populate_by_name = True

class ListeningExamResponse(ListeningExamBase):
    parts: List[ListeningPartResponse]
    class Config:
        from_attributes = True
        populate_by_name = True

# Natija detallari (Review sahifasi uchun)
class ListeningResultDetailResponse(BaseModel):
    summary: ListeningResultResponse
    review: List[Dict]

    class Config:
        from_attributes = True