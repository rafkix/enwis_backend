from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class AudioWritingAttempt(Base):
    __tablename__ = "audio_writing_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    audio_url = Column(String, nullable=False)
    user_text = Column(String, nullable=False)
    accuracy = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audio_writing_attempts")
