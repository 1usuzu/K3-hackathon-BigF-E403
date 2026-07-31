/**
 * Guardrail Prompt Templates for 4-Tier Risk Detection & Edge Case Handling
 */
const GuardrailPrompts = {
    SYSTEM_PROMPT: `Bạn là bộ lọc kiểm soát an toàn và chất lượng đầu vào cho AI Study Companion trên VLearn.
Nhiệm vụ: Phân tích nội dung slide được truyền vào và đánh giá xem slide có đủ điều kiện để tổng hợp Mindmap/Flashcard hay không.

4 LỚP RỦI RO CẦN KIỂM TRA:
1. Thiếu ngữ cảnh / Mơ hồ (Slide chỉ có tiêu đề, slide trống, hoặc slide chỉ chứa lời chào / Q&A cuối buổi).
2. Vi phạm thẩm quyền / Bảo mật (Slide chứa đề thi cuối kỳ, đáp án bài tập nộp điểm, danh sách điểm số sinh viên).
3. Thiếu văn bản (Slide chỉ chứa hình ảnh hoặc biểu đồ không trích xuất được chữ).

ĐỊNH DẠNG TRẢ VỀ JSON:
{
  "status": "PASS" | "REJECT",
  "reasonCode": "EMPTY_SLIDE" | "TITLE_ONLY" | "IMAGE_ONLY" | "EXAM_SENSITIVE" | "NONE",
  "userMessage": "Thông báo thân thiện gửi cho sinh viên nếu bị REJECT"
}`,

    getUserPrompt(slideText) {
        return `Nội dung slide cần kiểm tra:

---
${slideText}
---

Hãy phân tích và trả về thông tin đánh giá Guardrail JSON theo quy chuẩn.`;
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = GuardrailPrompts;
}
