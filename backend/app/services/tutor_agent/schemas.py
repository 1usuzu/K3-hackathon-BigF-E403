from typing import List, Optional
from pydantic import BaseModel, Field

class CitationSchema(BaseModel):
    document_id: Optional[str] = Field(default=None, description="ID tài liệu gốc")
    document_version_id: Optional[str] = Field(default=None, description="ID phiên bản tài liệu")
    chunk_id: Optional[str] = Field(default=None, description="ID khối thông tin chunk")
    page_number: Optional[int] = Field(default=None, description="Số trang tài liệu PDF")
    slide_number: Optional[int] = Field(default=None, description="Số slide PowerPoint")
    timestamp_start: Optional[float] = Field(default=None, description="Thời gian bắt đầu (nếu là video/audio)")
    timestamp_end: Optional[float] = Field(default=None, description="Thời gian kết thúc (nếu là video/audio)")
    source_excerpt: str = Field(..., description="Trích đoạn ngắn văn bản gốc được tham chiếu")

class TutorResponseSchema(BaseModel):
    answer: str = Field(..., description="Nội dung câu trả lời từ AI Tutor dựa trên tài liệu")
    answer_type: str = Field(
        default="direct_answer",
        description="Loại câu trả lời (direct_answer, explanation, insufficient_context, code_explanation, formula_explanation)"
    )
    response_language: str = Field(default="vi", description="Ngôn ngữ câu trả lời")
    preserved_terms: List[str] = Field(default_factory=list, description="Các thuật ngữ tiếng Anh được bảo toàn")
    citations: List[CitationSchema] = Field(default_factory=list, description="Danh sách các trích dẫn nguồn")
    confidence: float = Field(default=0.90, description="Độ tin cậy của câu trả lời (0.0 đến 1.0)")
    insufficient_context: bool = Field(default=False, description="True nếu tài liệu không đủ thông tin để trả lời")
    suggested_questions: List[str] = Field(default_factory=list, description="Gợi ý câu hỏi học tập tiếp theo")
