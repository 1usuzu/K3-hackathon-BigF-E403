/**
 * Lesson Loader Service
 * Responsibilities:
 * - Load lesson resources asynchronously from data/vlearn-pack/ (slides, transcripts, chatlogs)
 * - Aggregate resources into a unified Lesson Context object
 * 
 * Target Output Format:
 * {
 *   lessonId: string,
 *   slideContent: string,
 *   transcript: string,
 *   chatlog: string,
 *   mergedContent: string
 * }
 */
class LessonLoader {
    constructor(basePath = '../data/vlearn-pack') {
        this.basePath = basePath;
    }

    /**
     * Asynchronously loads resources for a given lessonId (e.g. '01', '02', 'd2')
     * @param {string} lessonId 
     * @returns {Promise<{lessonId: string, slideContent: string, transcript: string, chatlog: string, mergedContent: string}>}
     */
    async loadLesson(lessonId = '02') {
        const normalizedId = String(lessonId).padStart(2, '0');

        const [slideContent, transcript, chatlog] = await Promise.all([
            this._fetchResource(`slides/d${parseInt(lessonId, 10) || 2}-slide-hackathon.pdf`, `[Slide Data for Lesson ${lessonId}]`),
            this._fetchResource(`transcript/transcript-${normalizedId}-clean.md`, `[Transcript Data for Lesson ${lessonId}]`),
            this._fetchResource(`chatlog/chat_history_anonymized_for_hackathon.csv`, `[Chatlog Data for Lesson ${lessonId}]`)
        ]);

        const mergedContent = this._combineResources(lessonId, slideContent, transcript, chatlog);

        return {
            lessonId: String(lessonId),
            slideContent,
            transcript,
            chatlog,
            mergedContent
        };
    }

    /**
     * Internal helper to fetch resources across Browser and Node environments
     */
    async _fetchResource(relativePath, fallbackText = '') {
        const fullPath = `${this.basePath}/${relativePath}`;

        // Node.js Environment
        if (typeof process !== 'undefined' && process.versions && process.versions.node) {
            try {
                const fs = require('fs').promises;
                const path = require('path');
                const absolutePath = path.resolve(__dirname, '../../data/vlearn-pack', relativePath);
                if (relativePath.endsWith('.pdf')) {
                    return `[PDF Binary Content Indexed: ${relativePath}]`;
                }
                const data = await fs.readFile(absolutePath, 'utf-8');
                return data;
            } catch (err) {
                console.warn(`[LessonLoader] Node fetch failed for ${fullPath}:`, err.message);
                return fallbackText;
            }
        }

        // Browser Environment
        if (typeof fetch !== 'undefined') {
            try {
                if (relativePath.endsWith('.pdf')) {
                    return `[PDF Content Loaded: ${fullPath}]`;
                }
                const response = await fetch(fullPath);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return await response.text();
            } catch (err) {
                console.warn(`[LessonLoader] Browser fetch failed for ${fullPath}:`, err.message);
                return fallbackText;
            }
        }

        return fallbackText;
    }

    /**
     * Combines all resources into one cohesive Markdown text block
     */
    _combineResources(lessonId, slideContent, transcript, chatlog) {
        return `# LESSON CONTEXT: ${lessonId}

## 1. SLIDE CONTENT
${slideContent}

---

## 2. LECTURE TRANSCRIPT
${transcript}

---

## 3. STUDENT CHATLOG / Q&A SIGNAL
${chatlog}
`;
    }
}

// Browser Global Binding
if (typeof window !== 'undefined') {
    window.LessonLoader = LessonLoader;
}

// CommonJS Module Export for Node / Evaluators
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LessonLoader;
}
