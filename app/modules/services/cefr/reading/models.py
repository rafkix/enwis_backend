from sqlalchemy import (
    JSON, Column, DateTime, Float, Integer, String, Text, Enum, ForeignKey, Boolean, func
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE_NOT_GIVEN = "TRUE_FALSE_NOT_GIVEN"
    GAP_FILL = "GAP_FILL"
    GAP_FILL_FILL = "GAP_FILL_FILL"
    HEADINGS_MATCH = "HEADINGS_MATCH"
    MULTIPLE_SELECT = "MULTIPLE_SELECT"
    TEXT_MATCH = "TEXT_MATCH"

class Exam(Base):
    __tablename__ = "reading_exams"

    id = Column(String, primary_key=True) 
    title = Column(String, nullable=False)
    is_demo = Column(Boolean, default=False)
    is_free = Column(Boolean, default=False)
    is_mock = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    cefr_level = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    language = Column(String, default="en")
    type = Column(String, default="READING")
    total_questions = Column(Integer, default=35)

    parts = relationship("ReadingPart", back_populates="exam", cascade="all, delete-orphan", lazy="selectin")
    results = relationship("ExamResult", back_populates="exam", cascade="all, delete-orphan")

class ReadingPart(Base):
    __tablename__ = "reading_parts"

    id = Column(Integer, primary_key=True)
    exam_id = Column(String, ForeignKey("reading_exams.id", ondelete="CASCADE"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    passage = Column(Text, nullable=False)

    exam = relationship("Exam", back_populates="parts")
    questions = relationship("Question", back_populates="part", cascade="all, delete-orphan", lazy="selectin")

class Question(Base):
    __tablename__ = "reading_questions"

    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey("reading_parts.id", ondelete="CASCADE"))
    question_number = Column(Integer)
    type = Column(Enum(QuestionType, native_enum=False), nullable=False) # Native Enum muammosini oldini olish
    text = Column(Text, nullable=False)
    correct_answer = Column(String, nullable=False)
    word_limit = Column(Integer, nullable=True)

    part = relationship("ReadingPart", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan", lazy="selectin")

class QuestionOption(Base):
    __tablename__ = "reading_question_options"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("reading_questions.id", ondelete="CASCADE"))
    label = Column(String, nullable=False)
    value = Column(String, nullable=False)

    question = relationship("Question", back_populates="options")

class ExamResult(Base):
    __tablename__ = "reading_exam_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exam_id = Column(String, ForeignKey("reading_exams.id", ondelete="CASCADE"), nullable=False)
    
    raw_score = Column(Integer)
    standard_score = Column(Float)
    cefr_level = Column(String)
    percentage = Column(Float)
    
    user_answers = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reading_results")
    exam = relationship("Exam", back_populates="results")