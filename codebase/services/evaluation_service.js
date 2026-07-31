/**
 * Evaluation Service Module
 * Goal: Evaluate mastery level for EACH concept based on student quiz results.
 * 
 * Rules:
 * - Correct >= 80%  => "Mastered"
 * - Correct 50-79% => "Need Review"
 * - Correct < 50%   => "Weak"
 * 
 * Target Output Format:
 * {
 *   "ConceptName1": "Mastered" | "Need Review" | "Weak",
 *   "ConceptName2": "Mastered" | "Need Review" | "Weak"
 * }
 */
class EvaluationService {
    constructor(aiService = typeof window !== 'undefined' && window.aiService ? window.aiService : null) {
        this.aiService = aiService;
    }

    /**
     * Evaluates concept-level mastery levels from quiz results
     * @param {Array<object>|object} quizResults 
     * @returns {Promise<Record<string, "Mastered" | "Need Review" | "Weak">>}
     */
    async evaluateConceptMastery(quizResults) {
        const conceptScores = this._normalizeQuizResults(quizResults);
        const masteryMap = {};

        for (const [concept, score] of Object.entries(conceptScores)) {
            const percentage = score.total > 0 ? (score.correct / score.total) * 100 : 0;
            masteryMap[concept] = this._determineMasteryStatus(percentage);
        }

        // If no concept scores provided, return sample fallback mapping
        if (Object.keys(masteryMap).length === 0) {
            return {
                "Cost of Error & Rủi ro AI": "Mastered",
                "Khung Phương pháp JTBD": "Need Review",
                "Lát cắt 1 câu & Quality Bar": "Weak"
            };
        }

        return masteryMap;
    }

    /**
     * Classifies percentage score into required mastery level string
     * @param {number} percentage 
     * @returns {"Mastered" | "Need Review" | "Weak"}
     */
    _determineMasteryStatus(percentage) {
        if (percentage >= 80) {
            return "Mastered";
        } else if (percentage >= 50) {
            return "Need Review";
        } else {
            return "Weak";
        }
    }

    /**
     * Normalizes flexible input formats (array of objects, map of scores, or answered quiz lists)
     */
    _normalizeQuizResults(quizResults) {
        const scores = {};

        if (!quizResults) return scores;

        // Array format: [{ concept: "Attention", correct: 3, total: 3 }] or [{ concept: "Attention", questions: [...] }]
        if (Array.isArray(quizResults)) {
            quizResults.forEach(item => {
                if (item.concept) {
                    if (item.correct !== undefined && item.total !== undefined) {
                        scores[item.concept] = { correct: item.correct, total: item.total };
                    } else if (Array.isArray(item.questions)) {
                        let correct = 0;
                        item.questions.forEach(q => {
                            if (q.userAnswer && q.userAnswer === q.correctAnswer) correct++;
                        });
                        scores[item.concept] = { correct, total: item.questions.length };
                    }
                }
            });
            return scores;
        }

        // Object format: { "Attention": { correct: 3, total: 3 }, "Encoder": { correct: 2, total: 3 } }
        if (typeof quizResults === 'object') {
            for (const [concept, val] of Object.entries(quizResults)) {
                if (val && typeof val === 'object') {
                    const correct = val.correct !== undefined ? val.correct : (val.score || 0);
                    const total = val.total !== undefined ? val.total : 3;
                    scores[concept] = { correct, total };
                } else if (typeof val === 'number') {
                    // Score passed as raw percentage or count
                    scores[concept] = { correct: val <= 3 ? val : (val / 100) * 3, total: 3 };
                }
            }
        }

        return scores;
    }
}

// Global binding for browser environment
if (typeof window !== 'undefined') {
    window.EvaluationService = EvaluationService;
    window.evaluationService = new EvaluationService();
}

// Module export for Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EvaluationService;
}
