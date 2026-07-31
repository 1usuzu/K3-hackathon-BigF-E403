import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.core.database import Base, get_db
from backend.app.models import *
from backend.app.models.user import User
from backend.app.models.course import Course, Lesson
from backend.app.models.flashcard import Flashcard, FlashcardAttempt
from backend.app.models.mindmap import Mindmap, MindmapNode
from backend.app.services.node_linking.repository import NodeLinkRepository
from backend.app.services.learning_progress import (
    LearningProgressService, MasteryConfig, ProgressResponseDTO, determine_progress_token
)
from backend.app.main import app

TEST_DB_URL = "sqlite:///file:mem_prog?mode=memory&cache=shared&uri=true"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False, "uri": True},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_shared_session = None

def override_get_db():
    global _shared_session
    if _shared_session is None:
        _shared_session = TestingSessionLocal()
    Base.metadata.create_all(bind=engine)
    try:
        yield _shared_session
    finally:
        pass

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_environment():
    global _shared_session
    _shared_session = TestingSessionLocal()
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if _shared_session:
        _shared_session.close()
        _shared_session = None
    app.dependency_overrides.clear()

def test_special_multi_node_flashcard_deduplication():
    """
    SPECIAL TEST: Verifies that when a parent node has 2 child nodes sharing the SAME Flashcard,
    the parent node's progress calculation counts that Flashcard EXACTLY ONCE (zero double-counting!).
    """
    db = TestingSessionLocal()

    user = User(id="usr-prog", email="student@school.edu", full_name="Student Test")
    course = Course(id="c-prog", code="AI401", title="Deep Learning")
    mindmap = Mindmap(id="mm-prog", course_id="c-prog", title="Cây bài học")

    # Parent Node
    node_parent = MindmapNode(id="n-parent", mindmap_id="mm-prog", node_stable_id="n-parent", label="Chương 1: Deep Learning")
    db.add_all([user, course, mindmap, node_parent])
    db.commit()

    # 2 Child Nodes under Parent Node
    node_child_a = MindmapNode(id="n-child-a", mindmap_id="mm-prog", node_stable_id="n-child-a", label="Child A", parent_node_id="n-parent")
    node_child_b = MindmapNode(id="n-child-b", mindmap_id="mm-prog", node_stable_id="n-child-b", label="Child B", parent_node_id="n-parent")
    db.add_all([node_child_a, node_child_b])
    db.commit()

    # Flashcard 1 (Unique to Child A)
    fc1 = Flashcard(id="fc-1", course_id="c-prog", question="Q1?", answer="A1")
    # Flashcard 2 (SHARED between Child A AND Child B!)
    fc_shared = Flashcard(id="fc-shared", course_id="c-prog", question="Q Shared?", answer="A Shared")
    # Flashcard 3 (Unique to Child B)
    fc3 = Flashcard(id="fc-3", course_id="c-prog", question="Q3?", answer="A3")

    db.add_all([fc1, fc_shared, fc3])
    db.commit()

    repo = NodeLinkRepository(db)
    repo.link_flashcard_to_nodes("fc-1", ["n-child-a"])
    repo.link_flashcard_to_nodes("fc-shared", ["n-child-a", "n-child-b"])  # SHARED CARD!
    repo.link_flashcard_to_nodes("fc-3", ["n-child-b"])

    service = LearningProgressService(db=db)

    # 1. Check Parent Node Total Flashcards Count
    parent_dto = service.calculate_node_progress_dto("usr-prog", node_parent)
    # Total unique cards across child A and child B should be EXACTLY 3 (not 4!)
    assert parent_dto.total_cards == 3

    # 2. Student attempts the SHARED Flashcard
    service.record_attempt("usr-prog", "fc-shared", is_correct=True)

    # Check Parent Node Progress again
    parent_dto2 = service.calculate_node_progress_dto("usr-prog", node_parent)
    assert parent_dto2.completed_cards == 1
    assert parent_dto2.total_cards == 3
    assert parent_dto2.completion_percentage == 33.33

    db.close()

