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
    description: Optional[str] = None
    video_url: Optional[str] = None
    order: Optional[int] = None
    # created_at maydonini Optional qiling va default qiymat bering
    created_at: Optional[datetime] = None 

    class Config:
        from_attributes = True