# app/models/words_model.py

from __future__ import annotations
import enum
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey, Enum,
    JSON, DateTime, Float, func, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


# =====================================
#  SRS (Spaced Repetition System)
# =====================================
class SRSStage(int, enum.Enum):
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    MASTERED = 3


# =====================================
#  WORD CATEGORY
# =====================================
class WordCategory(Base):
    __tablename__ = "word_categories"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    language = Column(String(10), default="en")
    icon = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items = relationship(
        "WordCategoryItem",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


# =====================================
#  MANY-TO-MANY PIVOT
# =====================================
class WordCategoryItem(Base):
    __tablename__ = "word_category_items"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("word_categories.id", ondelete="CASCADE"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)

    custom_note = Column(Text)

    category = relationship("WordCategory", back_populates="items", lazy="joined")
    word = relationship("Word", lazy="joined")

    __table_args__ = (
        UniqueConstraint("category_id", "word_id", name="uq_category_word"),
    )


# =====================================
#  WORD
# =====================================
class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True)
    lemma = Column(String(255), nullable=False, index=True)
    pos = Column(String(50), nullable=True)
    base_language = Column(String(10), nullable=False, default="en")
    meaning = Column(Text, nullable=True)
    transcription = Column(String(100), nullable=True)
    difficulty = Column(String(20), nullable=True)
    tags = Column(JSON, nullable=True)
    meta_data = Column(JSON, nullable=True)
    example_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    examples = relationship(
        "WordExample",
        back_populates="word",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    audios = relationship(
        "WordAudio",
        back_populates="word",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    synonyms = relationship(
        "WordSynonym",
        back_populates="word",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    categories = relationship(
        "WordCategoryItem",
        back_populates="word",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    __table_args__ = (
        Index("ix_words_lemma_base", "lemma", "base_language"),
    )


# =====================================
#  WORD EXAMPLES
# =====================================
class WordExample(Base):
    __tablename__ = "word_examples"

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)

    text = Column(Text, nullable=False)
    translation = Column(Text)
    source = Column(String(255))
    is_preferred = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    word = relationship("Word", back_populates="examples", lazy="joined")


# =====================================
#  WORD AUDIOS
# =====================================
class WordAudio(Base):
    __tablename__ = "word_audios"

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)

    provider = Column(String(50))
    url = Column(String(1000), nullable=False)
    duration = Column(Float)
    meta_data = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    word = relationship("Word", back_populates="audios", lazy="joined")


# =====================================
#  WORD SYNONYMS
# =====================================
class WordSynonym(Base):
    __tablename__ = "word_synonyms"

    id = Column(Integer, primary_key=True)
    word_id = Column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)

    synonym = Column(String(255), nullable=False)
    type = Column(String(50))  # exact, near, antonym

    word = relationship("Word", back_populates="synonyms", lazy="joined")


# =====================================
#  USER WORD (SRS PROGRESS)
# =====================================
class UserWord(Base):
    __tablename__ = "user_words"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id", ondelete="CASCADE"), nullable=False)

    stage = Column(Enum(SRSStage), default=SRSStage.NEW, nullable=False)
    efactor = Column(Float, default=2.5, nullable=False)
    interval_days = Column(Integer, default=0, nullable=False)
    repetitions = Column(Integer, default=0, nullable=False)

    last_reviewed_at = Column(DateTime(timezone=True))
    next_review_at = Column(DateTime(timezone=True))
    streak = Column(Integer, default=0)

    user_notes = Column(Text)
    user_translation = Column(String(500))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    word = relationship("Word", lazy="joined")
    user = relationship("User", back_populates="user_words", lazy="joined")




# =====================================
#  REVIEW HISTORY
# =====================================
class UserWordHistory(Base):
    __tablename__ = "user_word_history"

    id = Column(Integer, primary_key=True)

    user_word_id = Column(Integer, ForeignKey("user_words.id", ondelete="CASCADE"), nullable=False)

    attempted_at = Column(DateTime(timezone=True), server_default=func.now())

    outcome = Column(String(50))   # correct / wrong / partial
    response = Column(JSON)
    points = Column(Integer)
    meta = Column(JSON)

    user_word = relationship("UserWord", lazy="joined")
