/**
 * Lightweight Express Backend for AI Study Companion
 */
const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const aiRoutes = require('./routes/ai');
const errorHandler = require('./middleware/errorHandler');

const app = express();
const PORT = process.env.PORT || 5000;

// Enable CORS and Body Parser
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Health Check Endpoint
app.get('/api/health', (req, res) => {
    res.json({
        status: 'OK',
        uptime: process.uptime(),
        timestamp: new Date().toISOString(),
        service: 'AI Study Companion Express Backend'
    });
});

// Mount AI REST Routes
app.use('/api', aiRoutes);

// Global Error Handler
app.use(errorHandler);

// Start Server
if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`\n==================================================`);
        console.log(`🚀 AI Study Companion Express Server Running`);
        console.log(`📡 Port: http://localhost:${PORT}`);
        console.log(`🏥 Health Check: http://localhost:${PORT}/api/health`);
        console.log(`==================================================\n`);
    });
}

module.exports = app;
