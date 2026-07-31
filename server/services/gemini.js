/**
 * Server-side Gemini API Service Module
 * Configured dynamically via process.env (dotenv)
 */
const fetch = global.fetch || require('node-fetch');

class GeminiBackendService {
    constructor() {
        this.apiBase = 'https://generativelanguage.googleapis.com/v1beta/models';
    }

    get apiKey() {
        return process.env.GEMINI_API_KEY || '';
    }

    get modelName() {
        return process.env.MODEL_NAME || process.env.GEMINI_MODEL || 'gemini-2.5-flash';
    }

    get temperature() {
        return parseFloat(process.env.TEMPERATURE) || 0.2;
    }

    get maxOutputTokens() {
        return parseInt(process.env.MAX_OUTPUT_TOKENS, 10) || 4096;
    }

    /**
     * Executes prompt against Gemini API using environment variable parameters
     * @param {string} systemPrompt 
     * @param {string} userPrompt 
     * @returns {Promise<object|null>} Parsed JSON output or fallback
     */
    async callGemini(systemPrompt, userPrompt) {
        if (!this.apiKey) {
            console.log(`[GeminiBackendService] GEMINI_API_KEY not configured in .env. Model: ${this.modelName}, Temp: ${this.temperature}, MaxTokens: ${this.maxOutputTokens}. Using fallback payload.`);
            return null;
        }

        const endpoint = `${this.apiBase}/${this.modelName}:generateContent?key=${this.apiKey}`;
        const payload = {
            contents: [
                {
                    role: 'user',
                    parts: [{ text: `${systemPrompt}\n\n${userPrompt}` }]
                }
            ],
            generationConfig: {
                temperature: this.temperature,
                maxOutputTokens: this.maxOutputTokens,
                responseMimeType: 'application/json'
            }
        };

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`Gemini API Error ${response.status}: ${errText}`);
            }

            const data = await response.json();
            const textResponse = data.candidates?.[0]?.content?.parts?.[0]?.text;

            if (!textResponse) {
                throw new Error('Gemini API returned an empty output candidate');
            }

            return this._cleanAndParseJSON(textResponse);
        } catch (error) {
            console.warn('[GeminiBackendService] API execution warning:', error.message);
            return null;
        }
    }

    /**
     * Generates complete Study Kit using Gemini Backend Service
     */
    /**
     * Helper to split text into semantic chunks of ~1200 words without splitting paragraphs
     */
    _semanticChunking(text, maxWords = 1200) {
        if (!text) return [];
        const paragraphs = text.split(/\n+/);
        const chunks = [];
        let currentChunk = [];
        let currentWordCount = 0;

        for (const para of paragraphs) {
            const cleanPara = para.trim();
            if (!cleanPara) continue;
            
            const words = cleanPara.split(/\s+/).length;
            if (currentWordCount + words > maxWords && currentChunk.length > 0) {
                chunks.push(currentChunk.join('\n\n'));
                currentChunk = [];
                currentWordCount = 0;
            }
            currentChunk.push(cleanPara);
            currentWordCount += words;
        }

        if (currentChunk.length > 0) {
            chunks.push(currentChunk.join('\n\n'));
        }
        return chunks;
    }

    /**
     * Generates complete Study Kit using Gemini Backend Service (Multi-stage Pipeline)
     */
    async generateStudyKit(lessonContent) {
        const text = typeof lessonContent === 'string' ? lessonContent : JSON.stringify(lessonContent);
        console.log(`[GeminiBackendService] Starting multi-stage generation pipeline. Total characters: ${text.length}`);

        // Step 3: Split the lesson into semantic chunks
        const chunks = this._semanticChunking(text, 1200);
        console.log(`[GeminiBackendService] Document split into ${chunks.length} semantic chunks.`);

        // Step 4: Generate a structured summary for EACH chunk in parallel
        const chunkSummarySystem = `Bạn là chuyên gia phân tích tài liệu học thuật. Hãy tóm tắt có cấu trúc đoạn bài giảng sau đây. Nội dung tóm tắt phải làm rõ: chủ đề chính (mainTopic), các khái niệm cốt lõi (keyConcepts) kèm định nghĩa, và mối quan hệ giữa chúng. Trả về JSON: { "mainTopic": "...", "keyConcepts": [{ "concept": "...", "definition": "...", "relationToOthers": "..." }] }`;
        
        console.log(`[GeminiBackendService] Generating structured summaries for each chunk...`);
        const chunkSummaryPromises = chunks.map((chunk, idx) => 
            this.callGemini(chunkSummarySystem, `[Phần ${idx + 1}/${chunks.length}]\nNội dung:\n${chunk}`)
        );
        const chunkSummariesRaw = await Promise.all(chunkSummaryPromises);
        const chunkSummaries = chunkSummariesRaw.filter(c => c !== null);

        // Step 5: Merge all chunk summaries into one complete lesson summary
        console.log(`[GeminiBackendService] Merging chunk summaries into complete lesson summary...`);
        const mergeSummariesSystem = `Bạn là giảng viên AI VLearn. Hãy tổng hợp các phần tóm tắt của các đoạn bài giảng dưới đây thành một bản tóm tắt tổng thể hoàn chỉnh, mạch lạc và sâu sắc cho toàn bộ bài học. Cố gắng giữ lại mọi chi tiết và định nghĩa quan trọng.
Trả về định dạng JSON sau:
{
  "title": "Tiêu đề bài học tổng thể",
  "summary": [
    "Ý tóm tắt chi tiết 1",
    "Ý tóm tắt chi tiết 2",
    "Ý tóm tắt chi tiết 3",
    "Ý tóm tắt chi tiết 4",
    "Ý tóm tắt chi tiết 5"
  ]
}`;
        const summariesInput = JSON.stringify(chunkSummaries, null, 2);
        const finalSummary = await this.callGemini(mergeSummariesSystem, `Danh sách tóm tắt các phần:\n${summariesInput}`) 
            || this._getFallbackSummary();

        // Step 6: Extract ALL lesson concepts from the merged summary
        console.log(`[GeminiBackendService] Extracting all lesson concepts from merged summary...`);
        const conceptExtractionSystem = `Bạn là chuyên gia cấu trúc kiến thức. Hãy trích xuất TẤT CẢ các khái niệm quan trọng từ bản tóm tắt bài học dưới đây. Hãy đảm bảo giữ nguyên quan hệ cha-con (hệ thống phân cấp logic) giữa các khái niệm. Không được bỏ sót các phần nhỏ.
Trả về định dạng JSON duy nhất sau:
{
  "concepts": [
    { "id": "concept-1", "title": "Tên khái niệm", "parentId": null, "description": "Mô tả ngắn gọn khái niệm", "slideNumber": "Slide X" },
    { "id": "concept-2", "title": "Tên khái niệm con", "parentId": "concept-1", "description": "Mô tả ngắn...", "slideNumber": "Slide Y" }
  ]
}`;
        const finalSummaryText = typeof finalSummary === 'object' ? JSON.stringify(finalSummary) : finalSummary;
        const conceptRes = await this.callGemini(conceptExtractionSystem, `Tóm tắt bài học:\n${finalSummaryText}`);
        
        let concepts = [];
        if (conceptRes && Array.isArray(conceptRes.concepts)) {
            concepts = conceptRes.concepts;
        } else {
            // Basic fallback concepts if extraction failed
            concepts = [
                { id: "concept-root", title: "Tổng quan bài học", parentId: null, description: "Nội dung chính của slide", slideNumber: "Slide 1" }
            ];
        }
        console.log(`[GeminiBackendService] Extracted ${concepts.length} concepts.`);

        // Step 7, 8, 9: Parallel generation of Mindmap, Flashcards, and Quizzes ONLY from concepts
        console.log(`[GeminiBackendService] Launching parallel generation for Mindmap, Flashcards, and Quizzes...`);
        const conceptsInput = JSON.stringify(concepts, null, 2);

        const mindmapSystem = `Bạn là chuyên gia thiết kế Sơ đồ tư duy VLearn. Hãy chuyển đổi danh sách các khái niệm được cung cấp dưới đây thành sơ đồ tư duy Mindmap (Nodes & Edges).
YÊU CẦU NGHIÊM NGẶT:
- CHỈ sử dụng các khái niệm có trong danh sách được cung cấp. KHÔNG tự bịa ra khái niệm mới. KHÔNG gộp các chủ đề không liên quan.
- Tạo cấu trúc phân nhánh logic rõ ràng, đầy đủ các nút con.
Trả về định dạng JSON sau:
{
  "title": "Tiêu đề sơ đồ tư duy",
  "nodes": [
    { "id": "node-id", "title": "Tên khái niệm", "relatedSlide": "Slide X", "flashcardIds": ["fc-id"], "quizIds": ["q-id"] }
  ],
  "edges": [
    { "from": "parent-node-id", "to": "child-node-id", "relation": "bao_gồm" }
  ]
}`;

        const flashcardSystem = `Bạn là chuyên gia biên soạn thẻ nhớ ôn tập VLearn. Hãy tạo bộ Flashcards tương ứng với danh sách các khái niệm được cung cấp dưới đây.
YÊU CẦU:
- Mỗi flashcard phải thuộc về đúng 1 khái niệm trong danh sách.
- Không sử dụng kiến thức ngoài. Nếu thiếu thông tin, hãy ghi "Not found in lesson" thay vì tự bịa đặt.
- Tạo tối đa 30 thẻ ôn tập chi tiết.
Trả về định dạng JSON mảng các đối tượng:
[
  {
    "id": "fc-id",
    "concept": "Tên khái niệm (khớp chính xác với danh sách)",
    "definition": "Định nghĩa chi tiết từ bài học",
    "example": "Ví dụ thực tế cụ thể trong bài học",
    "commonMistake": "Sai lầm thường gặp khi hiểu hoặc áp dụng khái niệm này",
    "relatedSlide": "Slide X"
  }
]`;

        const quizSystem = `Bạn là chuyên gia khảo thí học thuật VLearn. Hãy biên soạn bộ câu hỏi trắc nghiệm gồm tối đa 30 câu dựa trên danh sách các khái niệm được cung cấp dưới đây.
YÊU CẦU NGHIÊM NGẶT:
- Chỉ sử dụng các khái niệm có trong bài học, TUYỆT ĐỐI không bịa ra khái niệm mới hay đưa kiến thức ngoài vào câu hỏi.
- Nếu thiếu thông tin để làm câu hỏi, ghi "Not found in lesson" vào các trường dữ liệu tương ứng thay vì tự bịa đặt.
- Mỗi câu hỏi gồm 4 lựa chọn (A, B, C, D) với 1 đáp án đúng và lời giải thích có dẫn chứng slide rõ ràng.
- Độ khó phân bổ Easy, Medium, Hard.
Trả về định dạng JSON mảng chứa tối đa 30 câu hỏi:
[
  {
    "question": "Nội dung câu hỏi?",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correctAnswer": "A. ...",
    "explanation": "Giải thích chi tiết (Dẫn chứng: Slide X)",
    "difficulty": "Easy",
    "concept": "Tên khái niệm"
  }
]`;

        const [mindmapRes, flashcardsRes, quizRes] = await Promise.all([
            this.callGemini(mindmapSystem, `Danh sách khái niệm:\n${conceptsInput}\n\nVà toàn bộ tài liệu để đối chiếu:\n${text}`),
            this.callGemini(flashcardSystem, `Danh sách khái niệm:\n${conceptsInput}\n\nVà toàn bộ tài liệu để đối chiếu:\n${text}`),
            this.callGemini(quizSystem, `Danh sách khái niệm:\n${conceptsInput}\n\nVà toàn bộ tài liệu để đối chiếu:\n${text}`)
        ]);

        console.log(`[GeminiBackendService] Pipeline generation completed.`);

        // Step 10: Generate and return Study Kit JSON
        return {
            summary: finalSummary,
            concepts: concepts,
            mindmap: mindmapRes || this._getFallbackMindmap(),
            flashcards: flashcardsRes || this._getFallbackFlashcards(),
            quiz: quizRes || (this._getFallbackQuiz() ? this._getFallbackQuiz().quizzesByConcept : [])
        };
    }

    /**
     * Evaluates quiz submission using Gemini Backend Service
     */
    async evaluateQuiz(quizResults, lessonContent) {
        const promptSystem = `Bạn là giảng viên AI VLearn. Đánh giá mức độ thuộc bài của học viên từng khái niệm. Trả về JSON mapping concept name sang "Mastered" | "Need Review" | "Weak".`;
        const promptUser = `Kết quả làm bài:\n${JSON.stringify(quizResults, null, 2)}\n\nNội dung bài giảng:\n${lessonContent || ''}`;

        const evalRes = await this.callGemini(promptSystem, promptUser);
        if (evalRes && typeof evalRes === 'object') return evalRes;

        const masteryMap = {};
        if (Array.isArray(quizResults)) {
            quizResults.forEach(item => {
                if (item.concept) {
                    const pct = item.total > 0 ? (item.correct / item.total) * 100 : 0;
                    masteryMap[item.concept] = pct >= 80 ? "Mastered" : pct >= 50 ? "Need Review" : "Weak";
                }
            });
        }
        if (Object.keys(masteryMap).length === 0) {
            masteryMap["Cost of error"] = "Mastered";
            masteryMap["Core JTBD"] = "Need Review";
        }
        return masteryMap;
    }

    _cleanAndParseJSON(rawText) {
        let cleaned = rawText.trim();
        if (cleaned.includes('```json')) {
            cleaned = cleaned.split('```json')[1].split('```')[0].trim();
        } else if (cleaned.includes('```')) {
            cleaned = cleaned.split('```')[1].split('```')[0].trim();
        }
        try {
            return JSON.parse(cleaned);
        } catch (e) {
            console.error('[GeminiBackendService] JSON parse error:', e);
            return null;
        }
    }

    _getFallbackSummary() {
        return {
            title: "Tổng quan Bài học: Xác định bài toán AI & JTBD",
            summary: [
                "Tập trung vào Cost of Error khi chọn bài toán AI",
                "Định hình lát cắt 1 câu: 1 user - 1 việc - 1 quyết định AI - 1 kết quả",
                "Phân biệt rõ ràng giữa Automate và Augment trong thiết kế UX",
                "Cost of Error: Hậu quả và chi phí khi AI đưa ra quyết định sai.",
                "Core JTBD: Công việc cốt lõi người dùng đang cố hoàn thành."
            ]
        };
    }

    _getFallbackMindmap() {
        return {
            title: "Cấu trúc Kiến thức: Xác định bài toán AI & JTBD",
            nodes: [
                { id: "node-root", title: "XÁC ĐỊNH BÀI TOÁN AI", relatedSlide: "Toàn bộ bài", flashcardIds: ["fc-1"], quizIds: ["q-1"] },
                { id: "node-jtbd", title: "User & Job (JTBD)", relatedSlide: "Slide 5-15", flashcardIds: ["fc-2"], quizIds: ["q-2"] },
                { id: "node-criteria", title: "5 Tiêu chí nghiệm thu", relatedSlide: "Slide 16-25", flashcardIds: ["fc-3"], quizIds: ["q-3"] },
                { id: "node-risk", title: "Cost of error & Rủi ro AI", relatedSlide: "Slide 26-40", flashcardIds: ["fc-1", "fc-5"], quizIds: ["q-1"] }
            ],
            edges: [
                { from: "node-root", to: "node-jtbd", relation: "bao_gồm" },
                { from: "node-root", to: "node-criteria", relation: "bao_gồm" },
                { from: "node-root", to: "node-risk", relation: "bao_gồm" }
            ]
        };
    }

    _getFallbackFlashcards() {
        return [
            {
                id: "fc-1",
                concept: "Cost of Error (Chi phí Lỗi)",
                definition: "Chi phí và hậu quả phát sinh khi hệ thống AI đưa ra quyết định sai.",
                simpleExplanation: "Đo lường mức độ nghiêm trọng khi AI đoán nhầm.",
                example: "Trong hệ thống lọc CV tự động, loại nhầm ứng viên giỏi (False Negative) có Cost of Error cao.",
                relatedSlide: "Slide 1"
            },
            {
                id: "fc-2",
                concept: "Core JTBD (Job-To-Be-Done)",
                definition: "Khái niệm xác định công việc cốt lõi mà người dùng đang cố gắng hoàn thành.",
                simpleExplanation: "Tập trung vào mục tiêu của người dùng thay vì tính năng công nghệ.",
                example: "Sinh viên muốn 'tự kiểm tra xem mình có hiểu bài hay không'.",
                relatedSlide: "Slide 2"
            }
        ];
    }

    _getFallbackQuiz() {
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
}

module.exports = new GeminiBackendService();
