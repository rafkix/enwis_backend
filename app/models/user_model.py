from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, unique=True, nullable=True)
    age = Column(Integer, nullable=True)
    level = Column(String, default="beginner")
    role = Column(String, default="student")
    password = Column(String, nullable=False)
    bio = Column(Text, default="")
    profile_image = Column(String, default="default.jpg")
    created_at = Column(DateTime, default=datetime.utcnow)

    google_id = Column(String, unique=True, nullable=True)
    telegram_id = Column(String, unique=True, nullable=True)
    auth_provider = Column(String, default="local")  # local | google | telegram

    # Relationships (names must match back_populates used in other models)
    settings = relationship("Settings", back_populates="user", uselist=False)
    courses = relationship("UserCourse", back_populates="user", cascade="all, delete-orphan")
    user_tasks = relationship("UserTask", back_populates="user", cascade="all, delete-orphan")
    words = relationship("UserWord", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")
    ai_chats = relationship("AiChat", back_populates="user", cascade="all, delete-orphan")
    translations = relationship("Translation", back_populates="user", cascade="all, delete-orphan")
    user_lessons = relationship("UserLesson", back_populates="user", cascade="all, delete-orphan")
    courses_created = relationship("Course", back_populates="creator", cascade="all, delete-orphan")
    user_courses = relationship("UserCourse", back_populates="user", cascade="all, delete-orphan")
    user_words = relationship("UserWord", back_populates="user", cascade="all, delete-orphan", lazy="selectin")


