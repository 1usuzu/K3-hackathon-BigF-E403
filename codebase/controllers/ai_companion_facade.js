/**
 * AI Companion Facade
 * Unified pipeline orchestrator implementing the full end-to-end flow:
 * Lesson -> Lesson Loader -> Summary Service -> Mindmap Service -> Flashcard Service -> Quiz Service -> Frontend Output
 * 
 * Target Output Study Kit:
 * {
 *   summary: { title: string, summary: Array<string> },
 *   mindmap: { title: string, nodes: Array<object>, edges: Array<object> },
 *   flashcards: Array<object>,
 *   quiz: { quizzesByConcept: Array<object> }
 * }
 */
class AICompanionFacade {
    constructor() {
        this.aiService = typeof window !== 'undefined' && window.aiService ? window.aiService : new AIService();
        this.lessonLoader = typeof window !== 'undefined' && window.lessonLoader ? window.lessonLoader : new LessonLoader();
        this.summaryService = typeof window !== 'undefined' && window.summaryService ? window.summaryService : new SummaryService(this.aiService);
        this.mindmapService = typeof window !== 'undefined' && window.mindmapService ? window.mindmapService : new MindmapService(this.aiService);
        this.flashcardService = typeof window !== 'undefined' && window.flashcardService ? window.flashcardService : new FlashcardService(this.aiService);
        this.quizService = typeof window !== 'undefined' && window.quizService ? window.quizService : new QuizService(this.aiService);
        this.evaluationService = typeof window !== 'undefined' && window.evaluationService ? window.evaluationService : new EvaluationService(this.aiService);
    }

    /**
     * Executes full Study Kit pipeline for a given lessonId
     * @param {string} lessonId 
     * @returns {Promise<{success: boolean, studyKit: {summary: object, mindmap: object, flashcards: Array<object>, quiz: object}, error?: string}>}
     */
    async generateFullStudyKit(lessonId = '02') {
        try {
            console.log(`[AICompanionFacade] Executing Full Study Kit Pipeline for Lesson ${lessonId}...`);

            // Step 1: Lesson -> Lesson Loader
            const lessonContext = await this.lessonLoader.loadLesson(lessonId);

            // Step 2-5: Parallel Execution of Summary, Mindmap, Flashcard, and Quiz Services
            const [summary, mindmap, flashcards, quiz] = await Promise.all([
                this.summaryService.generateLessonSummary(lessonContext.mergedContent),
                this.mindmapService.extractKnowledgeStructure(lessonContext.mergedContent),
                this.flashcardService.generateConceptFlashcards(lessonContext.mergedContent),
                this.quizService.generateConceptQuizzes(lessonContext.mergedContent)
            ]);

            const studyKit = {
                summary,
                mindmap,
                flashcards,
                quiz
            };

            console.log('[AICompanionFacade] Pipeline execution finished successfully.');
            return {
                success: true,
                studyKit
            };
        } catch (error) {
            console.error('[AICompanionFacade] Pipeline execution failed:', error);
            return {
                success: false,
                error: error.message || 'Lỗi xử lý luồng AI Study Kit',
                studyKit: null
            };
        }
    }

    /**
     * Executes full Study Kit pipeline for a given raw text content
     * @param {string} textContent
     * @returns {Promise<{success: boolean, studyKit: {summary: object, mindmap: object, flashcards: Array<object>, quiz: object}, error?: string}>}
     */
    async generateStudyKitFromText(textContent) {
        try {
            console.log(`[AICompanionFacade] Executing Full Study Kit Pipeline for provided text...`);

            const [summary, mindmap, flashcards, quiz] = await Promise.all([
                this.summaryService.generateLessonSummary(textContent),
                this.mindmapService.extractKnowledgeStructure(textContent),
                this.flashcardService.generateConceptFlashcards(textContent),
                this.quizService.generateConceptQuizzes(textContent)
            ]);

            const studyKit = {
                summary,
                mindmap,
                flashcards,
                quiz
            };

            console.log('[AICompanionFacade] Pipeline execution finished successfully.');
            return {
                success: true,
                studyKit
            };
        } catch (error) {
            console.error('[AICompanionFacade] Pipeline execution failed:', error);
            return {
                success: false,
                error: error.message || 'Lỗi xử lý luồng AI Study Kit',
                studyKit: null
            };
        }
    }

    /**
     * Legacy method alias
     */
    async generateStudyPack(lessonId = '02') {
        const res = await this.generateFullStudyKit(lessonId);
        if (res.success && res.studyKit) {
            return {
                success: true,
                mindmap: res.studyKit.mindmap,
                flashcards: res.studyKit.flashcards
            };
        }
        return res;
    }
}

// Global browser binding
if (typeof window !== 'undefined') {
    window.AICompanionFacade = AICompanionFacade;
    window.aiCompanionFacade = new AICompanionFacade();
}

// CommonJS module export for Node environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AICompanionFacade;
}
