from datetime import datetime, timedelta, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, BigInteger
from sqlalchemy.orm import relationship
from app.core.database import Base


class PhoneVerifyCode(Base):
    __tablename__ = "phone_verify_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # NULLABLE
    full_name = Column(String, nullable=False)
    phone = Column(String(30), index=True, nullable=False)
    code = Column(String(10), nullable=False)
    telegram_id = Column(BigInteger, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="phone_verify_codes")

    @staticmethod
    def create(phone: str, code: str, ttl_minutes: int = 5):
        return PhoneVerifyCode(
            phone=phone,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
        )