from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.education.tasks.models import Task, UserTask
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.permissions import require_admin, require_roles
from app.modules.education.tasks.schemas import UserTaskOut
from app.modules.payment.repository import PaymentRepository, SubscriptionRepository
from app.modules.payment.schemas import PaymentResponse, PaymentUpdateStatus, SubscriptionResponse
from app.modules.users.models import User
from app.modules.admin.service import AdminUserService
from app.modules.users.schemas import UserResponse


ADMIN_ROLES = {"admin", "teacher", "mentor"}

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users/all", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    result = await db.execute(select(User))
    return result.scalars().all()

@router.get("/users/select/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

@router.get("/task/{task_id}/submissions", response_model=list[UserTaskOut])
async def task_submissions(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Forbidden")

    res = await db.execute(
        select(UserTask).where(UserTask.task_id == task_id)
    )
    return res.scalars().all()

@router.get("/admin/all", response_model=list[PaymentResponse])
async def all_payments(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return await PaymentRepository(db).get_all() # type: ignore

@router.post("/subscription/{user_id}", response_model=SubscriptionResponse)
async def grant_subscription(
    user_id: int,
    plan_type: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    repo = SubscriptionRepository(db)
    sub = await repo.create_subscription(user_id, plan_type) # type: ignore

    await db.commit()
    await db.refresh(sub)
    return sub

@router.patch("/status/{payment_id}", response_model=PaymentResponse)
async def update_payment_status(
    payment_id: int,
    data: PaymentUpdateStatus,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    repo = PaymentRepository(db)
    payment = await repo.get_by_id(payment_id)

    if not payment:
        raise HTTPException(404, "Payment not found")

    await repo.update_status(payment, data.status)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.patch("/admin/subscription/{sub_id}/cancel")
async def cancel_subscription(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    repo = SubscriptionRepository(db)
    sub = await db.get(repo.model, sub_id) # type: ignore

    if not sub:
        raise HTTPException(404, "Subscription not found")

    await repo.cancel(sub)
    await db.commit()
    return {"message": "Subscription cancelled"}


@router.put("/users/update/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_roles("admin"))
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    service = AdminUserService(db)
    await service.reset_password(user, new_password)
    await db.commit()

    return {"message": "Password reset successfully"}

@router.put("/users/update/{user_id}/role")
async def change_role(
    user_id: int,
    role: str,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_roles("admin"))
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404)

    service = AdminUserService(db)
    await service.change_role(user, role)
    await db.commit()

    return {"message": f"Role changed to {role}"}

@router.put("/users/update/{user_id}/block")
async def block_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin = Depends(require_roles("admin"))
):
    user = await db.get(User, user_id)
    service = AdminUserService(db)
    await service.block_user(user)
    await db.commit()
    return {"message": "User blocked"}

@router.delete("/users/delete/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    user = await db.get(User, user_id)

    if user.id == admin.id: # type: ignore
        raise HTTPException(400, "Cannot delete yourself")

    service = AdminUserService(db)
    await service.delete_user(user)
    await db.commit()

    return {"message": "User deleted"}

@router.delete("/user/task/{user_task_id}", status_code=204)
async def delete_user_task(
    user_task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(403, "Forbidden")

    ut = await db.scalar(select(UserTask).where(UserTask.id == user_task_id))
    if not ut:
        raise HTTPException(404, "UserTask not found")

    await db.delete(ut)
    await db.commit()
    
@router.delete("/delete/task/{task_id}", status_code=204)
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
