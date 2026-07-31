from typing import List, Optional
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.mindmap import node_flashcard_association
from backend.app.schemas.enums import DifficultyLevel

class Flashcard(Base):
    __tablename__ = "flashcards"

    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True, index=True)
    content_chunk_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("content_chunks.id", ondelete="SET NULL"), nullable=True, index=True)

    question: Mapped[str] = mapped_column(String(1000), nullable=False)
    answer: Mapped[str] = mapped_column(String(2000), nullable=False)
    options_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List/dict of MCQ choices
    difficulty: Mapped[str] = mapped_column(String(20), default=DifficultyLevel.MEDIUM.value, nullable=False)
    tags_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    content_chunk: Mapped[Optional["ContentChunk"]] = relationship("ContentChunk", back_populates="flashcards")
    mindmap_nodes: Mapped[List["MindmapNode"]] = relationship("MindmapNode", secondary=node_flashcard_association, back_populates="flashcards")
    attempts: Mapped[List["FlashcardAttempt"]] = relationship("FlashcardAttempt", back_populates="flashcard", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_flashcards_course_lesson", "course_id", "lesson_id"),
    )

class FlashcardAttempt(Base):
    __tablename__ = "flashcard_attempts"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    flashcard_id: Mapped[str] = mapped_column(String(36), ForeignKey("flashcards.id", ondelete="CASCADE"), nullable=False, index=True)
    
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    selected_option: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attempted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="flashcard_attempts")
    flashcard: Mapped["Flashcard"] = relationship("Flashcard", back_populates="attempts")

    __table_args__ = (
        Index("ix_attempts_user_card", "user_id", "flashcard_id"),
    )
