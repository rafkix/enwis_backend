from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class LessonResponse(BaseModel):
    id: int
    title: str
    content: Optional[str] = None

    class Config:
        from_attributes = True


class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    level: Optional[str] = None
    category_id: int


class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    level: Optional[str]
    category_id: int
    created_at: datetime
    updated_at: datetime
    lessons: List[LessonResponse] = []

    class Config:
        from_attributes = True


class CourseCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CourseCategoryCreate(CourseCategoryBase):
    pass


class CourseCategoryResponse(CourseCategoryBase):
    id: int

    class Config:
        from_attributes = True