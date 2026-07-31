/**
 * Robust JSON parsing utility for cleaning and extracting JSON from LLM outputs.
 */
const JSONParser = {
    /**
     * Extracts and parses JSON from raw LLM text string.
     * Handles markdown block wrapping (```json ... ```), preamble, or postscript text.
     * @param {string} rawText 
     * @returns {object|null} Parsed JSON object or null if invalid
     */
    cleanAndParse(rawText) {
        if (!rawText || typeof rawText !== 'string') return null;
        
        let cleaned = rawText.trim();
        
        // Remove markdown codeblock syntax if present
        if (cleaned.includes('```json')) {
            cleaned = cleaned.split('```json')[1].split('```')[0].trim();
        } else if (cleaned.includes('```')) {
            cleaned = cleaned.split('```')[1].split('```')[0].trim();
        }
        
        // Find first '{' or '[' and last '}' or ']'
        const firstCurly = cleaned.indexOf('{');
        const firstSquare = cleaned.indexOf('[');
        
        let startIndex = -1;
        let isArray = false;
        
        if (firstCurly !== -1 && (firstSquare === -1 || firstCurly < firstSquare)) {
            startIndex = firstCurly;
        } else if (firstSquare !== -1) {
            startIndex = firstSquare;
            isArray = true;
        }
        
        if (startIndex !== -1) {
            const endIndex = isArray ? cleaned.lastIndexOf(']') : cleaned.lastIndexOf('}');
            if (endIndex > startIndex) {
                cleaned = cleaned.substring(startIndex, endIndex + 1);
            }
        }
        
        try {
            return JSON.parse(cleaned);
        } catch (e) {
            console.error('[JSONParser] Failed to parse JSON:', e, '\nOriginal Text:', rawText);
            return null;
        }
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = JSONParser;
}
