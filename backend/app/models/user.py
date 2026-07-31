from typing import List, Optional
from sqlalchemy import String, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    access_scope: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    progress_records: Mapped[List["LearningProgress"]] = relationship("LearningProgress", back_populates="user", cascade="all, delete-orphan")
    flashcard_attempts: Mapped[List["FlashcardAttempt"]] = relationship("FlashcardAttempt", back_populates="user", cascade="all, delete-orphan")
    chat_sessions: Mapped[List["ChatSession"]] = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_users_tenant_email", "tenant_id", "email"),
    )
