from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base


class PracticeAttempt(Base):
    __tablename__ = "practice_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    duration_seconds = Column(Integer, default=0)
    overall_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
