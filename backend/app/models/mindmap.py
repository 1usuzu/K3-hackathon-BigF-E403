from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, JSON, Table, Column, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

# Junction table NodeFlashcard (Many-to-Many between MindmapNode and Flashcard)
node_flashcard_association = Table(
    "node_flashcards",
    Base.metadata,
    Column("node_id", String(36), ForeignKey("mindmap_nodes.id", ondelete="CASCADE"), primary_key=True),
    Column("flashcard_id", String(36), ForeignKey("flashcards.id", ondelete="CASCADE"), primary_key=True),
)

class Mindmap(Base):
    __tablename__ = "mindmaps"

    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True, index=True)
    document_version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    root_node_stable_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson", back_populates="mindmaps")
    nodes: Mapped[List["MindmapNode"]] = relationship("MindmapNode", back_populates="mindmap", cascade="all, delete-orphan")

class MindmapNode(Base):
    __tablename__ = "mindmap_nodes"

    mindmap_id: Mapped[str] = mapped_column(String(36), ForeignKey("mindmaps.id", ondelete="CASCADE"), nullable=False, index=True)
    node_stable_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # Stable ID string, e.g. "node-day02-part1"
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_node_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("mindmap_nodes.id", ondelete="CASCADE"), nullable=True, index=True)
    
    slide_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    mindmap: Mapped["Mindmap"] = relationship("Mindmap", back_populates="nodes")
    parent_node: Mapped[Optional["MindmapNode"]] = relationship("MindmapNode", remote_side="MindmapNode.id", back_populates="child_nodes")
    child_nodes: Mapped[List["MindmapNode"]] = relationship("MindmapNode", back_populates="parent_node", cascade="all, delete-orphan")
    
    flashcards: Mapped[List["Flashcard"]] = relationship("Flashcard", secondary=node_flashcard_association, back_populates="mindmap_nodes")

    __table_args__ = (
        Index("ix_nodes_mindmap_stable", "mindmap_id", "node_stable_id"),
        Index("ix_nodes_parent_order", "parent_node_id", "order_index"),
    )
