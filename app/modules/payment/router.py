from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from .schemas import PaymentCreate, PaymentResponse, SubscriptionResponse
from .repository import PaymentRepository, SubscriptionRepository
from app.modules.users.models import User

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/check/me", response_model=list[PaymentResponse])
async def my_payments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repo = PaymentRepository(db)
    return await repo.get_by_user(user.id) # pyright: ignore[reportArgumentType]


@router.get("/subscription/me", response_model=SubscriptionResponse | None)
async def my_subscription(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repo = SubscriptionRepository(db)
    return await repo.get_active(user.id) # pyright: ignore[reportArgumentType]


@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    repo = PaymentRepository(db)
    payment = await repo.create(user.id, data) # pyright: ignore[reportArgumentType]

    await db.commit()
    await db.refresh(payment)
    return payment
