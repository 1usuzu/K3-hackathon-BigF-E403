from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.services.document_ingestion import (
    DocumentIngestionService, FileValidator,
    InvalidFileFormatException, FileTooLargeException, DangerousFileContentException,
    UnauthorizedCourseAccessException, CourseNotFoundException
)

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    course_id: str = Form(...),
    user_id: str = Form(...),
    lesson_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        file_bytes = await file.read()
        service = DocumentIngestionService(db=db)
        
        result = await service.ingest_document(
            file_bytes=file_bytes,
            filename=file.filename or "unnamed_file",
            course_id=course_id,
            user_id=user_id,
            lesson_id=lesson_id
        )
        return result
    except (InvalidFileFormatException, DangerousFileContentException, FileTooLargeException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UnauthorizedCourseAccessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CourseNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Upload Error: {str(e)}")
