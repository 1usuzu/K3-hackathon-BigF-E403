import pytest
import os
import shutil
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base
from backend.app.main import app
from backend.app.api.v1.documents import get_db
from backend.app.models.user import User
from backend.app.models.course import Course, Lesson
from backend.app.models.job import ProcessingJob
from backend.app.schemas.enums import JobStatus
from backend.app.services.storage.local_storage import LocalStorageProvider
from backend.app.services.document_ingestion.validator import FileValidator

TEST_DB_URL = "sqlite:///:memory:"
TEST_UPLOAD_DIR = "./test_uploads"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_test_db_and_storage():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Clear existing if any
    db.query(ProcessingJob).delete()
    db.query(Lesson).delete()
    db.query(Course).delete()
    db.query(User).delete()
    db.commit()

    # Create test Course and User
    course = Course(id="course-101", code="COMP2010", title="AI Thực Chiến", tenant_id="tenant-1")
    lesson = Lesson(id="lesson-01", course_id="course-101", title="Day 01", order_index=1)
    user_authorized = User(id="user-auth", email="student@vlearn.edu", full_name="Học Viên Valid", tenant_id="tenant-1")
    user_unauthorized = User(id="user-unauth", email="hacker@other.edu", full_name="Học Viên Hack", tenant_id="tenant-2")

    db.add_all([course, lesson, user_authorized, user_unauthorized])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR)

client = TestClient(app)

def test_valid_pdf_upload():
    pdf_bytes = b"%PDF-1.5 Fake PDF content for testing document ingestion."
    
    response = client.post(
        "/api/v1/documents/upload",
        data={
            "course_id": "course-101",
            "user_id": "user-auth",
            "lesson_id": "lesson-01"
        },
        files={"file": ("sample_lecture.pdf", pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["document_id"] is not None
    assert data["course_id"] == "course-101"
    assert data["mime_type"] == "application/pdf"
    assert data["processing_status"] == JobStatus.PENDING.value or data["processing_status"] == "pending"
    assert data["is_duplicate"] is False

def test_valid_markdown_and_txt_uploads():
    md_bytes = "# Day 02 Lecture Notes\nContent for AI Learning Agent".encode("utf-8")
    
    response = client.post(
        "/api/v1/documents/upload",
        data={"course_id": "course-101", "user_id": "user-auth"},
        files={"file": ("notes.md", md_bytes, "text/markdown")}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["mime_type"] == "text/markdown"

def test_invalid_file_format_and_extension_spoofing():
    fake_exe_bytes = b"MZExecutableContentHere"
    
    response = client.post(
        "/api/v1/documents/upload",
        data={"course_id": "course-101", "user_id": "user-auth"},
        files={"file": ("malicious.pdf", fake_exe_bytes, "application/pdf")}
    )

    assert response.status_code == 400
    assert "Executable or binary script file signature detected" in response.json()["detail"]

def test_file_too_large():
    big_bytes = b"%PDF-1.5 " + (b"X" * (100 * 1024))
    
    with pytest.raises(Exception) as exc_info:
        FileValidator.validate(big_bytes, "big.pdf", max_size_bytes=50 * 1024)
    assert "exceeds max limit" in str(exc_info.value)

def test_duplicate_file_upload_idempotency():
    pdf_bytes = b"%PDF-1.5 Duplicate test content"

    res1 = client.post(
        "/api/v1/documents/upload",
        data={"course_id": "course-101", "user_id": "user-auth"},
        files={"file": ("slide_v1.pdf", pdf_bytes, "application/pdf")}
    )
    assert res1.status_code == 201
    data1 = res1.json()

    res2 = client.post(
        "/api/v1/documents/upload",
        data={"course_id": "course-101", "user_id": "user-auth"},
        files={"file": ("slide_v1_copy.pdf", pdf_bytes, "application/pdf")}
    )
    assert res2.status_code == 201
    data2 = res2.json()

    assert data2["document_id"] == data1["document_id"]
    assert data2["is_duplicate"] is True

def test_unauthorized_course_access():
    pdf_bytes = b"%PDF-1.5 Content"

    response = client.post(
        "/api/v1/documents/upload",
        data={"course_id": "course-101", "user_id": "user-unauth"},
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

def test_path_traversal_filename_sanitization():
    sanitized = FileValidator.sanitize_filename("../../../etc/passwd_script.pdf")
    assert sanitized == "passwd_script.pdf"
    assert ".." not in sanitized
    assert "/" not in sanitized
