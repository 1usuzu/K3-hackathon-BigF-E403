import os
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.course import Course, Lesson
from backend.app.models.document import LearningDocument, DocumentVersion
from backend.app.models.job import ProcessingJob
from backend.app.schemas.enums import JobStatus
from backend.app.services.storage import StorageProvider, LocalStorageProvider
from backend.app.services.document_ingestion.validator import FileValidator

class UnauthorizedCourseAccessException(Exception):
    pass

class CourseNotFoundException(Exception):
    pass

class DocumentIngestionService:
    def __init__(self, db: Session, storage: Optional[StorageProvider] = None):
        self.db = db
        self.storage = storage or LocalStorageProvider()

    def _verify_user_course_access(self, user_id: str, course_id: str):
        # Verify Course exists
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise CourseNotFoundException(f"Course '{course_id}' not found.")

        # Verify User access
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UnauthorizedCourseAccessException(f"User '{user_id}' not found or unauthorized.")

        # Security check: tenant/course scope verification
        if user.tenant_id and course.tenant_id and user.tenant_id != course.tenant_id:
            raise UnauthorizedCourseAccessException("Access denied: Tenant mismatch.")

        if user.access_scope and "allowed_courses" in user.access_scope:
            allowed = user.access_scope.get("allowed_courses", [])
            if course_id not in allowed and "*" not in allowed:
                raise UnauthorizedCourseAccessException(f"User '{user_id}' does not have access to course '{course_id}'.")

    async def ingest_document(
        self,
        file_bytes: bytes,
        filename: str,
        course_id: str,
        user_id: str,
        lesson_id: Optional[str] = None,
        security_level: str = "INTERNAL_STUDENT_ONLY"
    ) -> Dict[str, Any]:
        # 1. Verify User Access Control (Req 12)
        self._verify_user_course_access(user_id, course_id)

        # 2. Validate file signature, extension, size, and sanitize filename (Req 1, 2, 3, 4, 5, 6)
        sanitized_filename, mime_type = FileValidator.validate(file_bytes, filename)
        checksum = FileValidator.compute_sha256(file_bytes)
        file_size = len(file_bytes)

        # 3. Check for Duplicate Uploads by checksum (Req 11: Idempotency)
        existing_doc = self.db.query(LearningDocument).filter(
            LearningDocument.course_id == course_id,
            LearningDocument.checksum == checksum
        ).first()

        if existing_doc:
            active_ver = self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == existing_doc.id,
                DocumentVersion.is_active == True
            ).first()
            existing_job = self.db.query(ProcessingJob).filter(
                ProcessingJob.course_id == course_id,
                ProcessingJob.document_version_id == active_ver.id if active_ver else None
            ).first()
            
            return {
                "document_id": existing_doc.id,
                "course_id": existing_doc.course_id,
                "lesson_id": existing_doc.lesson_id,
                "original_filename": existing_doc.title,
                "mime_type": existing_doc.file_type,
                "file_size": file_size,
                "checksum": existing_doc.checksum,
                "storage_path": existing_doc.file_path,
                "security_level": security_level,
                "processing_status": existing_job.status if existing_job else JobStatus.COMPLETED.value,
                "document_version": active_ver.version_number if active_ver else 1,
                "is_duplicate": True
            }

        # 4. Save file via Storage Abstraction (Req 7, 8, 9)
        storage_rel_path = f"courses/{course_id}/docs/{checksum[:12]}_{sanitized_filename}"
        saved_storage_path = await self.storage.save_file(file_bytes, storage_rel_path)

        # 5. Save Document & Version to DB
        doc = LearningDocument(
            course_id=course_id,
            lesson_id=lesson_id,
            title=sanitized_filename,
            file_type=mime_type,
            file_path=saved_storage_path,
            checksum=checksum
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        doc_version = DocumentVersion(
            document_id=doc.id,
            version_number=1,
            changelog="Initial document upload",
            file_path=saved_storage_path,
            is_active=True
        )
        self.db.add(doc_version)
        self.db.commit()
        self.db.refresh(doc_version)

        # 6. Create ProcessingJob (Req 10)
        job = ProcessingJob(
            course_id=course_id,
            document_version_id=doc_version.id,
            status=JobStatus.PENDING.value,
            progress_percentage=0,
            retry_count=0,
            max_retries=3
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return {
            "document_id": doc.id,
            "course_id": doc.course_id,
            "lesson_id": doc.lesson_id,
            "original_filename": doc.title,
            "mime_type": doc.file_type,
            "file_size": file_size,
            "checksum": doc.checksum,
            "storage_path": doc.file_path,
            "security_level": security_level,
            "processing_status": job.status,
            "document_version": doc_version.version_number,
            "is_duplicate": False
        }
