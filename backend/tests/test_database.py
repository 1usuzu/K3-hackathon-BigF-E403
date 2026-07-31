import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.models import (
    User, Course, Lesson, LearningDocument, DocumentVersion,
    ContentBlock, ContentChunk, ProcessingJob, ProcessingTask,
    Flashcard, FlashcardAttempt, Mindmap, MindmapNode,
    LearningProgress, GlossaryTerm, ChatSession, ChatMessage,
    SourceReference, ModelConfiguration
)
from backend.app.schemas.enums import JobStatus, DeploymentMode, DifficultyLevel

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_all_20_tables_exist(db_session):
    engine = db_session.get_bind()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = [
        "users", "courses", "lessons", "learning_documents", "document_versions",
        "content_blocks", "content_chunks", "processing_jobs", "processing_tasks",
        "flashcards", "flashcard_attempts", "mindmaps", "mindmap_nodes",
        "node_flashcards", "learning_progress", "glossary_terms", "chat_sessions",
        "chat_messages", "source_references", "model_configurations"
    ]
    for table in expected_tables:
        assert table in tables, f"Table '{table}' missing in schema"

def test_stable_node_id_and_multi_node_flashcard(db_session):
    # Create course, lesson, mindmap
    course = Course(code="COMP2010", title="AI Thực Chiến")
    db_session.add(course)
    db_session.commit()

    lesson = Lesson(course_id=course.id, title="Day 02: Xác định bài toán AI", order_index=2)
    db_session.add(lesson)
    db_session.commit()

    mindmap = Mindmap(course_id=course.id, lesson_id=lesson.id, title="Mindmap Day 02")
    db_session.add(mindmap)
    db_session.commit()

    # Stable Node IDs
    node1 = MindmapNode(mindmap_id=mindmap.id, node_stable_id="node-day02-part1", label="Phần 1: JTBD")
    node2 = MindmapNode(mindmap_id=mindmap.id, node_stable_id="node-day02-part2", label="Phần 2: 5 Tiêu chí")
    db_session.add_all([node1, node2])
    db_session.commit()

    # Single flashcard linked to MULTIPLE nodes (Requirement 6)
    flashcard = Flashcard(
        course_id=course.id,
        lesson_id=lesson.id,
        question="Cost of error lớn nhất là gì?",
        answer="False Negative",
        difficulty=DifficultyLevel.HARD.value
    )
    flashcard.mindmap_nodes.extend([node1, node2])
    db_session.add(flashcard)
    db_session.commit()

    # Refresh & verify association
    db_session.refresh(node1)
    db_session.refresh(node2)
    assert len(node1.flashcards) == 1
    assert len(node2.flashcards) == 1
    assert node1.flashcards[0].id == flashcard.id
    assert node2.flashcards[0].id == flashcard.id

def test_parent_node_flashcard_deduplication(db_session):
    # Test requirement 7: Không đếm trùng Flashcard khi tính progress node cha
    course = Course(code="COMP2010_DEDUP", title="Test Course")
    db_session.add(course)
    db_session.commit()

    mindmap = Mindmap(course_id=course.id, title="Mindmap Parent Test")
    db_session.add(mindmap)
    db_session.commit()

    parent = MindmapNode(mindmap_id=mindmap.id, node_stable_id="parent-node", label="Parent")
    db_session.add(parent)
    db_session.commit()

    child1 = MindmapNode(mindmap_id=mindmap.id, node_stable_id="child-1", label="Child 1", parent_node_id=parent.id)
    child2 = MindmapNode(mindmap_id=mindmap.id, node_stable_id="child-2", label="Child 2", parent_node_id=parent.id)
    db_session.add_all([child1, child2])
    db_session.commit()

    fc_shared = Flashcard(course_id=course.id, question="Shared Question?", answer="Ans")
    fc_child1_only = Flashcard(course_id=course.id, question="Child 1 Question?", answer="Ans")
    
    fc_shared.mindmap_nodes.extend([child1, child2])
    fc_child1_only.mindmap_nodes.append(child1)
    db_session.add_all([fc_shared, fc_child1_only])
    db_session.commit()

    # Deduplication logic simulation for parent node
    all_child_nodes = [child1, child2]
    all_flashcard_ids = set()
    for c in all_child_nodes:
        for f in c.flashcards:
            all_flashcard_ids.add(f.id)

    # Total unique flashcards under parent should be 2 (fc_shared counted ONCE, not twice)
    assert len(all_flashcard_ids) == 2

def test_processing_job_retry_and_resume(db_session):
    course = Course(code="COMP2010_JOB", title="Job Test")
    db_session.add(course)
    db_session.commit()

    job = ProcessingJob(
        course_id=course.id,
        status=JobStatus.PENDING.value,
        retry_count=1,
        max_retries=3,
        last_completed_step="chunking",
        checkpoint_data={"processed_chunks": 15, "last_chunk_id": "chunk-15"}
    )
    db_session.add(job)
    db_session.commit()

    db_session.refresh(job)
    assert job.status == JobStatus.PENDING.value
    assert job.last_completed_step == "chunking"
    assert job.checkpoint_data["processed_chunks"] == 15

def test_model_config_no_secrets(db_session):
    # Requirement 12: No secrets directly in database
    model_cfg = ModelConfiguration(
        provider_name="OpenAI",
        model_name="gpt-4o",
        api_key_env_var_name="OPENAI_API_KEY",  # Variable name only!
        deployment_mode=DeploymentMode.CLOUD_ENTERPRISE.value,
        zero_data_retention=True
    )
    db_session.add(model_cfg)
    db_session.commit()

    db_session.refresh(model_cfg)
    assert model_cfg.api_key_env_var_name == "OPENAI_API_KEY"
    assert not hasattr(model_cfg, "api_key") or getattr(model_cfg, "api_key", None) is None
