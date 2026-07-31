import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base
from backend.app.models.course import Course, Lesson
from backend.app.models.document import LearningDocument, DocumentVersion, ContentChunk
from backend.app.models.flashcard import Flashcard
from backend.app.services.model_gateway import ModelGateway, MockTextProvider
from backend.app.services.flashcard_generation import (
    FlashcardItemSchema, FlashcardListSchema,
    FlashcardPromptTemplate, FlashcardDeduplicator, FlashcardValidator,
    FlashcardRepository, FlashcardGeneratorService, FlashcardWorkerHandler
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

def test_prompt_template_building():
    chunk = ContentChunk(
        id="chk-text",
        document_version_id="ver-1",
        text_content="Gradient Descent là thuật toán tối ưu hóa loss function.",
        has_formulas=True,
        has_code=True,
        metadata_json={"title": "Tối ưu hóa", "source_references": ["Slide 15"]}
    )

    prompt = FlashcardPromptTemplate.build_prompt(chunk, {"Gradient Descent": "Optimization"})
    assert "Gradient Descent" in prompt
    assert "Slide 15" in prompt
    assert "VỚI CÔNG THỨC TOÁN HỌC" in prompt
    assert "VỚI ĐOẠN MÃ NGUỒN" in prompt

def test_deduplication_and_quality_validation():
    cards = [
        FlashcardItemSchema(
            type="concept",
            front="Gradient Descent là gì?",
            back="Là thuật toán tối ưu.",
            explanation="Giải thích...",
            source_references=["Slide 15"],
            quality_score=0.85
        ),
        # Duplicate front text
        FlashcardItemSchema(
            type="concept",
            front="gradient descent là gì?",
            back="Thuật toán giảm loss.",
            explanation="Giải thích...",
            source_references=["Slide 15"],
            quality_score=0.80
        ),
        # Card with low quality score (< 0.70) -> Should be filtered out
        FlashcardItemSchema(
            type="definition",
            front="Loss function là gì?",
            back="Hàm đo sai số.",
            explanation="...",
            source_references=["Slide 15"],
            quality_score=0.50
        ),
        # Card missing source_references -> Should be filtered out
        FlashcardItemSchema(
            type="definition",
            front="Overfitting là gì?",
            back="Quá khớp dữ liệu.",
            explanation="...",
            source_references=[],
            quality_score=0.90
        )
    ]

    protected = {"Gradient Descent": "Opt"}
    valid_cards = FlashcardValidator.validate_and_filter(cards, protected)
    assert len(valid_cards) == 2  # Low quality and missing source cards filtered

    unique_cards = FlashcardDeduplicator.filter_duplicates(valid_cards)
    assert len(unique_cards) == 1  # Duplicate card filtered out
    assert unique_cards[0].front == "Gradient Descent là gì?"

@pytest.mark.asyncio
async def test_integration_generator_service_and_worker_handler():
    db = TestingSessionLocal()
    course = Course(id="c-fc", code="AI202", title="Machine Learning")
    doc = LearningDocument(id="doc-fc", course_id="c-fc", title="lecture.pdf", file_type="application/pdf", file_path="lecture.pdf")
    doc_ver = DocumentVersion(id="docver-fc", document_id="doc-fc", version_number=1, file_path="lecture.pdf")
    chunk = ContentChunk(
        id="chk-fc",
        document_version_id="docver-fc",
        chunk_index=1,
        text_content="Overfitting xảy ra khi mô hình học quá kỹ dữ liệu huấn luyện.",
        has_formulas=False,
        has_code=False,
        metadata_json={"title": "Overfitting", "source_references": ["Page 8"], "lesson_id": "les-10"}
    )
    db.add_all([course, doc, doc_ver, chunk])
    db.commit()

    # Mock Model Gateway Structured Output Response
    mock_json = {
        "flashcards": [
            {
                "type": "concept",
                "front": "Khi nào xảy ra hiện tượng Overfitting?",
                "back": "Khi mô hình học quá sát dữ liệu huấn luyện.",
                "explanation": "Dẫn đến khả năng tổng quát hóa kém trên dữ liệu mới.",
                "difficulty": "MEDIUM",
                "blooms_level": "Understand",
                "tags": ["Machine Learning", "Overfitting"],
                "glossary_terms": ["Overfitting"],
                "source_references": ["Page 8"],
                "quality_score": 0.92
            }
        ]
    }
    
    mock_response_obj = FlashcardListSchema(**mock_json)
    mock_provider = MockTextProvider(custom_structured_response=mock_response_obj)
    gateway = ModelGateway(text_provider=mock_provider)

    generator = FlashcardGeneratorService(gateway=gateway, db=db)
    handler = FlashcardWorkerHandler(db=db, generator_service=generator)

    res = await handler.process_chunk(chunk)

    assert res["chunk_id"] == "chk-fc"
    assert res["flashcards_generated_count"] == 1

    # Verify DB persistence via FlashcardRepository
    saved_cards = db.query(Flashcard).filter(Flashcard.content_chunk_id == "chk-fc").all()
    assert len(saved_cards) == 1
    assert saved_cards[0].content_chunk_id == "chk-fc"
    assert "Overfitting" in saved_cards[0].question
    assert saved_cards[0].options_json["quality_score"] == 0.92

    db.close()
