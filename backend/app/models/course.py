from typing import List, Optional
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class Course(Base):
    __tablename__ = "courses"

    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    # Relationships
    lessons: Mapped[List["Lesson"]] = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    documents: Mapped[List["LearningDocument"]] = relationship("LearningDocument", back_populates="course", cascade="all, delete-orphan")
    glossary_terms: Mapped[List["GlossaryTerm"]] = relationship("GlossaryTerm", back_populates="course", cascade="all, delete-orphan")

class Lesson(Base):
    __tablename__ = "lessons"

    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="lessons")
    documents: Mapped[List["LearningDocument"]] = relationship("LearningDocument", back_populates="lesson")
    mindmaps: Mapped[List["Mindmap"]] = relationship("Mindmap", back_populates="lesson")

    __table_args__ = (
        Index("ix_lessons_course_order", "course_id", "order_index"),
    )

class LearningProgress(Base):
    __tablename__ = "learning_progress"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=True, index=True)
    mindmap_node_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("mindmap_nodes.id", ondelete="SET NULL"), nullable=True, index=True)

    completed_flashcards_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_flashcards_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mastery_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_studied_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="progress_records")

    __table_args__ = (
        Index("ix_progress_user_course", "user_id", "course_id"),
        Index("ix_progress_user_lesson", "user_id", "lesson_id"),
    )
