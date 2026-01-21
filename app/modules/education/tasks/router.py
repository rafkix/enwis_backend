from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from .models import Task, TaskItem, UserTask, UserTaskAnswer
from .schemas import (
    TaskCreate, TaskUpdate, TaskOut,
    UserTaskSubmit, UserTaskOut
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])

ADMIN_ROLES = {"admin", "teacher", "mentor"}


@router.get("/all", response_model=list[TaskOut])
async def list_tasks(
    lesson_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Task)
    if lesson_id:
        stmt = stmt.where(Task.lesson_id == lesson_id)

    res = await db.execute(stmt.order_by(Task.created_at.desc()))
    return res.scalars().all()


@router.get("/select/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.post("/create", response_model=TaskOut, status_code=201)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Forbidden")

    task = Task(
        lesson_id=payload.lesson_id,
        title=payload.title,
        description=payload.description,
        type=payload.type,
        difficulty=payload.difficulty,
        max_score=payload.max_score,
        available_from=payload.available_from,
        deadline=payload.deadline,
        allow_multiple_attempts=payload.allow_multiple_attempts,
    )

    db.add(task)
    await db.flush()

    if payload.items:
        for item in payload.items:
            db.add(
                TaskItem(
                    task_id=task.id,
                    question=item.question,
                    type=item.type,
                    options=item.options,
                    correct_answer=item.correct_answer,
                    points=item.points,
                )
            )

    await db.commit()
    await db.refresh(task)
    return task


# =====================================================
# UPDATE TASK
# =====================================================
@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Forbidden")

    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(404, "Task not found")

    for k, v in data.dict(exclude_unset=True).items():
        setattr(task, k, v)

    await db.commit()
    await db.refresh(task)
    return task


# =====================================================
# SUBMIT TASK (USER)
# =====================================================
@router.post("/{task_id}/submit", response_model=UserTaskOut)
async def submit_task(
    task_id: int,
    payload: UserTaskSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task or not task.is_active: # type: ignore
        raise HTTPException(404, "Task not available")

    user_task = UserTask(
        user_id=current_user.id,
        task_id=task.id,
        is_completed=True,
    )
    db.add(user_task)
    await db.flush()

    total_score = 0.0

    for ans in payload.answers:
        item = await db.scalar(
            select(TaskItem).where(TaskItem.id == ans["task_item_id"])
        )
        if not item:
            continue

        is_correct = ans.get("answer") == item.correct_answer
        score = item.points if is_correct else 0.0
        total_score += score

        db.add(
            UserTaskAnswer(
                user_task_id=user_task.id,
                task_item_id=item.id,
                answer=ans.get("answer"),
                is_correct=is_correct,
                score=score,
            )
        )

    user_task.score = total_score # type: ignore
    user_task.feedback = "Auto graded" # type: ignore
    user_task.graded_by = "system" # type: ignore

    await db.commit()
    await db.refresh(user_task)
    return user_task

@router.delete("/delete/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Forbidden")

    task = await db.scalar(select(Task).where(Task.id == task_id))
    if not task:
        raise HTTPException(404, "Task not found")

    await db.delete(task)
    await db.commit()
