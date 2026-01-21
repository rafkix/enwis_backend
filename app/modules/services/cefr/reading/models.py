from sqlalchemy import (
    JSON, Column, DateTime, Float, Integer, String, Text, Enum, ForeignKey, func
)
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

# --- ENUMLAR ---
class QuestionType(enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE_NOT_GIVEN = "TRUE_FALSE_NOT_GIVEN"
    GAP_FILL = "GAP_FILL"
    GAP_FILL_FILL = "GAP_FILL_FILL"
    HEADINGS_MATCH = "HEADINGS_MATCH"
    MULTIPLE_SELECT = "MULTIPLE_SELECT"
    TEXT_MATCH = "TEXT_MATCH"

# --- READING IMTIHONI ---
class Exam(Base):
    __tablename__ = "reading_exams"

    id = Column(String, primary_key=True)  # slugs: reading-test-1
    title = Column(String, nullable=False)
    cefr_level = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    language = Column(String, default="en")
    type = Column(String, default="READING")
    total_questions = Column(Integer, default=35)

    # Relationship: Exam -> Parts
    parts = relationship(
        "ReadingPart", 
        back_populates="exam", 
        cascade="all, delete-orphan", 
        lazy="selectin"
    )
    # Relationship: Exam -> Results
    results = relationship(
        "ExamResult", 
        back_populates="exam", 
        cascade="all, delete-orphan"
    )

class ReadingPart(Base):
    __tablename__ = "reading_parts"

    id = Column(Integer, primary_key=True)
    exam_id = Column(String, ForeignKey("reading_exams.id", ondelete="CASCADE"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    passage = Column(Text, nullable=False)

    exam = relationship("Exam", back_populates="parts")
    # Relationship: Part -> Questions
    questions = relationship(
        "Question", 
        back_populates="part", 
        cascade="all, delete-orphan", 
        lazy="selectin"
    )

class Question(Base):
    __tablename__ = "reading_questions"

    id = Column(Integer, primary_key=True)
    part_id = Column(Integer, ForeignKey("reading_parts.id", ondelete="CASCADE"))
    question_number = Column(Integer)
    type = Column(Enum(QuestionType), nullable=False)
    text = Column(Text, nullable=False)
    correct_answer = Column(String, nullable=False)
    word_limit = Column(Integer, nullable=True)

    part = relationship("ReadingPart", back_populates="questions")
    # Relationship: Question -> Options
    options = relationship(
        "QuestionOption", 
        back_populates="question", 
        cascade="all, delete-orphan", 
        lazy="selectin"
    )

class QuestionOption(Base):
    __tablename__ = "reading_question_options"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("reading_questions.id", ondelete="CASCADE"))
    label = Column(String, nullable=False) # A, B, C...
    value = Column(String, nullable=False) # Variant matni

    question = relationship("Question", back_populates="options")

# --- NATIJALAR ---
class ExamResult(Base):
    __tablename__ = "reading_exam_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exam_id = Column(String, ForeignKey("reading_exams.id", ondelete="CASCADE"), nullable=False)
    
    raw_score = Column(Integer)        # To'g'ri javoblar soni (0-35)
    standard_score = Column(Float)     # Agentlik shkalasi (0-75)
    cefr_level = Column(String)        # C1, B2, B1
    percentage = Column(Float)
    
    user_answers = Column(JSON, nullable=False) # {"101": "A", "102": "London"}
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Bog'lanishlar
    # overlaps="results" - SAWarning xatosini oldini olish uchun
    user = relationship("User", back_populates="reading_results", overlaps="results")
    exam = relationship("Exam", back_populates="results")