from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.schemas.enums import JobStatus, TaskStatus

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    course_id: Mapped[str] = mapped_column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    status: Mapped[str] = mapped_column(String(50), default=JobStatus.PENDING.value, nullable=False, index=True)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    last_completed_step: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    checkpoint_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Relationships
    tasks: Mapped[List["ProcessingTask"]] = relationship("ProcessingTask", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_jobs_course_status", "course_id", "status"),
    )

class ProcessingTask(Base):
    __tablename__ = "processing_tasks"

    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=TaskStatus.PENDING.value, nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    input_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_details: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Relationships
    job: Mapped["ProcessingJob"] = relationship("ProcessingJob", back_populates="tasks")

    __table_args__ = (
        Index("ix_tasks_job_order", "job_id", "step_order"),
    )
