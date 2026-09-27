const express = require('express');
const router = express.Router();
const candidateController = require('../controllers/candidate.controller');

/**
 * @route   POST /api/candidates
 * @desc    Create candidate profile
 * @access  Public
 */
router.post('/', candidateController.createCandidate);

/**
 * @route   POST /api/candidates/:id/resume
 * @desc    Upload or update candidate resume reference/URL
 * @access  Public
 */
router.post('/:id/resume', candidateController.updateCandidateResume);

/**
 * @route   GET /api/candidates/:id
 * @desc    Get candidate profile by ID
 * @access  Public
 */
router.get('/:id', candidateController.getCandidateById);

module.exports = router;
