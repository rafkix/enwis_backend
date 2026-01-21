from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


# ---------- PAYMENT ----------

class PaymentCreate(BaseModel):
    plan_type: Optional[str] = None
    amount: float
    currency: str = "UZS"


class PaymentUpdateStatus(BaseModel):
    status: Literal["pending", "completed", "failed"]


class PaymentResponse(BaseModel):
    id: int
    plan_type: Optional[str]
    amount: float
    currency: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- SUBSCRIPTION ----------

class SubscriptionCreate(BaseModel):
    plan_type: str


class SubscriptionResponse(BaseModel):
    id: int
    plan_type: Optional[str]
    start_date: datetime
    end_date: Optional[datetime]
    active: bool

    class Config:
        from_attributes = True
