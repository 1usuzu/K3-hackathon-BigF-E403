from typing import Dict, List, Optional
from backend.app.models.document import ContentChunk
from backend.app.services.glossary_protection import GlossaryPromptFormatter

class FlashcardPromptTemplate:
    @staticmethod
    def build_prompt(
        chunk: ContentChunk,
        protected_glossary: Optional[Dict[str, str]] = None
    ) -> str:
        glossary_instructions = GlossaryPromptFormatter.format_glossary_instructions(
            protected_glossary or {}
        )

        chunk_meta = chunk.metadata_json or {}
        title = chunk_meta.get("title", "Bài học")
        source_refs = chunk_meta.get("source_references", [])
        refs_str = ", ".join(source_refs) if source_refs else "Tài liệu học tập"

        formula_guidance = ""
        if chunk.has_formulas:
            formula_guidance = """
- VỚI CÔNG THỨC TOÁN HỌC: Tạo các câu hỏi tập trung vào:
  1. Ý nghĩa toán học và mục đích của công thức.
  2. Định nghĩa các biến số trong công thức.
  3. Điều kiện áp dụng công thức.
  4. Cách ứng dụng thực tế.
  5. Các sai lầm thường gặp khi áp dụng.
  6. GIỮ NGUYÊN công thức dạng LaTeX ($...$ hoặc $$...$$).
"""

        code_guidance = ""
        if chunk.has_code:
            code_guidance = """
- VỚI ĐOẠN MÃ NGUỒN (CODE BLOCK): Tạo các câu hỏi tập trung vào:
  1. Mục đích hoạt động của hàm/thuật toán.
  2. Đầu vào (Input) và Đầu ra (Output).
  3. Luồng điều khiển (Control Flow) và logic xử lý.
  4. Độ phức tạp thời gian/bộ nhớ (Time/Space Complexity).
  5. Các trường hợp biên (Edge Cases).
  6. GIỮ NGUYÊN 100% tên biến, tên hàm, tên lớp (Code identifiers).
"""

        prompt = f"""
Bạn là một Chuyên gia Giáo dục và Trợ lý Học tập AI cao cấp.
Nhiệm vụ của bạn là tạo các Flashcard chất lượng cao từ đoạn nội dung bài giảng dưới đây.

{glossary_instructions}

### NỘI DUNG BÀI GIẢNG (CHUNK CONTEXT):
- Tiêu đề: {title}
- Trích dẫn nguồn: {refs_str}
- Nội dung:
\"\"\"
{chunk.text_content}
\"\"\"

### QUY TẮC TẠO FLASHCARD:
1. MỖI FLASHCARD CHỈ KIỂM TRA MỘT Ý CHÍNH DUY NHẤT.
2. CHỈ SỬ DỤNG THÔNG TIN CÓ TRONG NỘI DUNG TRÊN. Không tự suy diễn thông tin ngoài tài liệu.
3. CÂU HỎI PHẢI RÕ RÀNG, KHÔNG MƠ HỒ.
4. MỖI FLASHCARD BẮT BUỘC CÓ NGUỒN TRÍCH DẪN (source_references: ["{refs_str}"]).
5. ĐIỂM CHẤT LƯỢNG (quality_score): Đánh giá chính xác từ 0.70 đến 1.00.

{formula_guidance}
{code_guidance}

Hãy tạo danh sách Flashcards phù hợp nhất.
"""
        return prompt.strip()
