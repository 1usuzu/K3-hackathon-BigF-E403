/**
 * Summary Service Module
 * Responsibility: Wraps AIService to produce grounded lesson summaries
 * adhering strictly to the max 10 bullet points constraint.
 * 
 * Output Format:
 * {
 *   title: string,
 *   summary: Array<string> // max 10 bullet items
 * }
 */
class SummaryService {
    constructor(aiService = typeof window !== 'undefined' && window.aiService ? window.aiService : new AIService()) {
        this.aiService = aiService;
    }

    /**
     * Generates a grounded summary from merged lesson context
     * @param {string|object} mergedLessonContent 
     * @returns {Promise<{title: string, summary: Array<string>}>}
     */
    async generateLessonSummary(mergedLessonContent) {
        const textContent = typeof mergedLessonContent === 'object' 
            ? (mergedLessonContent.mergedContent || JSON.stringify(mergedLessonContent))
            : String(mergedLessonContent);

        // Call base AIService.generateSummary()
        const rawSummary = await this.aiService.generateSummary(textContent);

        // Format and strictly enforce max 10 bullet points constraint
        const title = rawSummary?.title || 'Tóm tắt Bài học VLearn';
        let bulletPoints = [];

        if (rawSummary && Array.isArray(rawSummary.keyTakeaways)) {
            bulletPoints = rawSummary.keyTakeaways;
        } else if (rawSummary && Array.isArray(rawSummary.summary)) {
            bulletPoints = rawSummary.summary;
        } else if (rawSummary && rawSummary.overview) {
            bulletPoints = [rawSummary.overview];
        }

        // Add core concept definitions if available and space permits
        if (rawSummary?.coreConcepts && Array.isArray(rawSummary.coreConcepts)) {
            rawSummary.coreConcepts.forEach(c => {
                if (c.concept && c.definition && bulletPoints.length < 10) {
                    bulletPoints.push(`${c.concept}: ${c.definition}`);
                }
            });
        }

        // Fallback default bullet points if empty
        if (bulletPoints.length === 0) {
            bulletPoints = [
                "Xác định nỗi đau thực tế của học viên từ chatlog và khảo sát.",
                "Đánh giá rủi ro AI thông qua Cost of Error (False Negative vs False Positive).",
                "Ứng dụng khung JTBD để tìm công việc cốt lõi mà học viên muốn hoàn thành.",
                "Định hình Lát cắt 1 câu: 1 user, 1 việc, 1 quyết định AI, 1 kết quả.",
                "Xây dựng tiêu chí nghiệm thu rõ ràng có thể đo lường qua Golden Set."
            ];
        }

        // Cap strictly at maximum 10 bullet points
        const finalSummary = bulletPoints.slice(0, 10);

        return {
            title,
            summary: finalSummary
        };
    }
}

// Global binding for browser environment
if (typeof window !== 'undefined') {
    window.SummaryService = SummaryService;
    window.summaryService = new SummaryService();
}

// Module export for Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SummaryService;
}
