/**
 * AI Companion Client Configuration
 * Communicates exclusively with the Express Backend REST API.
 * No Gemini API keys or direct Gemini endpoints exist in the frontend.
 */
const AI_CONFIG = {
    // Backend API Base Endpoint
    BACKEND_API_BASE: 'http://localhost:3000/api',
    
    // Feature flags & Latency settings
    ENABLE_MOCK_FALLBACK: true,
    SIMULATE_LATENCY_MS: 500,
    
    // Quality Bar Threshold Target
    QUALITY_BAR_PASS_RATE: 0.80
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AI_CONFIG;
}
