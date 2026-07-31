from typing import List, Optional
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class LearningDocument(Base):
    __tablename__ = "learning_documents"

    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, slide, transcript
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="documents")
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson", back_populates="documents")
    versions: Mapped[List["DocumentVersion"]] = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("learning_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    changelog: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    document: Mapped["LearningDocument"] = relationship("LearningDocument", back_populates="versions")
    content_blocks: Mapped[List["ContentBlock"]] = relationship("ContentBlock", back_populates="document_version", cascade="all, delete-orphan")
    content_chunks: Mapped[List["ContentChunk"]] = relationship("ContentChunk", back_populates="document_version", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_doc_version_doc_num", "document_id", "version_number", unique=True),
    )

class ContentBlock(Base):
    __tablename__ = "content_blocks"

    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("learning_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True, index=True)
    
    block_type: Mapped[str] = mapped_column(String(50), nullable=False)  # heading, paragraph, list, table, formula, code, image, diagram, note
    raw_content: Mapped[str] = mapped_column(String(10000), nullable=False)
    normalized_content: Mapped[str] = mapped_column(String(10000), nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="vi", nullable=False)
    
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    slide_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extraction_confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    document_version: Mapped["DocumentVersion"] = relationship("DocumentVersion", back_populates="content_blocks")

    __table_args__ = (
        Index("ix_blocks_docver_seq", "document_version_id", "sequence_number"),
    )

class ContentChunk(Base):
    __tablename__ = "content_chunks"

    document_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text_content: Mapped[str] = mapped_column(String(10000), nullable=False)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    has_formulas: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_code: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    page_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    document_version: Mapped["DocumentVersion"] = relationship("DocumentVersion", back_populates="content_chunks")
    flashcards: Mapped[List["Flashcard"]] = relationship("Flashcard", back_populates="content_chunk")

    __table_args__ = (
        Index("ix_chunks_docver_index", "document_version_id", "chunk_index"),
    )

class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"

    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    term: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    definition: Mapped[str] = mapped_column(String(2000), nullable=False)
    domain_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_slide: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_protected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="glossary_terms")

    __table_args__ = (
        Index("ix_glossary_course_term", "course_id", "term", unique=True),
    )
