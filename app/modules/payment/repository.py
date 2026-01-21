from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Payment, Subscription


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, data):
        payment = Payment(
            user_id=user_id,
            plan_type=data.plan_type,
            amount=data.amount,
            currency=data.currency,
            status="pending",
        )
        self.db.add(payment)
        return payment

    async def get_by_user(self, user_id: int):
        res = await self.db.execute(
            select(Payment).where(Payment.user_id == user_id)
        )
        return res.scalars().all()

    async def get_by_id(self, payment_id: int):
        res = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return res.scalar_one_or_none()

    async def update_status(self, payment: Payment, status: str):
        payment.status = status
        return payment


class SubscriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active(self, user_id: int):
        res = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.active.is_(True)
            )
        )
        return res.scalar_one_or_none()

    async def create(self, user_id: int, plan_type: str):
        sub = Subscription(
            user_id=user_id,
            plan_type=plan_type,
            active=True,
        )
        self.db.add(sub)
        return sub

    async def cancel(self, sub: Subscription):
        sub.active = False # type: ignore
        return sub
