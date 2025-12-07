from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LessonCreate(BaseModel):
    title: str
    description: Optional[str] = None
    video_url: Optional[str] = None
    order: Optional[int] = None
    course_id: int

class LessonResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    video_url: Optional[str]
    order: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
