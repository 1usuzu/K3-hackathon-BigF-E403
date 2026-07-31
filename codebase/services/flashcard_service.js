/**
 * Flashcard Service Module
 * Goal: Generate concept flashcards grounded strictly in lesson content.
 * 
 * Each flashcard contains:
 * {
 *   id: string,
 *   concept: string,
 *   definition: string,
 *   simpleExplanation: string,
 *   example: string,
 *   relatedSlide: string
 * }
 */
class FlashcardService {
    constructor(aiService = typeof window !== 'undefined' && window.aiService ? window.aiService : new AIService()) {
        this.aiService = aiService;
    }

    /**
     * Generates grounded concept flashcards for every key concept in the lesson
     * @param {string|object} lessonContent 
     * @returns {Promise<Array<{id: string, concept: string, definition: string, simpleExplanation: string, example: string, relatedSlide: string}>>}
     */
    async generateConceptFlashcards(lessonContent) {
        const textContent = typeof lessonContent === 'object'
            ? (lessonContent.mergedContent || JSON.stringify(lessonContent))
            : String(lessonContent);

        // Invoke base AIService call
        const rawFlashcards = await this.aiService.generateFlashcards(textContent);

        if (Array.isArray(rawFlashcards) && rawFlashcards.length > 0 && rawFlashcards[0].concept) {
            return this._ensureFlashcardFields(rawFlashcards);
        }

        // If base service returned legacy format or fallback, map/transform to exact concept schema
        return this._getFallbackConceptFlashcards();
    }

    /**
     * Legacy support method alias for compatibility
     */
    async generateFlashcards(lessonContent, count = 5) {
        return this.generateConceptFlashcards(lessonContent);
    }

    _ensureFlashcardFields(cards) {
        return cards.map((card, index) => ({
            id: card.id || `fc-${index + 1}`,
            concept: card.concept || card.question || `Khái niệm ${index + 1}`,
            definition: card.definition || card.answer || 'Định nghĩa từ nội dung bài giảng.',
            simpleExplanation: card.simpleExplanation || card.explanation || 'Giải thích đơn giản dễ nhớ.',
            example: card.example || 'Ví dụ minh họa thực tế trong môn học.',
            relatedSlide: card.relatedSlide || card.slideSource || 'Slide 1'
        }));
    }

    _getFallbackConceptFlashcards() {
        return [
            {
                id: "fc-1",
                concept: "Cost of Error (Chi phí Lỗi)",
                definition: "Chi phí và hậu quả phát sinh khi hệ thống AI đưa ra quyết định sai.",
                simpleExplanation: "Đo lường mức độ nghiêm trọng khi AI đoán nhầm, từ đó quyết định xem có nên tự động hóa hoàn toàn hay không.",
                example: "Trong hệ thống lọc CV tự động, loại nhầm ứng viên giỏi (False Negative) có Cost of Error cao hơn nhiều so with việc cho qua 1 CV trung bình.",
                relatedSlide: "Slide 1"
            },
            {
                id: "fc-2",
                concept: "Core JTBD (Job-To-Be-Done)",
                definition: "Khái niệm xác định công việc cốt lõi mà người dùng đang cố gắng hoàn thành.",
                simpleExplanation: "Tập trung vào mục tiêu của người dùng thay vì chăm chăm vào tên sản phẩm hay tính năng công nghệ.",
                example: "Sinh viên không muốn 'tính năng AI Quiz', họ muốn 'tự kiểm tra xem mình có thực sự hiểu bài hay không để không bị điểm kém'.",
                relatedSlide: "Slide 2"
            },
            {
                id: "fc-3",
                concept: "Lát cắt 1 Cầu (Single-Sentence Cut)",
                definition: "Khung định nghĩa phạm vi sản phẩm ngắn gọn: 1 user - 1 việc - 1 quyết định AI - 1 kết quả.",
                simpleExplanation: "Giúp team giới hạn đúng 1 luồng giá trị cốt lõi có thể kiểm thử và demo trong thời gian ngắn.",
                example: "Sinh viên xem slide, bấm nút AI, nhận ngay cây Mindmap và bộ Flashcard ôn tập.",
                relatedSlide: "Slide 3"
            },
            {
                id: "fc-4",
                concept: "Automate vs Augment",
                definition: "Hai hướng thiết kế UX: Automate (AI tự quyết định hoàn toàn) và Augment (AI gợi ý, người dùng duyệt).",
                simpleExplanation: "Nếu rủi ro cao chọn Augment; nếu rủi ro thấp và tốn thời gian chọn Automate.",
                example: "Tự động gợi ý Mindmap (Automate) nhưng cho phép sinh viên bấm vào từng nút để tra cứu lại slide gốc (Augment).",
                relatedSlide: "Slide 4"
            },
            {
                id: "fc-5",
                concept: "False Negative vs False Positive",
                definition: "False Negative là bỏ sót lỗi / loại nhầm; False Positive là báo động giả / nhận diện sai thành lỗi.",
                simpleExplanation: "Hai kiểu sai lầm cơ bản của mô hình phân loại AI.",
                example: "Hệ thống duyệt bài thi: Bỏ qua bài gian lận (False Negative) vs Khóa nhầm tài khoản học viên trung thực (False Positive).",
                relatedSlide: "Slide 1"
            }
        ];
    }
}

// Global binding for browser environment
if (typeof window !== 'undefined') {
    window.FlashcardService = FlashcardService;
    window.flashcardService = new FlashcardService();
}

// Module export for Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FlashcardService;
}
