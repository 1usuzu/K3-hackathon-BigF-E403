/**
 * Quiz Service Module
 * Goal: Generate multiple choice quizzes grouped by concept.
 * 
 * Each concept contains exactly 3 MCQs.
 * Each question includes:
 * {
 *   question: string,
 *   options: Array<string>,
 *   correctAnswer: string,
 *   explanation: string,
 *   difficulty: "Easy" | "Medium" | "Hard"
 * }
 */
class QuizService {
    constructor(aiService = typeof window !== 'undefined' && window.aiService ? window.aiService : new AIService()) {
        this.aiService = aiService;
    }

    /**
     * Generates concept-grouped quizzes from lesson content
     * @param {string|object} lessonContent 
     * @returns {Promise<{quizzesByConcept: Array<{concept: string, questions: Array<object>}>}>}
     */
    async generateConceptQuizzes(lessonContent) {
        const textContent = typeof lessonContent === 'object'
            ? (lessonContent.mergedContent || JSON.stringify(lessonContent))
            : String(lessonContent);

        // Invoke base AIService call
        const rawQuizData = await this.aiService.generateQuiz(textContent);

        // Deduplicate and group into required format
        if (rawQuizData && Array.isArray(rawQuizData.quizzesByConcept)) {
            return this._deduplicateAndFormat(rawQuizData.quizzesByConcept);
        }

        // Transform array of questions into concept-grouped structure if flat array returned
        if (Array.isArray(rawQuizData)) {
            return this._groupFlatQuestionsByConcept(rawQuizData);
        }

        // Fallback grounded quiz set matching the exact required schema
        return this._getFallbackConceptQuizzes();
    }

    _deduplicateAndFormat(quizzesByConcept) {
        const seenQuestions = new Set();

        const formatted = quizzesByConcept.map(group => {
            const uniqueQuestions = [];
            (group.questions || []).forEach(q => {
                const normQ = (q.question || '').trim().toLowerCase();
                if (!seenQuestions.has(normQ) && normQ.length > 5) {
                    seenQuestions.add(normQ);
                    uniqueQuestions.push({
                        question: q.question,
                        options: Array.isArray(q.options) ? q.options : [],
                        correctAnswer: q.correctAnswer || q.answer || q.options?.[0],
                        explanation: q.explanation || 'Dựa theo nội dung bài giảng.',
                        difficulty: q.difficulty || 'Medium'
                    });
                }
            });
            return {
                concept: group.concept || 'Khái niệm bài học',
                questions: uniqueQuestions
            };
        });

        return { quizzesByConcept: formatted };
    }

    _groupFlatQuestionsByConcept(questions) {
        const grouped = [
            {
                concept: "Cost of Error & Rủi ro AI",
                questions: questions.slice(0, 3).map((q, idx) => ({
                    question: q.question,
                    options: q.options || [],
                    correctAnswer: q.correctAnswer || q.answer || q.options?.[0],
                    explanation: q.explanation || 'Dựa vào phân tích Cost of Error trong slide.',
                    difficulty: idx === 0 ? 'Easy' : idx === 1 ? 'Medium' : 'Hard'
                }))
            }
        ];
        return { quizzesByConcept: grouped };
    }

