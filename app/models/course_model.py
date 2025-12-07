from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class CourseCategory(Base):
    __tablename__ = "course_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # ✅ To'g'ri bog'lanish
    courses = relationship("Course", back_populates="category", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(String(50), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    category_id = Column(Integer, ForeignKey("course_categories.id", ondelete="SET NULL"))  # ✅ yangi
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ Bog'lanishlar
    creator = relationship("User", back_populates="courses_created", overlaps="user_courses,courses")
    category = relationship("CourseCategory", back_populates="courses")
    lessons = relationship("Lesson", back_populates="course", lazy="selectin")
    user_courses = relationship("UserCourse", back_populates="course", cascade="all, delete-orphan")


class UserCourse(Base):
    __tablename__ = "user_courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="user_courses", overlaps="courses,courses_created")
    course = relationship("Course", back_populates="user_courses", overlaps="creator,user_courses")