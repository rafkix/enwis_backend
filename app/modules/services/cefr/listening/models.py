from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Boolean, ForeignKey, Enum as PgEnum, Text, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

# Savol turlari (TypeScript dagi tiplarga mos)
class ListeningQuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    GAP_FILL = "GAP_FILL"
    MATCHING = "MATCHING"
    MAP_DIAGRAM = "MAP_DIAGRAM"
    SENTENCE_COMPLETION = "SENTENCE_COMPLETION"
    SHORT_ANSWER = "SHORT_ANSWER"

class ListeningExam(Base):
    __tablename__ = "listening_exams"

    id = Column(String, primary_key=True) # listening-demo-1
    title = Column(String, nullable=False)
    is_demo = Column(Boolean, default=False)
    is_free = Column(Boolean, default=False)
    is_mock = Column(Boolean, default=False) # Mock imtihon ekanligini belgilaydi
    is_active = Column(Boolean, default=True) # Admin vaqtincha yopib qo'yishi uchun
    sections = Column(String) # "Sections: 1, 2, 3..."
    level = Column(String) # "MEDIUM Level"
    duration = Column(Integer) # 35 minut
    total_questions = Column(Integer)

    # Bog'lanish
    parts = relationship("ListeningPart", back_populates="exam", cascade="all, delete-orphan")

class ListeningPart(Base):
    __tablename__ = "listening_parts"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(String, ForeignKey("listening_exams.id"))
    part_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    instruction = Column(Text, nullable=False)
    task_type = Column(String, nullable=False) # Frontenddagi "taskType"
    
    # Listening uchun maxsus maydonlar
    audio_label = Column(String, nullable=False) # Audio URL
    context = Column(String, nullable=True) # Masalan: "Saturday music classes"
    passage = Column(Text, nullable=True) # Gap fill matni
    map_image = Column(String, nullable=True) # Map labeling uchun rasm

    # Bog'lanishlar
    exam = relationship("ListeningExam", back_populates="parts")
    questions = relationship("ListeningQuestion", back_populates="part", cascade="all, delete-orphan")
    options = relationship("ListeningPartOption", back_populates="part", cascade="all, delete-orphan")

class ListeningQuestion(Base):
    __tablename__ = "listening_questions"

    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("listening_parts.id"))
    question_number = Column(Integer, nullable=False)
    type = Column(PgEnum(ListeningQuestionType), nullable=False)
    question = Column(Text, nullable=True) # Savol matni (ba'zida bo'lmasligi mumkin)
    correct_answer = Column(String, nullable=False) # Javob

    # Bog'lanishlar
    part = relationship("ListeningPart", back_populates="questions")
    options = relationship("ListeningQuestionOption", back_populates="question", cascade="all, delete-orphan")

# Part darajasidagi optionlar (Matching va Map Labeling uchun A, B, C...)
class ListeningPartOption(Base):
    __tablename__ = "listening_part_options"
    
    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("listening_parts.id"))
    value = Column(String, nullable=False) # "A"
    label = Column(String, nullable=False) # "The forest area"

    part = relationship("ListeningPart", back_populates="options")

# Savol darajasidagi optionlar (Multiple Choice uchun)
class ListeningQuestionOption(Base):
    __tablename__ = "listening_question_options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("listening_questions.id"))
    value = Column(String, nullable=False) # "A"
    label = Column(String, nullable=False) # "It's three o'clock"

    question = relationship("ListeningQuestion", back_populates="options")
    
class ListeningResult(Base):
    __tablename__ = "listening_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exam_id = Column(String, ForeignKey("listening_exams.id",ondelete="CASCADE"), nullable=False)
    
    raw_score = Column(Integer)
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    standard_score = Column(Float)
    cefr_level = Column(String)
    user_answers = Column(JSON)
    percentage = Column(Float)

    # MANA SHU QATORNI QO'SHING:
    created_at = Column(DateTime(timezone=True), server_default=func.now())