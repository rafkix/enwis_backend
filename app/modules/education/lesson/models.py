from sqlalchemy import (
    Column, Integer, String, Text, DateTime,
    ForeignKey, Boolean, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Lesson(Base):
    __tablename__ = "lessons"

    __table_args__ = (
        UniqueConstraint("course_id", "order", name="uq_course_lesson_order"),
        Index("ix_lessons_course_id", "course_id"),
    )

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=1)
    is_free = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    course = relationship("Course", back_populates="lessons")

    tasks = relationship(
        "Task",
        back_populates="lesson",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    user_lessons = relationship(
        "UserLesson",
        back_populates="lesson",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class UserLesson(Base):
    __tablename__ = "user_lessons"

    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),
        Index("ix_user_lessons_user_id", "user_id"),
        Index("ix_user_lessons_lesson_id", "lesson_id"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"))

    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="user_lessons")
    lesson = relationship("Lesson", back_populates="user_lessons")
