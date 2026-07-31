import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base
from backend.app.models.user import User
from backend.app.models.course import Course
from backend.app.services.model_gateway import ModelGateway, MockEmbeddingProvider
from backend.app.services.vector_retrieval import (
    VectorEmbeddingService, InProcessVectorStore, HybridRetrievalService,
    SimpleScoreReranker, AccessDeniedException, VectorDocumentPayload
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

@pytest.mark.asyncio
async def test_embedding_all_6_target_entities():
    mock_embed = MockEmbeddingProvider()
    gateway = ModelGateway(embedding_provider=mock_embed)
    service = VectorEmbeddingService(gateway=gateway, model_version="text-embedding-v1")

    # 1. ContentChunk
    payload_chunk = await service.build_payload_for_entity("ContentChunk", "chk-1", "Chunk text", "c-1", content_type="paragraph")
    # 2. MindmapNode
    payload_node = await service.build_payload_for_entity("MindmapNode", "n-1", "Node summary", "c-1", content_type="heading")
    # 3. Flashcard
    payload_fc = await service.build_payload_for_entity("Flashcard", "fc-1", "Flashcard Q&A", "c-1", content_type="flashcard")
    # 4. GlossaryTerm
    payload_gt = await service.build_payload_for_entity("GlossaryTerm", "gt-1", "Glossary definition", "c-1", content_type="glossary")
    # 5. Formula
    payload_form = await service.build_payload_for_entity("Formula", "fm-1", "Formula explanation", "c-1", content_type="formula")
    # 6. Code
    payload_code = await service.build_payload_for_entity("Code", "cd-1", "Code explanation", "c-1", content_type="code")

    for p in [payload_chunk, payload_node, payload_fc, payload_gt, payload_form, payload_code]:
        assert p.embedding_model_version == "text-embedding-v1"
        assert len(p.vector) > 0

@pytest.mark.asyncio
async def test_cross_course_isolation():
    db = TestingSessionLocal()

    # User only has access to "course-A"
    user = User(id="usr-iso", email="iso@test.com", full_name="Iso User", access_scope="course-A")
    course_a = Course(id="course-A", code="CS101", title="Course A")
    course_b = Course(id="course-B", code="CS102", title="Course B")

    db.add_all([user, course_a, course_b])
    db.commit()

    mock_embed = MockEmbeddingProvider()
    gateway = ModelGateway(embedding_provider=mock_embed)
    embed_service = VectorEmbeddingService(gateway=gateway)
    retrieval_service = HybridRetrievalService(db=db, embedding_service=embed_service)

    # User attempts to query course-B (unauthorized course)
    with pytest.raises(AccessDeniedException):
        await retrieval_service.search("Query text", user_id="usr-iso", course_id="course-B")

    db.close()

@pytest.mark.asyncio
async def test_metadata_filtering_and_embedding_version_isolation():
    db = TestingSessionLocal()
    user = User(id="usr-meta", email="meta@test.com", full_name="Meta User", access_scope="ALL")
    course = Course(id="c-meta", code="CS103", title="Meta Course")

    db.add_all([user, course])
    db.commit()

    store = InProcessVectorStore()

    # Document 1 (v1 model, lesson-01, paragraph)
    p1 = VectorDocumentPayload(
        id="p1", entity_type="ContentChunk", entity_id="chk-1",
        text_content="Gradient Descent Optimization", vector=[0.1] * 128,
        embedding_model_version="v1", course_id="c-meta", lesson_id="lesson-01", content_type="paragraph"
    )
    # Document 2 (v2 model - DIFFERENT VERSION, lesson-01, paragraph)
    p2 = VectorDocumentPayload(
        id="p2", entity_type="ContentChunk", entity_id="chk-2",
        text_content="Gradient Descent Optimization V2", vector=[0.1] * 128,
        embedding_model_version="v2", course_id="c-meta", lesson_id="lesson-01", content_type="paragraph"
    )
    # Document 3 (v1 model, lesson-02 - DIFFERENT LESSON, paragraph)
    p3 = VectorDocumentPayload(
        id="p3", entity_type="ContentChunk", entity_id="chk-3",
        text_content="Gradient Descent Lesson 02", vector=[0.1] * 128,
        embedding_model_version="v1", course_id="c-meta", lesson_id="lesson-02", content_type="paragraph"
    )

    store.upsert(p1)
    store.upsert(p2)
    store.upsert(p3)

    mock_embed = MockEmbeddingProvider()
    gateway = ModelGateway(embedding_provider=mock_embed)
    embed_service = VectorEmbeddingService(gateway=gateway, model_version="v1")
    retrieval_service = HybridRetrievalService(db=db, embedding_service=embed_service, vector_store=store, min_relevance_threshold=0.0)

    # Search with lesson_id="lesson-01" and model_version="v1"
    results = await retrieval_service.search(
        query="Gradient Descent", user_id="usr-meta", course_id="c-meta", lesson_id="lesson-01"
    )

    # Must only match p1 (p2 has different model_version 'v2', p3 has different lesson_id 'lesson-02')
    assert len(results) == 1
    assert results[0].entity_id == "chk-1"

    db.close()

@pytest.mark.asyncio
async def test_minimum_relevance_threshold_returns_empty():
    db = TestingSessionLocal()
    user = User(id="usr-thresh", email="thresh@test.com", full_name="Thresh User", access_scope="ALL")
    course = Course(id="c-thresh", code="CS104", title="Thresh Course")

    db.add_all([user, course])
    db.commit()

    store = InProcessVectorStore()
    # Unrelated document
    p_weak = VectorDocumentPayload(
        id="p-weak", entity_type="ContentChunk", entity_id="chk-weak",
        text_content="Lịch sử CNTT 1980", vector=[0.0] * 128,
        embedding_model_version="v1", course_id="c-thresh", content_type="paragraph"
    )
    store.upsert(p_weak)

    mock_embed = MockEmbeddingProvider()
    gateway = ModelGateway(embedding_provider=mock_embed)
    embed_service = VectorEmbeddingService(gateway=gateway, model_version="v1")
    
    # High relevance threshold = 0.80
    retrieval_service = HybridRetrievalService(
        db=db, embedding_service=embed_service, vector_store=store, min_relevance_threshold=0.80
    )

    results = await retrieval_service.search(
        query="Gradient Descent Optimization", user_id="usr-thresh", course_id="c-thresh"
    )

    # Req 12: Low relevance result filtered out -> Returns empty context instead of weak data!
    assert len(results) == 0

    db.close()