def test_attempt_status_transitions_and_mastery_config():
    db = TestingSessionLocal()
    user = User(id="usr-st", email="user@test.com", full_name="User Test")
    course = Course(id="c-st", code="CS101", title="Intro")
    mindmap = Mindmap(id="mm-st", course_id="c-st", title="Mindmap")
    node = MindmapNode(id="n-st", mindmap_id="mm-st", node_stable_id="n-st", label="Concept Node")
    card = Flashcard(id="fc-st", course_id="c-st", question="Q?", answer="A")

    db.add_all([user, course, mindmap, node, card])
    db.commit()

    repo = NodeLinkRepository(db)
    repo.link_flashcard_to_nodes("fc-st", ["n-st"])

    custom_config = MasteryConfig(consecutive_correct_required=3)
    service = LearningProgressService(db=db, config=custom_config)

    # Initial status: new
    assert service.evaluate_card_status("usr-st", "fc-st") == "new"

    # Attempt 1 (Correct): status -> learning
    service.record_attempt("usr-st", "fc-st", is_correct=True)
    assert service.evaluate_card_status("usr-st", "fc-st") == "learning"

    # Attempt 2 (Correct): status -> reviewing
    service.record_attempt("usr-st", "fc-st", is_correct=True)
    assert service.evaluate_card_status("usr-st", "fc-st") == "reviewing"

    # Attempt 3 (Correct - 3 consecutive correct): status -> mastered!
    _, dto = service.record_attempt("usr-st", "fc-st", is_correct=True)
    assert service.evaluate_card_status("usr-st", "fc-st") == "mastered"
    assert dto.mastery_percentage == 100.0
    assert dto.progress_token == "progress-purple"

    db.close()

def test_progress_rebuild_from_history():
    db = TestingSessionLocal()
    user = User(id="usr-reb", email="reb@test.com", full_name="Rebuild Test")
    course = Course(id="c-reb", code="CS102", title="Rebuild Course")
    mindmap = Mindmap(id="mm-reb", course_id="c-reb", title="Mindmap")
    node = MindmapNode(id="n-reb", mindmap_id="mm-reb", node_stable_id="n-reb", label="Rebuild Node")
    card = Flashcard(id="fc-reb", course_id="c-reb", question="Q?", answer="A")

    db.add_all([user, course, mindmap, node, card])
    db.commit()

    repo = NodeLinkRepository(db)
    repo.link_flashcard_to_nodes("fc-reb", ["n-reb"])

    # Insert raw attempts history directly in DB
    a1 = FlashcardAttempt(user_id="usr-reb", flashcard_id="fc-reb", is_correct=True, attempted_at=datetime.now(timezone.utc))
    a2 = FlashcardAttempt(user_id="usr-reb", flashcard_id="fc-reb", is_correct=True, attempted_at=datetime.now(timezone.utc))
    a3 = FlashcardAttempt(user_id="usr-reb", flashcard_id="fc-reb", is_correct=True, attempted_at=datetime.now(timezone.utc))
    db.add_all([a1, a2, a3])
    db.commit()

    service = LearningProgressService(db=db)
    rebuilt = service.rebuild_progress_from_history("usr-reb", "c-reb")
    assert rebuilt >= 1

    dto = service.calculate_node_progress_dto("usr-reb", node)
    assert dto.mastery_percentage == 100.0

    db.close()

def test_fastapi_progress_endpoints():
    db = _shared_session
    user = User(id="usr-api", email="api@test.com", full_name="API Test")
    course = Course(id="c-api", code="CS103", title="API Course")
    mindmap = Mindmap(id="mm-api", course_id="c-api", title="Mindmap")
    node = MindmapNode(id="n-api", mindmap_id="mm-api", node_stable_id="n-api", label="API Node")
    card = Flashcard(id="fc-api", course_id="c-api", question="API Q?", answer="API A")

    db.add_all([user, course, mindmap, node, card])
    db.commit()

    repo = NodeLinkRepository(db)
    repo.link_flashcard_to_nodes("fc-api", ["n-api"])

    # Keep db session alive so in-memory SQLite tables persist for client requests

    # 1. Record Attempt API (POST /api/v1/progress/attempts)
    resp = client.post("/api/v1/progress/attempts", json={
        "user_id": "usr-api",
        "flashcard_id": "fc-api",
        "is_correct": True,
        "selected_option": "API A",
        "response_time_ms": 1200
    })

    assert resp.status_code == 201
    data = resp.json()
    assert "attempt_id" in data
    assert data["completion_percentage"] == 100.0
    assert data["progress_token"] != ""

    # 2. Get Node Progress API (GET /api/v1/progress/nodes/{node_id})
    resp_node = client.get(f"/api/v1/progress/nodes/n-api?user_id=usr-api")
    assert resp_node.status_code == 200
    node_data = resp_node.json()
    assert node_data["node_id"] == "n-api"
    assert node_data["completed_cards"] == 1
    assert node_data["total_cards"] == 1
