import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base
from backend.app.models.course import Course, Lesson
from backend.app.models.document import LearningDocument, DocumentVersion, ContentChunk
from backend.app.models.flashcard import Flashcard
from backend.app.models.mindmap import Mindmap, MindmapNode, node_flashcard_association
from backend.app.services.node_linking import (
    FlashcardNodeLinkerService, NodeLinkRepository, NodeLinkMatch
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

def test_flashcard_linking_multiple_nodes_and_unsuitable_rejection():
    db = TestingSessionLocal()

    course = Course(id="c-link", code="AI301", title="AI Architecture")
    doc = LearningDocument(id="doc-l", course_id="c-link", title="file.pdf", file_type="application/pdf", file_path="file.pdf")
    doc_ver = DocumentVersion(id="ver-l", document_id="doc-l", version_number=1, file_path="file.pdf")
    chunk = ContentChunk(id="chk-l1", document_version_id="ver-l", chunk_index=1, text_content="Tối ưu hóa Gradient Descent trong PyTorch.")
    
    db.add_all([course, doc, doc_ver, chunk])
    db.commit()

    mindmap = Mindmap(id="mm-1", course_id="c-link", title="Mindmap 1")
    node1 = MindmapNode(
        id="n-1",
        mindmap_id="mm-1",
        node_stable_id="node-gradient-descent",
        label="Gradient Descent Optimization",
        slide_reference="Slide 12",
        metadata_json={"content_chunk_ids": ["chk-l1"], "glossary_terms": ["Gradient Descent"]}
    )
    node2 = MindmapNode(
        id="n-2",
        mindmap_id="mm-1",
        node_stable_id="node-pytorch-training",
        label="PyTorch Framework Training",
        slide_reference="Slide 12",
        metadata_json={"content_chunk_ids": ["chk-l1"], "glossary_terms": ["PyTorch"]}
    )
    # Unsuitable Node (Different chunk, different topic, no matching references)
    node_unsuitable = MindmapNode(
        id="n-unsuitable",
        mindmap_id="mm-1",
        node_stable_id="node-unrelated",
        label="Lịch sử CNTT 1980",
        slide_reference="Slide 99",
        metadata_json={"content_chunk_ids": ["chk-other"], "glossary_terms": ["History"]}
    )
    db.add_all([mindmap, node1, node2, node_unsuitable])
    db.commit()

    flashcard = Flashcard(
        id="fc-1",
        course_id="c-link",
        content_chunk_id="chk-l1",
        question="Cách cài đặt Gradient Descent trong PyTorch?",
        answer="Sử dụng torch.optim...",
        options_json={"source_references": ["Slide 12"], "glossary_terms": ["Gradient Descent", "PyTorch"]}
    )
    db.add(flashcard)
    db.commit()

    linker = FlashcardNodeLinkerService(min_confidence_threshold=0.60)
    matches = linker.find_matching_nodes(flashcard, [node1, node2, node_unsuitable])

    # Req 1 & 2: Flashcard links to MULTIPLE suitable nodes (node1 and node2)
    assert len(matches) == 2
    matched_ids = [m.node_id for m in matches]
    assert "n-1" in matched_ids
    assert "n-2" in matched_ids

    # Req 10: Unsuitable node is REJECTED (not in matches)
    assert "n-unsuitable" not in matched_ids
    for m in matches:
        assert m.confidence_score >= 0.60

    # Save links to DB via repository
    repo = NodeLinkRepository(db)
    inserted = repo.link_flashcard_to_nodes("fc-1", matched_ids)
    assert inserted == 2

    # Idempotency check: Link again -> 0 new rows inserted
    dup_inserted = repo.link_flashcard_to_nodes("fc-1", matched_ids)
    assert dup_inserted == 0

    db.close()

def test_mindmap_regeneration_stable_key_relinking():
    db = TestingSessionLocal()
    course = Course(id="c-regen", code="AI301", title="Regen Course")
    db.add(course)
    db.commit()

    # Old Mindmap
    mm_old = Mindmap(id="mm-old", course_id="c-regen", title="Old Mindmap")
    n_old = MindmapNode(id="n-old-1", mindmap_id="mm-old", node_stable_id="stable-node-loss", label="Loss Function")
    db.add_all([mm_old, n_old])
    db.commit()

    # Create flashcard linked to old node
    fc = Flashcard(id="fc-regen", course_id="c-regen", question="Loss Function là gì?", answer="Hàm mất mát.")
    db.add(fc)
    db.commit()

    repo = NodeLinkRepository(db)
    repo.link_flashcard_to_nodes("fc-regen", ["n-old-1"])

    # New Regenerated Mindmap (New Node Primary Key, but SAME node_stable_id)
    mm_new = Mindmap(id="mm-new", course_id="c-regen", title="Regenerated Mindmap")
    n_new = MindmapNode(id="n-new-1", mindmap_id="mm-new", node_stable_id="stable-node-loss", label="Loss Function V2")
    db.add_all([mm_new, n_new])
    db.commit()

    # Execute Relinking via stable key (Req 11)
    result = repo.relink_flashcards_on_mindmap_regeneration(
        old_mindmap_id="mm-old",
        new_mindmap_id="mm-new"
    )

    assert result["relinked_nodes_count"] == 1
    assert result["total_links_relinked"] == 1

    # Verify new node is now linked to the flashcard in DB
    db.refresh(n_new)
    assert len(n_new.flashcards) == 1
    assert n_new.flashcards[0].id == "fc-regen"

    db.close()
