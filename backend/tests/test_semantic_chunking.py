import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base
from backend.app.models.course import Course, Lesson
from backend.app.models.document import LearningDocument, DocumentVersion, ContentBlock, ContentChunk, GlossaryTerm
from backend.app.models.job import ProcessingJob
from backend.app.schemas.enums import JobStatus
from backend.app.services.semantic_chunking import (
    SemanticChunker, SemanticChunkData, SemanticChunkingPipeline
)

TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_test_environment():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_atomic_formula_and_code_grouping():
    blocks = [
        ContentBlock(id="b1", block_type="heading", normalized_content="Phần 1: Cost of Error", sequence_number=1),
        ContentBlock(id="b2", block_type="paragraph", normalized_content="Phương trình Loss Function được định nghĩa như sau:", sequence_number=2),
        ContentBlock(id="b3", block_type="formula", normalized_content="$$ L(\\theta) = \\sum (y_i - f(x_i))^2 $$", sequence_number=3),
        ContentBlock(id="b4", block_type="paragraph", normalized_content="Trong đó theta là trọng số mô hình.", sequence_number=4),
        ContentBlock(id="b5", block_type="code", normalized_content="def compute_loss(y_true, y_pred):\n    return np.mean((y_true - y_pred)**2)", sequence_number=5),
        ContentBlock(id="b6", block_type="paragraph", normalized_content="Hàm trên dùng để tính giá trị loss.", sequence_number=6)
    ]

    chunker = SemanticChunker(max_tokens=300)
    chunks = chunker.chunk_blocks(blocks, "doc-1", "docver-1")

    assert len(chunks) == 1
    chunk = chunks[0]
    # Verify formula and code are grouped atomically with surrounding text
    assert "Loss Function" in chunk.content
    assert "\\sum" in chunk.content
    assert "compute_loss" in chunk.content
    assert "formula" in chunk.content_types
    assert "code" in chunk.content_types

def test_lesson_boundary_isolation():
    # Blocks belonging to two different lessons
    blocks = [
        ContentBlock(id="b1", lesson_id="lesson-01", block_type="heading", normalized_content="Day 01: Basics", sequence_number=1),
        ContentBlock(id="b2", lesson_id="lesson-01", block_type="paragraph", normalized_content="Content Day 01", sequence_number=2),
        ContentBlock(id="b3", lesson_id="lesson-02", block_type="heading", normalized_content="Day 02: Advanced", sequence_number=3),
        ContentBlock(id="b4", lesson_id="lesson-02", block_type="paragraph", normalized_content="Content Day 02", sequence_number=4)
    ]

    chunker = SemanticChunker(max_tokens=300)
    chunks = chunker.chunk_blocks(blocks, "doc-1", "docver-1")

    # Must produce AT LEAST 2 chunks (Never mix content from different lessons!)
    assert len(chunks) >= 2
    l1_chunks = [c for c in chunks if c.lesson_id == "lesson-01"]
    l2_chunks = [c for c in chunks if c.lesson_id == "lesson-02"]
    
    assert len(l1_chunks) > 0
    assert len(l2_chunks) > 0
    assert "Day 02" not in l1_chunks[0].content

def test_very_long_document_chunking():
    # Generate 120 blocks to test large document splitting with token bounds
    blocks = []
    for i in range(1, 121):
        btype = "heading" if i % 10 == 1 else ("code" if i % 10 == 5 else "paragraph")
        blocks.append(
            ContentBlock(
                id=f"b-{i}",
                block_type=btype,
                normalized_content=f"Đoạn văn bản bài giảng số {i} với nội dung chi tiết để kiểm tra khả năng chia nhỏ chunk lớn mà không bị vượt token limit.",
                sequence_number=i
            )
        )

    chunker = SemanticChunker(max_tokens=150)
    chunks = chunker.chunk_blocks(blocks, "doc-long", "docver-long")

    assert len(chunks) > 5
    for c in chunks:
        assert c.token_estimate <= 200  # Token limit enforced
        assert c.checksum != ""

@pytest.mark.asyncio
async def test_pipeline_execution_and_idempotency():
    db = TestingSessionLocal()
    
    course = Course(id="c-sem", code="COMP2010", title="AI Thực Chiến")
    gt = GlossaryTerm(course_id="c-sem", term="Gradient Descent", definition="Thuật toán tối ưu")
    doc = LearningDocument(id="doc-sem", course_id="c-sem", title="slide.pdf", file_type="application/pdf", file_path="slide.pdf")
    doc_ver = DocumentVersion(id="docver-sem", document_id="doc-sem", version_number=1, file_path="slide.pdf")
    job = ProcessingJob(id="job-sem", course_id="c-sem", document_version_id="docver-sem", status="PENDING")

    db.add_all([course, gt, doc, doc_ver, job])
    db.commit()

    b1 = ContentBlock(document_id="doc-sem", document_version_id="docver-sem", block_type="heading", raw_content="Gradient Descent Optimization", normalized_content="Gradient Descent Optimization", sequence_number=1)
    b2 = ContentBlock(document_id="doc-sem", document_version_id="docver-sem", block_type="paragraph", raw_content="Thuật toán Gradient Descent giúp tối ưu loss function.", normalized_content="Thuật toán Gradient Descent giúp tối ưu loss function.", sequence_number=2)
    db.add_all([b1, b2])
    db.commit()

    pipeline = SemanticChunkingPipeline(db=db)

    # 1st Run
    chunks1 = await pipeline.execute_for_version("docver-sem")
    assert len(chunks1) > 0
    
    db.refresh(job)
    assert job.status == JobStatus.PROCESSING.value or job.status == "processing"
    assert job.progress_percentage == 50
    assert job.last_completed_step == "semantic_chunking"

    # Verify glossary term matched in chunk metadata
    first_chunk_meta = chunks1[0].metadata_json
    assert "Gradient Descent" in first_chunk_meta["glossary_terms"]

    # 2nd Run (Idempotency check)
    chunks2 = await pipeline.execute_for_version("docver-sem")
    
    db_count = db.query(ContentChunk).filter(ContentChunk.document_version_id == "docver-sem").count()
    assert db_count == len(chunks1)

    db.close()
