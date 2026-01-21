from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db

from .models import CourseCategory
from .schema import CourseCategoryCreate, CourseCategoryResponse
from app.modules.users.models import User
from app.modules.auth.dependencies import get_current_user


router = APIRouter(prefix="/categories", tags=["Course Categories"])

@router.get("/all", response_model=list[CourseCategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CourseCategory))
    categories = result.scalars().all()
    return categories

@router.get("/select/{category_id}", response_model=CourseCategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CourseCategory).where(CourseCategory.id == category_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.post("/create", response_model=CourseCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CourseCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user or current_user.role not in ["admin", "mentor", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins, mentors, and teachers can create categories"
        )

    existing = await db.execute(select(CourseCategory).where(CourseCategory.name == data.name))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Category already exists")

    category = CourseCategory(
        name=data.name,
        description=data.description
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return category


@router.put("/update/{category_id}", response_model=CourseCategoryResponse)
async def update_category(
    category_id: int,
    data: CourseCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user or current_user.role not in ["admin", "mentor", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins, mentors, and teachers can update categories"
        )

    result = await db.execute(select(CourseCategory).where(CourseCategory.id == category_id))
    category = result.scalars().first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.name = data.name # type: ignore
    category.description = data.description # type: ignore

    db.add(category)
    await db.commit()
    await db.refresh(category)

    return category

@router.delete("/delete/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user or current_user.role not in ["admin", "mentor", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins, mentors, and teachers can delete categories"
        )

    result = await db.execute(select(CourseCategory).where(CourseCategory.id == category_id))
    category = result.scalars().first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    await db.delete(category)
    await db.commit()