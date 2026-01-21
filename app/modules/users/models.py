from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, String, Text,
    DateTime, BigInteger
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(30), unique=True, nullable=True)

    password = Column(String, nullable=False)
    auth_provider = Column(
        String,
        default="local"  # local | telegram | google
    )
    role = Column(String, default="student")
    level = Column(String, default="beginner")
    bio = Column(Text, default="")
    profile_image = Column(String, default="/static/avatars/default.jpg")
    age = Column(Integer, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)

    google_id = Column(String, unique=True, nullable=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    
    settings = relationship(
        "Settings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    user_courses = relationship(
        "UserCourse",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    results = relationship("ExamResult", back_populates="user", cascade="all, delete-orphan")

    user_tasks = relationship(
        "UserTask",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    user_words = relationship(
        "UserWord",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    payments = relationship(
        "Payment",
        back_populates="user",
        lazy="selectin"
    )

    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        lazy="selectin"
    )

    user_lessons = relationship(
        "UserLesson",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    courses_created = relationship(
        "Course",
        back_populates="creator"
    )
    video_shadowing_attempts = relationship(
        "VideoShadowingAttempt",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    audio_writing_attempts = relationship(
        "AudioWritingAttempt",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    reading_results = relationship("ExamResult", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    language = Column(String, default="en")
    notification = Column(Boolean, default=True)
    dark_mode = Column(Boolean, default=False)

    user = relationship(
        "User",
        back_populates="settings"
    )