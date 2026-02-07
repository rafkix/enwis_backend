from typing import Optional
from datetime import datetime

from sqlalchemy import (
    Integer, String, ForeignKey, DateTime, Float, Boolean
)
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship
)

from app.core.database import Base
from app.modules.users.models import User


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    product_type: Mapped[str] = mapped_column(
        String,  # subscription | mock_test | course
        nullable=False
    )

    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="UZS")

    status: Mapped[str] = mapped_column(
        String,
        default="pending"  # pending | paid | failed | refunded
    )

    provider: Mapped[Optional[str]] = mapped_column(
        String,  # click | payme | stripe
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="payments")



class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    plan_type: Mapped[str] = mapped_column(
        String,  # free | basic | premium
        nullable=False
    )

    start_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    active: Mapped[bool] = mapped_column(Boolean, default=True)

    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="subscriptions")