    _getFallbackConceptQuizzes() {
        return {
            quizzesByConcept: [
                {
                    concept: "Cost of Error (Chi phí Lỗi)",
                    questions: [
                        {
                            question: "Nếu AI lọc CV, 'Cost of Error' lớn nhất thuộc về trường hợp nào?",
                            options: [
                                "A. Tốn chi phí hạ tầng máy chủ",
                                "B. Loại nhầm ứng viên tài năng (False Negative)",
                                "C. Giao diện người dùng bị chậm",
                                "D. Người dùng không gửi phản hồi"
                            ],
                            correctAnswer: "B. Loại nhầm ứng viên tài năng (False Negative)",
                            explanation: "False Negative làm doanh nghiệp bỏ sót nhân tài, gây thiệt hại lâu dài không thể sửa chữa.",
                            difficulty: "Easy"
                        },
                        {
                            question: "Trong quy trình đánh giá sản phẩm AI, khi Cost of Error cực kỳ lớn thì nên làm gì?",
                            options: [
                                "A. Cho AI tự động hóa 100% không cần người duyệt",
                                "B. Chuyển sang mô hình Augment (AI gợi ý, con người quyết định)",
                                "C. Bỏ qua việc đánh giá lỗi",
                                "D. Tăng tốc độ phản hồi của API"
                            ],
                            correctAnswer: "B. Chuyển sang mô hình Augment (AI gợi ý, con người quyết định)",
                            explanation: "Mô hình Augment giữ con người ở vị trí duyệt cuối cùng để chặn rủi ro cao.",
                            difficulty: "Medium"
                        },
                        {
                            question: "Điểm khác biệt chính giữa False Positive và False Negative trong kiểm thử bài thi là gì?",
                            options: [
                                "A. False Positive là bỏ sót gian lận, False Negative là báo nhầm bài gian lận",
                                "B. False Positive là báo nhầm bài gian lận, False Negative là bỏ sót bài gian lận",
                                "C. Cả hai đều có nghĩa là bài thi đạt điểm tối đa",
                                "D. Cả hai đều là lỗi mạng kết nối"
                            ],
                            correctAnswer: "B. False Positive là báo nhầm bài gian lận, False Negative là bỏ sót bài gian lận",
                            explanation: "Báo nhầm gây phiền toái cho học viên trung thực, còn bỏ sót gây mất tính công bằng của kỳ thi.",
                            difficulty: "Hard"
                        }
                    ]
                },
                {
                    concept: "Phương pháp JTBD & Lát cắt 1 Câu",
                    questions: [
                        {
                            question: "Câu hỏi cốt lõi để xác định JTBD (Job-To-Be-Done) của học viên là gì?",
                            options: [
                                "A. Học viên muốn mua gói học phí nào?",
                                "B. Học viên đang cố hoàn thành việc gì và vướng ở đâu?",
                                "C. Giao diện nào đẹp nhất cho ứng dụng?",
                                "D. Mẫu model AI nào nhanh nhất hiện nay?"
                            ],
                            correctAnswer: "B. Học viên đang cố hoàn thành việc gì và vướng ở đâu?",
                            explanation: "JTBD tập trung vào bối cảnh và mục tiêu thực sự của người dùng.",
                            difficulty: "Easy"
                        },
                        {
                            question: "Cấu trúc tiêu chuẩn của một 'Lát cắt 1 câu' bao gồm 4 yếu tố nào?",
                            options: [
                                "A. 1 user - 1 việc - 1 quyết định AI - 1 kết quả",
                                "B. 1 slide - 1 quiz - 1 prompt - 1 code file",
                                "C. 1 chatbot - 1 database - 1 server - 1 demo",
                                "D. 1 học viên - 1 TA - 1 giảng viên - 1 lớp học"
                            ],
                            correctAnswer: "A. 1 user - 1 việc - 1 quyết định AI - 1 kết quả",
                            explanation: "Đây là lát cắt tối giản đủ để kiểm chứng giá trị sản phẩm AI trong prototype.",
                            difficulty: "Medium"
                        },
                        {
                            question: "Vì sao nên loại bỏ ứng viên Chatbot QA trong bài toán tóm tắt bài giảng VLearn?",
                            options: [
                                "A. Vì Chatbot quá đắt tiền",
                                "B. Vì học viên thường không biết gõ câu hỏi gì khi chưa hiểu bài",
                                "C. Vì Chatbot không thể trả lời bằng tiếng Việt",
                                "D. Vì Chatbot luôn bị lỗi kết nối"
                            ],
                            correctAnswer: "B. Vì học viên thường không biết gõ câu hỏi gì khi chưa hiểu bài",
                            explanation: "Khảo sát chỉ ra học viên ngại gõ prompt và cần dạng tương tác trực quan 1-click hơn.",
                            difficulty: "Hard"
                        }
                    ]
                }
            ]
        };
    }
}

// Global binding for browser environment
if (typeof window !== 'undefined') {
    window.QuizService = QuizService;
    window.quizService = new QuizService();
}

// Module export for Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuizService;
}
