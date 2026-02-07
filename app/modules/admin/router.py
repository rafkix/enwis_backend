from sqlalchemy import func, select
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.permissions import require_admin, require_roles

from app.modules.users.models import User
from app.modules.users.schemas import UserResponse
from app.modules.admin.service import AdminUserService

from app.modules.education.tasks.models import Task, UserTask
from app.modules.education.tasks.schemas import UserTaskOut

from app.modules.payment.repository import (
    PaymentRepository,
    SubscriptionRepository
)
from app.modules.payment.schemas import (
    PaymentResponse,
    PaymentUpdateStatus,
    SubscriptionResponse
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_roles("admin", "teacher", "mentor"))],
)

# ======================================================
# USERS
# ======================================================
@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(User))
    return res.scalars().all()


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


# ======================================================
# ADMIN USER MANAGEMENT (ONLY ADMIN)
# ======================================================
@router.put("/users/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    service = AdminUserService(db, admin)
    await service.reset_password(user, new_password)

    return {"message": "Password reset successfully"}


@router.put("/users/{user_id}/role")
async def change_role(
    user_id: int,
    role: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    service = AdminUserService(db, admin)
    await service.change_role(user, role)

    return {"message": f"Role changed to {role}"}


@router.put("/users/{user_id}/block")
async def block_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    service = AdminUserService(db, admin)
    await service.block_user(user)

    return {"message": "User blocked"}


@router.put("/users/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    service = AdminUserService(db, admin)
    await service.unblock_user(user)

    return {"message": "User unblocked"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    service = AdminUserService(db, admin)
    await service.delete_user(user)

    return {"message": "User deleted"}


# ======================================================
# TASKS
# ======================================================
@router.get("/tasks/{task_id}/submissions", response_model=list[UserTaskOut])
async def task_submissions(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(UserTask).where(UserTask.task_id == task_id)
    )
    return res.scalars().all()


@router.delete("/tasks/user-task/{user_task_id}", status_code=204)
async def delete_user_task(
    user_task_id: int,
    db: AsyncSession = Depends(get_db),
):
    ut = await db.get(UserTask, user_task_id)
    if not ut:
        raise HTTPException(404, "UserTask not found")

    await db.delete(ut)
    await db.commit()


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    await db.delete(task)
    await db.commit()


# ======================================================
# PAYMENTS
# ======================================================
@router.get("/payments", response_model=list[PaymentResponse])
async def all_payments(
    db: AsyncSession = Depends(get_db),
):
    return await PaymentRepository(db).get_all()  # type: ignore


@router.patch("/payments/{payment_id}", response_model=PaymentResponse)
async def update_payment_status(
    payment_id: int,
    data: PaymentUpdateStatus,
    db: AsyncSession = Depends(get_db),
):
    repo = PaymentRepository(db)
    payment = await repo.get_by_id(payment_id)

    if not payment:
        raise HTTPException(404, "Payment not found")

    await repo.update_status(payment, data.status)
    return payment


# ======================================================
# SUBSCRIPTIONS
# ======================================================
@router.post("/subscriptions/{user_id}", response_model=SubscriptionResponse)
async def grant_subscription(
    user_id: int,
    plan_type: str,
    db: AsyncSession = Depends(get_db),
):
    repo = SubscriptionRepository(db)
    sub = await repo.create_subscription(user_id, plan_type)  # type: ignore
    return sub


@router.patch("/subscriptions/{sub_id}/cancel")
async def cancel_subscription(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
):
    repo = SubscriptionRepository(db)
    sub = await repo.get_by_id(sub_id) # type: ignore

    if not sub:
        raise HTTPException(404, "Subscription not found")

    await repo.cancel(sub)
    return {"message": "Subscription cancelled"}


@router.get("/stats/overview")
async def admin_stats(db: AsyncSession = Depends(get_db)):
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(
        select(func.count(User.id)).where(User.is_active == True)
    )
    total_tests = await db.scalar(select(func.count(UserTask.id)))
    users_with_tests = await db.scalar(
        select(func.count(func.distinct(UserTask.user_id)))
    )

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "with_tests": users_with_tests,
        },
        "tests": {
            "total_attempts": total_tests,
        }
    }
