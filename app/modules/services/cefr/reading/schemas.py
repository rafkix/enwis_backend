from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime

# --- ENUMLAR ---
class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE_NOT_GIVEN = "TRUE_FALSE_NOT_GIVEN"
    GAP_FILL = "GAP_FILL"
    GAP_FILL_FILL = "GAP_FILL_FILL"
    HEADINGS_MATCH = "HEADINGS_MATCH"
    MULTIPLE_SELECT = "MULTIPLE_SELECT"
    TEXT_MATCH = "TEXT_MATCH"

# --- OPTION SCHEMAS ---
class OptionCreate(BaseModel):
    label: str  # A, B, C...
    value: str  # Variant matni

class OptionResponse(OptionCreate):
    pass

# --- QUESTION SCHEMAS ---
class QuestionCreate(BaseModel):
    question_number: Optional[int] = None
    type: QuestionType
    text: str
    correct_answer: str
    word_limit: Optional[int] = None
    options: Optional[List[OptionCreate]] = []
    # total_questions bu yerdan olib tashlandi, chunki u Exam darajasida

class QuestionResponse(BaseModel):
    id: int
    question_number: Optional[int]
    type: QuestionType
    text: str
    correct_answer: str
    word_limit: Optional[int] = None
    options: List[OptionResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- PART SCHEMAS ---
class ReadingPartCreate(BaseModel):
    title: str
    description: str
    passage: str
    questions: List[QuestionCreate]

class ReadingPartResponse(BaseModel):
    id: int
    title: str
    description: str
    passage: str
    questions: List[QuestionResponse]

    model_config = ConfigDict(from_attributes=True)

# --- EXAM SCHEMAS ---
class ExamCreate(BaseModel):
    id: str  # Slugs: reading-test-1
    title: str
    cefr_level: str
    duration_minutes: int
    language: str = "en"
    type: str = "READING"
    total_questions: int = 35
    parts: List[ReadingPartCreate]

class ExamUpdate(BaseModel):
    title: Optional[str] = None
    cefr_level: Optional[str] = None
    duration_minutes: Optional[int] = None
    language: Optional[str] = None
    total_questions: Optional[int] = None
    parts: Optional[List[ReadingPartCreate]] = None

class ExamResponse(BaseModel):
    id: str
    title: str
    cefr_level: str
    duration_minutes: int
    language: str
    type: str
    total_questions: int
    parts: List[ReadingPartResponse]

    model_config = ConfigDict(from_attributes=True)

# --- RESULT & SUBMISSION SCHEMAS ---

class ResultSubmission(BaseModel):
    exam_id: str
    user_answers: Dict[str, str] = Field(..., description="Savol ID va javob: {'101': 'A'}")

class ResultResponse(BaseModel):
    id: int
    exam_id: str
    raw_score: int
    standard_score: float
    cefr_level: str
    percentage: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Review (Tahlil) sahifasi uchun detallar
class QuestionReview(BaseModel):
    question_number: int
    user_answer: Optional[str]
    correct_answer: str
    is_correct: bool
    type: QuestionType

class ReadingResultDetailResponse(BaseModel):
    summary: ResultResponse
    review: List[QuestionReview]

    model_config = ConfigDict(from_attributes=True)