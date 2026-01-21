from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.core.database import Base


class DailyVocabWords(Base):
    __tablename__ = "daily_vocab"

    id = Column(Integer, primary_key=True)
    word = Column(String(100), unique=True, nullable=False)
    uz_translation = Column(Text, nullable=False)
    level = Column(String(10), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
