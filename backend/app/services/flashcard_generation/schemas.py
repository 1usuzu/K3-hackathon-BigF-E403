from typing import List, Optional
from pydantic import BaseModel, Field

FLASHCARD_TYPES = [
    "definition",
    "concept",
    "formula",
    "code",
    "fill_blank",
    "true_false",
    "multiple_choice",
    "application",
    "misconception",
    "comparison"
]

class FlashcardItemSchema(BaseModel):
    type: str = Field(..., description="Loại flashcard (definition, concept, formula, code, fill_blank, true_false, multiple_choice, application, misconception, comparison)")
    front: str = Field(..., description="Mặt trước flashcard (Câu hỏi hoặc yêu cầu điền từ)")
    back: str = Field(..., description="Mặt sau flashcard (Đáp án ngắn gọn, chính xác)")
    explanation: str = Field(..., description="Giải thích chi tiết nguyên lý và lý do đáp án đúng")
    difficulty: str = Field(default="MEDIUM", description="Độ khó: EASY, MEDIUM, HARD")
    blooms_level: str = Field(default="Understand", description="Cấp độ tư duy Bloom: Remember, Understand, Apply, Analyze, Evaluate, Create")
    tags: List[str] = Field(default_factory=list, description="Thẻ phân loại chủ đề")
    glossary_terms: List[str] = Field(default_factory=list, description="Danh sách thuật ngữ bảo vệ có trong card")
    source_references: List[str] = Field(default_factory=list, description="Trích dẫn nguồn gốc (Slide X hoặc Page Y)")
    quality_score: float = Field(default=0.85, description="Điểm chất lượng flashcard từ 0.0 đến 1.0")

class FlashcardListSchema(BaseModel):
    flashcards: List[FlashcardItemSchema] = Field(default_factory=list, description="Danh sách các flashcard được sinh ra")
