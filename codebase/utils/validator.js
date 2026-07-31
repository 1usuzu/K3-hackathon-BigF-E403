/**
 * Schema Validation Utility for Mindmap and Flashcard AI outputs.
 */
const SchemaValidator = {
    /**
     * Validates Mindmap structure
     * Expected format: { title: string, slideSource: string, children: Array<{ title: string, slideSource: string, children?: Array }> }
     */
    validateMindmap(data) {
        if (!data || typeof data !== 'object') return { valid: false, reason: 'Root object missing or invalid' };
        if (!data.title || typeof data.title !== 'string') return { valid: false, reason: 'Mindmap root title missing' };
        if (!Array.isArray(data.children) || data.children.length === 0) {
            return { valid: false, reason: 'Mindmap root must contain at least one child node' };
        }

        const validateNode = (node, depth = 1) => {
            if (!node.title) return false;
            if (node.children) {
                if (!Array.isArray(node.children)) return false;
                for (const child of node.children) {
                    if (!validateNode(child, depth + 1)) return false;
                }
            }
            return true;
        };

        for (const child of data.children) {
            if (!validateNode(child)) {
                return { valid: false, reason: 'Child node missing required properties' };
            }
        }

        return { valid: true };
    },

    /**
     * Validates Flashcard array structure
     * Expected format: Array<{ question: string, options: Array<string>, answer: string, slideSource: string }>
     */
    validateFlashcards(cards) {
        if (!Array.isArray(cards) || cards.length === 0) {
            return { valid: false, reason: 'Flashcards output must be a non-empty array' };
        }

        for (let i = 0; i < cards.length; i++) {
            const card = cards[i];
            if (!card.question || typeof card.question !== 'string') {
                return { valid: false, reason: `Card #${i + 1} missing question` };
            }
            if (!Array.isArray(card.options) || card.options.length < 2) {
                return { valid: false, reason: `Card #${i + 1} must have at least 2 options` };
            }
            if (!card.answer || typeof card.answer !== 'string') {
                return { valid: false, reason: `Card #${i + 1} missing correct answer` };
            }
        }

        return { valid: true };
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = SchemaValidator;
}
