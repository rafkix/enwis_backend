from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.course_model import Course, CourseCategory
from app.models.user_model import User
from app.schemas.course_schema import CourseCreate, CourseResponse
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/all", response_model=list[CourseResponse])
async def get_courses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course))
    courses = result.scalars().all()
    return courses

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/create", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print(f"🧩 Current user: {current_user.username}, role={current_user.role}")

    # 🔒 Ruxsatni tekshirish
    if not current_user or current_user.role not in ["admin", "mentor", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins, mentors, and teachers can create courses"
        )

    # ✅ Category mavjudligini tekshirish
    category_query = await db.execute(
        select(CourseCategory).where(CourseCategory.id == data.category_id)
    )
    category = category_query.scalars().first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {data.category_id} not found"
        )

    # ✅ Course yaratish
    course = Course(
        title=data.title,
        description=data.description,
        level=data.level,
        created_by=current_user.id,
        category_id=data.category_id  # <- Bu yerda to‘g‘ri ishlayapti
    )

    db.add(course)
    await db.commit()
    await db.refresh(course)

    print(f"✅ Course created: {course.title} (Category: {category.name})")

    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if not current_user or current_user.role not in ["admin", "mentor", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins, mentors, and teachers can create categories"
        )
    course.title = data.title
    course.description = data.description
    course.level = data.level

    db.add(course)
    await db.commit()
    await db.refresh(course)

    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if current_user.role not in ["admin", "mentor", "teacher"] and course.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this course"
        )

    await db.delete(course)
    await db.commit()
    return
