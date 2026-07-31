/**
 * AI Controller Module
 * Connects Express REST endpoints with backend Gemini service
 */
const geminiService = require('../services/gemini');

const AIController = {
    /**
     * POST /api/generate-study-kit
     */
    async generateStudyKit(req, res, next) {
        try {
            const { lessonId = '02', lessonContent = '' } = req.body;
            console.log(`[AIController] Generating Study Kit via Gemini Backend Service for Lesson ${lessonId}...`);

            const studyKit = await geminiService.generateStudyKit(lessonContent || `Lesson ${lessonId}`);

            return res.json({
                success: true,
                studyKit
            });
        } catch (error) {
            next(error);
        }
    },

    /**
     * POST /api/evaluate-quiz
     */
    async evaluateQuiz(req, res, next) {
        try {
            const { quizResults, lessonContent = '' } = req.body;
            console.log('[AIController] Evaluating quiz via Gemini Backend Service...');

            const masteryMap = await geminiService.evaluateQuiz(quizResults, lessonContent);

            return res.json({
                success: true,
                masteryMap
            });
        } catch (error) {
            next(error);
        }
    }
};

module.exports = AIController;
