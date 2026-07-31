import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base
from backend.app.models.course import Course
from backend.app.models.document import GlossaryTerm
from backend.app.services.glossary_protection import (
    DEFAULT_SYSTEM_GLOSSARY,
    GlossaryExtractionService,
    GlossaryMergeService,
    GlossaryPromptFormatter,
    GlossaryOutputValidator
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

def test_glossary_extraction_service():
    lecture_text = """
    Hôm nay chúng ta học về Cross Entropy Loss và bài toán Random Forest.
    Sử dụng thư viện PyTorch và model BERT với hàm compute_loss và biến \\theta.
    """

    extracted = GlossaryExtractionService.extract_candidate_terms(lecture_text)

    assert "Cross Entropy Loss" in extracted or "Random Forest" in extracted
    assert "BERT" in extracted
    assert "compute_loss" in extracted
    assert "\\theta" in extracted

def test_glossary_merge_service_3_tier_conflict_resolution():
    db = TestingSessionLocal()
    course = Course(id="c-glo", code="CS101", title="AI Intro")
    
    # Custom Course Glossary Term overriding default
    gt_override = GlossaryTerm(
        course_id="c-glo",
        term="Gradient Descent",
        definition="Định nghĩa riêng cấp khóa học cho Gradient Descent"
    )
    db.add_all([course, gt_override])
    db.commit()

    document_text = "Học về Backpropagation và Neural Network."

    merged = GlossaryMergeService.get_merged_glossary_for_course(
        course_id="c-glo",
        db=db,
        document_text=document_text
    )

    # 1. Course DB term overrides Default System definition
    assert merged["Gradient Descent"] == "Định nghĩa riêng cấp khóa học cho Gradient Descent"
    # 2. Default System term retained
    assert "Overfitting" in merged
    # 3. Document extracted term merged
    assert "Neural Network" in merged

    db.close()

def test_glossary_prompt_formatter():
    glossary = {
        "Gradient Descent": "Phương pháp tối ưu toán học",
        "False Positive": "Dương tính giả"
    }

    instructions = GlossaryPromptFormatter.format_glossary_instructions(glossary)

    assert "GLOSSARY PROTECTION RULES" in instructions
    assert "Gradient Descent" in instructions
    assert "False Positive" in instructions
    assert "KHÔNG DỊCH" in instructions

def test_glossary_output_validator_detects_forbidden_translations():
    protected_terms = {
        "Gradient Descent": "Optimization",
        "Overfitting": "High variance",
        "LossEvaluator": "Code class"
    }

    # Invalid translation output (Translated 'Gradient Descent' to 'giảm độ dốc' and 'Overfitting' to 'quá khớp')
    bad_output = "Thuật toán giảm độ dốc bị ảnh hưởng bởi quá khớp."
    result_bad = GlossaryOutputValidator.validate_output(bad_output, protected_terms)

    assert result_bad.is_valid is False
    assert len(result_bad.violations) >= 2
    found_violations = [v["found_translation"] for v in result_bad.violations]
    assert "giảm độ dốc" in found_violations
    assert "quá khớp" in found_violations

    # Valid output preserving English terms
    good_output = "Thuật toán Gradient Descent bị ảnh hưởng nếu mô hình bị Overfitting."
    result_good = GlossaryOutputValidator.validate_output(good_output, protected_terms)

    assert result_good.is_valid is True
    assert len(result_good.violations) == 0

def test_code_identifier_case_preservation():
    protected_terms = {
        "LossEvaluator": "Code class"
    }

    # Altered case output ('lossevaluator' instead of 'LossEvaluator')
    altered_output = "Lớp lossevaluator thực hiện tính toán."
    result = GlossaryOutputValidator.validate_output(altered_output, protected_terms)

    assert result.is_valid is False
    assert result.violations[0]["expected_term"] == "LossEvaluator"
