/**
 * Express AI Routes Module
 */
const express = require('express');
const router = express.Router();
const aiController = require('../controllers/aiController');

// POST /api/generate-study-kit
router.post('/generate-study-kit', aiController.generateStudyKit);

// POST /api/evaluate-quiz
router.post('/evaluate-quiz', aiController.evaluateQuiz);

module.exports = router;
