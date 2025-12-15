from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    ForeignKey, DateTime, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ReadingTest(Base):
    __tablename__ = "reading_tests"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    level = Column(String(20), nullable=False)  # B1, B2, C1
    duration_minutes = Column(Integer, default=60)

    is_paid = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    parts = relationship(
        "ReadingPart",
        back_populates="test",
        cascade="all, delete-orphan",
        order_by="ReadingPart.part_number"
    )

class ReadingPart(Base):
    __tablename__ = "reading_parts"

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("reading_tests.id", ondelete="CASCADE"))

    part_number = Column(Integer, nullable=False)  # 1,2,3
    title = Column(String(255), nullable=True)

    content = Column(Text, nullable=False)  # HTML / long text

    test = relationship("ReadingTest", back_populates="parts")

    questions = relationship(
        "ReadingQuestion",
        back_populates="part",
        cascade="all, delete-orphan",
        order_by="ReadingQuestion.order"
    )

QUESTION_TYPES = [
    "MULTIPLE_CHOICE",
    "TRUE_FALSE_NOT_GIVEN",
    "YES_NO_NOT_GIVEN",
    "MATCHING_HEADINGS",
    "MATCHING_INFORMATION",
    "GAP_FILL",
    "SUMMARY_COMPLETION"
]


class ReadingQuestion(Base):
    __tablename__ = "reading_questions"

    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey("reading_parts.id", ondelete="CASCADE"))

    question_type = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)

    options = Column(JSON, nullable=True)       # MCQ, matching
    correct_answer = Column(JSON, nullable=False)

    order = Column(Integer, default=1)

    part = relationship("ReadingPart", back_populates="questions")

class ReadingAttempt(Base):
    __tablename__ = "reading_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    test_id = Column(Integer, ForeignKey("reading_tests.id", ondelete="CASCADE"))

    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    score = Column(Integer, default=0)


class ReadingUserAnswer(Base):
    __tablename__ = "reading_user_answers"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("reading_attempts.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("reading_questions.id", ondelete="CASCADE"))

    user_answer = Column(JSON, nullable=False)
    is_correct = Column(Boolean, default=False)
