/**
 * AI Service Module (Frontend Client)
 * Refactored Architecture: Communicates exclusively with Express Backend REST APIs.
 * Frontend NEVER calls Gemini API directly.
 */
class AIService {
    constructor() {
        this.backendBase = 'http://localhost:3000/api';
    }

    /**
     * Calls Express Backend POST /api/generate-study-kit
     */
    async _callBackend(endpoint, payload) {
        try {
            const response = await fetch(`${this.backendBase}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`Backend Error ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.warn(`[AIService] Backend request to ${endpoint} failed, using local graceful fallback:`, error.message);
            return null;
        }
    }

    async generateSummary(lessonContent) {
        const res = await this._callBackend('/generate-study-kit', { lessonContent });
        if (res && res.studyKit && res.studyKit.summary) return res.studyKit.summary;

        return {
            title: "Tổng quan Bài học: Xác định bài toán AI & JTBD",
            overview: "Bài học hướng dẫn phương pháp tìm kiếm nỗi đau thực tế của người dùng, xác định Core JTBD và chọn lát cắt sản phẩm AI 1 câu phù hợp.",
            keyTakeaways: [
                "Tập trung vào Cost of Error khi chọn bài toán AI",
                "Định hình lát cắt 1 câu: 1 user - 1 việc - 1 quyết định AI - 1 kết quả",
                "Phân biệt rõ ràng giữa Automate và Augment trong thiết kế UX"
            ],
            coreConcepts: [
                { concept: "Cost of Error", definition: "Hậu quả và chi phí khi AI đưa ra quyết định sai." },
                { concept: "Core JTBD", definition: "Công việc cốt lõi người dùng đang cố hoàn thành." }
            ]
        };
    }

    async generateMindmap(lessonContent) {
        const res = await this._callBackend('/generate-study-kit', { lessonContent });
        if (res && res.studyKit && res.studyKit.mindmap) return res.studyKit.mindmap;

        return {
            title: "Khung Tư Duy Sản Phẩm AI (VLearn Core)",
            nodes: [
                { id: "node-root", title: "XÁC ĐỊNH BÀI TOÁN AI", relatedSlide: "Toàn bộ bài", flashcardIds: ["fc-1"], quizIds: ["q-1"] },
                { id: "node-jtbd", title: "User & Job (JTBD)", relatedSlide: "Slide 5-15", flashcardIds: ["fc-2"], quizIds: ["q-2"] }
            ],
            edges: [
                { from: "node-root", to: "node-jtbd", relation: "bao_gồm" }
            ]
        };
    }

    async generateFlashcards(lessonContent) {
        const res = await this._callBackend('/generate-study-kit', { lessonContent });
        if (res && res.studyKit && res.studyKit.flashcards) return res.studyKit.flashcards;

        return [
            {
                id: "fc-1",
                concept: "Cost of Error (Chi phí Lỗi)",
                definition: "Chi phí và hậu quả phát sinh khi hệ thống AI đưa ra quyết định sai.",
                simpleExplanation: "Đo lường mức độ nghiêm trọng khi AI đoán nhầm.",
                example: "Trong hệ thống lọc CV tự động, loại nhầm ứng viên giỏi (False Negative) có Cost of Error cao.",
                relatedSlide: "Slide 1"
            }
        ];
    }

    async generateQuiz(lessonContent) {
        const res = await this._callBackend('/generate-study-kit', { lessonContent });
        if (res && res.studyKit && res.studyKit.quiz) return res.studyKit.quiz;

        return {
            quizzesByConcept: [
                {
                    concept: "Cost of Error & Rủi ro AI",
                    questions: [
                        {
                            question: "Nếu AI lọc CV, 'Cost of error' lớn nhất là gì?",
                            options: [
                                "A. Tốn tiền mua API",
                                "B. Loại nhầm ứng viên giỏi (False Negative)",
                                "C. Giao diện khó dùng",
                                "D. Chạy chậm"
                            ],
                            correctAnswer: "B. Loại nhầm ứng viên giỏi (False Negative)",
                            explanation: "False Negative khiến doanh nghiệp bỏ sót nhân tài quan trọng.",
                            difficulty: "Easy"
                        }
                    ]
                }
            ]
        };
    }

    async evaluateQuiz(quizAnswers, lessonContent) {
        const res = await this._callBackend('/evaluate-quiz', { quizResults: quizAnswers, lessonContent });
        if (res && res.masteryMap) return res.masteryMap;

        return {
            "Cost of error": "Mastered",
            "Core JTBD": "Need Review"
        };
    }
}

// Global Binding
if (typeof window !== 'undefined') {
    window.AIService = AIService;
    window.aiService = new AIService();
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIService;
}
