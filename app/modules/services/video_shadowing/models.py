from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class VideoShadowingAttempt(Base):
    __tablename__ = "video_shadowing_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    video_url = Column(String, nullable=False)
    user_audio_url = Column(String, nullable=True)

    pronunciation_score = Column(Float, default=0.0)
    fluency_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship(
        "User",
        back_populates="video_shadowing_attempts"
    )
