import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    Float,
    JSON,
    UniqueConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from app.core.database import Base

class TaskTypeEnum(str, enum.Enum):
    quiz = "quiz"
    writing = "writing"
    speaking = "speaking"


class TaskItemTypeEnum(str, enum.Enum):
    mcq = "mcq"
    text = "text"
    audio = "audio"
    matching = "matching"
    gap_fill = "gap_fill"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    lesson_id = Column(
        Integer,
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
    )

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    type = Column(
        SQLEnum(TaskTypeEnum, name="task_type"),
        nullable=False,
    )

    difficulty = Column(String(20), default="easy")
    max_score = Column(Float, default=100)

    is_active = Column(Boolean, default=True)

    available_from = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    lesson = relationship("Lesson", back_populates="tasks")

    items = relationship(
        "TaskItem",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    user_tasks = relationship(
        "UserTask",
        back_populates="task",
        cascade="all, delete-orphan",
    )

class TaskItem(Base):
    __tablename__ = "task_items"

    id = Column(Integer, primary_key=True)

    task_id = Column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )

    question = Column(Text, nullable=False)

    type = Column(
        SQLEnum(TaskItemTypeEnum, name="task_item_type"),
        nullable=False,
    )

    options = Column(JSON, nullable=True)          # mcq / matching
    correct_answer = Column(JSON, nullable=True)   # auto check

    points = Column(Float, default=1.0)

    task = relationship("Task", back_populates="items")

class UserTask(Base):
    __tablename__ = "user_tasks"

    __table_args__ = (
        UniqueConstraint("user_id", "task_id", name="uq_user_task"),
    )

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    task_id = Column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )

    score = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    attempt_number = Column(Integer, default=1)

    submitted_at = Column(DateTime, nullable=True)
    feedback = Column(Text, nullable=True)

    # relationships
    user = relationship("User", back_populates="user_tasks")
    task = relationship("Task", back_populates="user_tasks")

    answers = relationship(
        "UserTaskAnswer",
        back_populates="user_task",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

class UserTaskAnswer(Base):
    __tablename__ = "user_task_answers"

    __table_args__ = (
        UniqueConstraint(
            "user_task_id",
            "task_item_id",
            name="uq_user_task_answer",
        ),
    )

    id = Column(Integer, primary_key=True)

    user_task_id = Column(
        Integer,
        ForeignKey("user_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )

    task_item_id = Column(
        Integer,
        ForeignKey("task_items.id", ondelete="CASCADE"),
        nullable=False,
    )

    answer = Column(JSON, nullable=True)

    is_correct = Column(Boolean, nullable=True)
    score = Column(Float, default=0.0)

    user_task = relationship("UserTask", back_populates="answers")
