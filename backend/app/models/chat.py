from typing import List, Optional
from sqlalchemy import String, Float, Integer, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.schemas.enums import MessageRole

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="Tutor Chat Session", nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_chat_sessions_user_course", "user_id", "course_id"),
    )

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), default=MessageRole.USER.value, nullable=False)
    content: Mapped[str] = mapped_column(String(5000), nullable=False)
    retrieval_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Retrieval scores, top_k, prompt tokens, model info

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
    citations: Mapped[List["SourceReference"]] = relationship("SourceReference", back_populates="message", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_chat_messages_session_role", "session_id", "role"),
    )

class SourceReference(Base):
    __tablename__ = "source_references"

    chat_message_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("learning_documents.id", ondelete="SET NULL"), nullable=True)
    document_version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True)
    content_chunk_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("content_chunks.id", ondelete="SET NULL"), nullable=True)

    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    slide_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    snippet_text: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    message: Mapped["ChatMessage"] = relationship("ChatMessage", back_populates="citations")

    __table_args__ = (
        Index("ix_source_refs_msg_doc", "chat_message_id", "document_id"),
    )
