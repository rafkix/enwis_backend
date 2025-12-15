from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Any

class ReadingQuestionType(str, Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE_NOT_GIVEN = "TRUE_FALSE_NOT_GIVEN"
    YES_NO_NOT_GIVEN = "YES_NO_NOT_GIVEN"
    MATCHING_HEADINGS = "MATCHING_HEADINGS"
    MATCHING_INFORMATION = "MATCHING_INFORMATION"
    GAP_FILL = "GAP_FILL"
    SUMMARY_COMPLETION = "SUMMARY_COMPLETION"

class ReadingQuestionBase(BaseModel):
    question_type: ReadingQuestionType
    question_text: str
    order: int = 1
    options: Optional[Any] = None  # MCQ / matching

class ReadingQuestionCreate(ReadingQuestionBase):
    correct_answer: Any

class ReadingQuestionRead(ReadingQuestionBase):
    id: int

    class Config:
        from_attributes = True

class ReadingQuestionPublic(ReadingQuestionBase):
    id: int

    class Config:
        from_attributes = True

class ReadingPartBase(BaseModel):
    part_number: int = Field(..., ge=1, le=3)
    title: Optional[str] = None
    content: str

class ReadingPartCreate(ReadingPartBase):
    questions: List[ReadingQuestionCreate]

class ReadingPartRead(ReadingPartBase):
    id: int
    questions: List[ReadingQuestionRead]

    class Config:
        from_attributes = True

class ReadingPartPublic(ReadingPartBase):
    id: int
    questions: List[ReadingQuestionPublic]

    class Config:
        from_attributes = True

class ReadingTestBase(BaseModel):
    title: str
    description: Optional[str] = None
    level: str
    duration_minutes: int = 60
    is_paid: bool = False
    is_active: bool = True

class ReadingTestCreate(ReadingTestBase):
    parts: List[ReadingPartCreate]

class ReadingTestRead(BaseModel):
    id: int
    title: str
    created_at: datetime
    parts: list["ReadingPartRead"]

    class Config:
        from_attributes = True

class ReadingTestPublic(ReadingTestBase):
    id: int
    parts: List[ReadingPartPublic]

    class Config:
        from_attributes = True

class ReadingUserAnswerSubmit(BaseModel):
    question_id: int
    answer: Any

class ReadingSubmitSchema(BaseModel):
    test_id: int
    answers: List[ReadingUserAnswerSubmit]

class ReadingResultSchema(BaseModel):
    test_id: int
    total_questions: int
    correct_answers: int
    score: int
    band_score: Optional[float] = None
