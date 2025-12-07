from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.lesson_model import Lesson
from app.schemas.lesson_schema import LessonCreate, LessonResponse
from app.routers.auth_router import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/lessons", tags=["Lessons"])

@router.get("/all", response_model=list[LessonResponse])
async def get_all_lessons(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lesson))
    lessons = result.scalars().all()
    return lessons

@router.get("/by_course/{course_id}", response_model=list[LessonResponse])
async def get_lessons(course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lesson).where(Lesson.course_id == course_id))
    lessons = result.scalars().all()
    return lessons

@router.post("/create", response_model=LessonResponse)
async def create_lesson(
    data: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "mentor", "teacher"]:
        raise HTTPException(status_code=403, detail="Only admins, teachers, and mentors can add lessons")

    lesson = Lesson(
        title=data.title,
        description=data.description,
        video_url=data.video_url,
        order=data.order,
        course_id=data.course_id
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson

@router.put("/update/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    data: LessonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalars().first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if current_user.role not in ["admin", "mentor", "teacher"]:
        raise HTTPException(status_code=403, detail="Only admins, teachers, and mentors can update lessons")

    lesson.title = data.title
    lesson.description = data.description
    lesson.video_url = data.video_url
    lesson.order = data.order
    lesson.course_id = data.course_id

    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson

@router.delete("/delete/{lesson_id}", status_code=204)
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalars().first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if current_user.role not in ["admin", "mentor", "teacher"]:
        raise HTTPException(status_code=403, detail="Only admins, teachers, and mentors can delete lessons")

    await db.delete(lesson)
    await db.commit()
