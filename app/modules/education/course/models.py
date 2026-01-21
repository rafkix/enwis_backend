from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey,
    DateTime, UniqueConstraint, Index, Enum
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


COURSE_LEVELS = ("beginner", "intermediate", "advanced")


class CourseCategory(Base):
    __tablename__ = "course_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    courses = relationship(
        "Course",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class Course(Base):
    __tablename__ = "courses"

    __table_args__ = (
        Index("ix_courses_category_id", "category_id"),
        Index("ix_courses_created_by", "created_by"),
    )

    id = Column(Integer, primary_key=True)
    title = Column(String(150), nullable=False)
    description = Column(Text)
    level = Column(Enum(*COURSE_LEVELS, name="course_levels"))

    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    category_id = Column(
        Integer,
        ForeignKey("course_categories.id", ondelete="SET NULL"),
        nullable=True
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship(
        "User",
        back_populates="courses_created",
        passive_deletes=True
    )

    category = relationship("CourseCategory", back_populates="courses")

    lessons = relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    user_courses = relationship(
        "UserCourse",
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


class UserCourse(Base):
    __tablename__ = "user_courses"

    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_course"),
        Index("ix_user_courses_user_id", "user_id"),
        Index("ix_user_courses_course_id", "course_id"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="user_courses")
    course = relationship("Course", back_populates="user_courses")
