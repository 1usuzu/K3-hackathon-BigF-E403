import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.models.user import User
from backend.app.models.course import Course
from backend.app.models.mindmap import Mindmap, MindmapNode
from backend.app.models.flashcard import Flashcard
from backend.app.services.node_linking import NodeLinkRepository

TEST_DB_URL = "sqlite:///file:mem_ui?mode=memory&cache=shared&uri=true"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_shared_session = None

def override_get_db():
    global _shared_session
    if _shared_session is None:
        _shared_session = TestingSessionLocal()
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

def test_integration_flow_mindmap_fetching():
    db = _shared_session
    course = Course(id="c-hackathon-d2", code="COMP2010", title="Day 02: AI Problem")
    mindmap = Mindmap(id="mm-ui-1", course_id="c-hackathon-d2", title="XÁC ĐỊNH BÀI TOÁN AI")
    node_root = MindmapNode(id="n-root-1", mindmap_id="mm-ui-1", node_stable_id="n-root-1", label="XÁC ĐỊNH BÀI TOÁN AI", page_number=1)
    
    db.add_all([course, mindmap, node_root])
    db.commit()

    resp = client.get("/api/v1/learning/mindmaps/c-hackathon-d2")
    assert resp.status_code == 200
    data = resp.json()
    assert "tree" in data
    assert len(data["tree"]) >= 1

def test_integration_flow_flashcard_fetching_and_attempts():
    db = _shared_session
    user = User(id="usr-student-1", email="student@test.com", full_name="Student 1")
    course = Course(id="c-hackathon-d2", code="COMP2010", title="Day 02")
    mindmap = Mindmap(id="mm-ui-card", course_id="c-hackathon-d2", title="Mindmap Card")
    node = MindmapNode(id="n-ui-1", mindmap_id="mm-ui-card", node_stable_id="n-ui-1", label="Card Node")
    card = Flashcard(id="fc-ui-1", course_id="c-hackathon-d2", question="Q?", answer="A")

    db.add_all([user, course, mindmap, node, card])
    db.commit()

    repo = NodeLinkRepository(db)
    repo.link_flashcard_to_nodes("fc-ui-1", ["n-ui-1"])

    # 1. Fetch Flashcards
    resp = client.get("/api/v1/learning/flashcards/c-hackathon-d2")
    assert resp.status_code == 200
    cards = resp.json()
    assert len(cards) >= 1

    # 2. Post Attempt
    resp_attempt = client.post("/api/v1/progress/attempts", json={
        "user_id": "usr-student-1",
        "flashcard_id": cards[0]["id"],
        "is_correct": True,
        "selected_option": cards[0]["answer"],
        "response_time_ms": 1200
    })
    assert resp_attempt.status_code == 201
    attempt_data = resp_attempt.json()
    assert "completion_percentage" in attempt_data
    assert "mastery_percentage" in attempt_data
    assert "progress_token" in attempt_data

def test_integration_flow_tutor_agent_chat():
    db = _shared_session
    user = User(id="usr-student-1", email="student@test.com", full_name="Student 1")
    course = Course(id="c-hackathon-d2", code="COMP2010", title="Day 02")

    db.add_all([user, course])
    db.commit()

    # 1. Create Session
    resp_sess = client.post("/api/v1/chat/sessions", json={
        "user_id": "usr-student-1",
        "course_id": "c-hackathon-d2",
        "title": "Tutor Chat UI Test"
    })
    assert resp_sess.status_code == 201
    sess_data = resp_sess.json()
    session_id = sess_data["session_id"]

    # 2. Post Message
    resp_msg = client.post("/api/v1/chat/messages", json={
        "user_id": "usr-student-1",
        "course_id": "c-hackathon-d2",
        "question": "JTBD là gì?",
        "conversation_id": session_id
    })
    assert resp_msg.status_code == 200
    msg_data = resp_msg.json()
    assert "answer" in msg_data
    assert "answer_type" in msg_data
