const express = require('express');
const router = express.Router();
const aiService = require('../services/ai.service');

/**
 * @route   GET /api/health
 * @desc    Basic liveness and health check endpoint for the Node.js backend
 * @access  Public
 */
router.get('/health', async (req, res) => {
  const checkAi = req.query.checkAi === 'true';
  let aiStatus = null;
  if (checkAi) {
    aiStatus = await aiService.checkHealth();
  }

  res.status(200).json({
    status: 'ok',
    service: 'boardroom-ai-backend',
    timestamp: new Date().toISOString(),
    ...(aiStatus && { aiService: aiStatus })
  });
});

/**
 * @route   GET /api/health/ai
 * @desc    Dedicated liveness check endpoint for the Python AI service
 * @access  Public
 */
router.get('/health/ai', async (req, res) => {
  const aiStatus = await aiService.checkHealth();
  res.status(200).json({
    status: 'ok',
    aiService: aiStatus
  });
});

module.exports = router;

