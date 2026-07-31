/**
 * LLM Provider Module
 * Frontend API client calling backend Express endpoints (http://localhost:5000/api)
 * Frontend NEVER calls Gemini directly.
 */
class LLMProvider {
    constructor(config = typeof AI_CONFIG !== 'undefined' ? AI_CONFIG : {}) {
        this.config = config;
        this.backendBase = 'http://localhost:3000/api';
    }

    /**
     * Calls Express Backend API
     */
    async generateContent(systemPrompt, userPrompt) {
        try {
            const response = await fetch(`${this.backendBase}/generate-study-kit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ systemPrompt, userPrompt })
            });

            if (!response.ok) {
                throw new Error(`Backend API Error: HTTP ${response.status}`);
            }

            const data = await response.json();
            return data.textOutput || JSON.stringify(data.studyKit || data);
        } catch (error) {
            console.warn('[LLMProvider] Backend API call fallback:', error.message);
            return null;
        }
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = LLMProvider;
}
