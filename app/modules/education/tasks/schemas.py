from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


# =========================
# TASK ITEM (QUESTION)
# =========================
class TaskItemCreate(BaseModel):
    question: str
    type: str                  # mcq / text / audio
    options: Optional[Any] = None
    correct_answer: Optional[Any] = None
    points: float = 1.0


class TaskItemOut(BaseModel):
    id: int
    question: str
    type: str
    options: Optional[Any]
    points: float

    class Config:
        from_attributes = True


# =========================
# TASK
# =========================
class TaskCreate(BaseModel):
    lesson_id: int
    title: str
    description: Optional[str] = None
    type: str                  # quiz / writing / speaking
    difficulty: str = "easy"
    max_score: float = 100
    available_from: Optional[datetime] = None
    deadline: Optional[datetime] = None
    allow_multiple_attempts: bool = False
    items: Optional[List[TaskItemCreate]] = None


class TaskUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    difficulty: Optional[str]
    max_score: Optional[float]
    deadline: Optional[datetime]
    is_active: Optional[bool]


class TaskOut(BaseModel):
    id: int
    lesson_id: int
    title: str
    description: Optional[str]
    type: str
    difficulty: str
    max_score: float
    is_active: bool
    created_at: datetime
    items: List[TaskItemOut] = []

    class Config:
        from_attributes = True


# =========================
# USER TASK (ATTEMPT)
# =========================
class UserTaskSubmit(BaseModel):
    answers: List[dict]  # {task_item_id, answer}


class UserTaskOut(BaseModel):
    id: int
    score: float
    is_completed: bool
    attempt_number: int
    submitted_at: datetime
    feedback: Optional[str]

    class Config:
        from_attributes = True
