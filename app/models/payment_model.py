from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    plan_type = Column(String, nullable=True)
    amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String, default="USD")
    status = Column(String, default="pending")  # e.g. pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payments")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    plan_type = Column(String, nullable=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

    user = relationship("User", back_populates="subscriptions")
