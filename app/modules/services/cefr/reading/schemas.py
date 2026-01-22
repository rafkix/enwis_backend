from pydantic import BaseModel, Field, ConfigDict, EmailStr
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
    model_config = ConfigDict(from_attributes=True)

# --- QUESTION SCHEMAS ---
class QuestionCreate(BaseModel):
    question_number: Optional[int] = Field(None, alias="question_number")
    type: QuestionType
    text: str
    correct_answer: str = Field(..., alias="correct_answer")
    word_limit: Optional[int] = Field(None, alias="word_limit")
    options: Optional[List[OptionCreate]] = []

    model_config = ConfigDict(populate_by_name=True)

class QuestionResponse(BaseModel):
    id: int
    question_number: Optional[int]
    type: QuestionType
    text: str
    correct_answer: str
    word_limit: Optional[int] = None
    options: List[OptionResponse] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

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
    id: str  # slugs: reading-test-1
    title: str
    isDemo: bool = Field(False, alias="is_demo")
    isFree: bool = Field(False, alias="is_free")
    isMock: bool = Field(False, alias="is_mock")
    isActive: bool = Field(True, alias="is_active")
    cefr_level: str = Field(..., alias="cefr_level")
    duration_minutes: int = Field(60, alias="duration_minutes")
    language: str = "en"
    total_questions: int = Field(35, alias="total_questions")
    parts: List[ReadingPartCreate]
    # QO'SHILGAN MAYDON:
    type: str = Field("READING", description="Imtihon turi: READING yoki LISTENING")

    model_config = ConfigDict(populate_by_name=True)

class ExamUpdate(BaseModel):
    title: Optional[str] = None
    isDemo: Optional[bool] = Field(None, alias="is_demo")
    isFree: Optional[bool] = Field(None, alias="is_free")
    isMock: Optional[bool] = Field(None, alias="is_mock")
    isActive: Optional[bool] = Field(None, alias="is_active")
    cefr_level: Optional[str] = Field(None, alias="cefr_level")
    duration_minutes: Optional[int] = Field(None, alias="duration_minutes")
    language: Optional[str] = None
    total_questions: Optional[int] = Field(None, alias="total_questions")
    parts: Optional[List[ReadingPartCreate]] = None

    model_config = ConfigDict(populate_by_name=True)

class ExamResponse(BaseModel):
    id: str
    title: str
    isDemo: bool = Field(False, alias="is_demo")
    isFree: bool = Field(False, alias="is_free")
    isMock: bool = Field(False, alias="is_mock")
    isActive: bool = Field(True, alias="is_active")
    cefr_level: str
    duration_minutes: int
    language: str
    total_questions: int
    parts: List[ReadingPartResponse]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# --- RESULT & SUBMISSION ---
class ResultSubmission(BaseModel):
    exam_id: str
    user_answers: Dict[str, str] = Field(..., description="Savol ID: Javob")

class ResultResponse(BaseModel):
    id: int
    exam_id: str
    raw_score: int
    standard_score: float
    cefr_level: str
    percentage: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class QuestionReview(BaseModel):
    question_number: int
    user_answer: Optional[str]
    correct_answer: str
    is_correct: bool
    type: QuestionType

    model_config = ConfigDict(from_attributes=True)

class ReadingResultDetailResponse(BaseModel):
    summary: ResultResponse
    review: List[QuestionReview]

    model_config = ConfigDict(from_attributes=True)