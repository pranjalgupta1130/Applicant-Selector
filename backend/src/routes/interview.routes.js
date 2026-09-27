const express = require('express');
const router = express.Router();
const interviewController = require('../controllers/interview.controller');

/**
 * @route   POST /api/interviews
 * @desc    Create interview session
 * @access  Public
 */
router.post('/', interviewController.createInterview);

/**
 * @route   GET /api/interviews/:id
 * @desc    Fetch interview session state
 * @access  Public
 */
router.get('/:id', interviewController.getInterviewById);

/**
 * @route   POST /api/interviews/:id/start
 * @desc    Start/initialize interview session stage progression
 * @access  Public
 */
router.post('/:id/start', interviewController.startInterview);

/**
 * @route   POST /api/interviews/:id/questions
 * @desc    Persist a new question attached to an interview (Task 6)
 * @access  Public
 */
router.post('/:id/questions', interviewController.createInterviewQuestion);

/**
 * @route   GET /api/interviews/:id/questions
 * @desc    Retrieve all persisted questions for an interview (Task 6)
 * @access  Public
 */
router.get('/:id/questions', interviewController.getInterviewQuestions);

/**
 * @route   GET /api/interviews/:id/questions/:questionId
 * @desc    Retrieve a single persisted question by ID (Task 6)
 * @access  Public
 */
router.get('/:id/questions/:questionId', interviewController.getInterviewQuestionById);

/**
 * @route   POST /api/interviews/:id/answers
 * @desc    Persist candidate answer submission (Task 6/8)
 * @access  Public
 */
router.post('/:id/answers', interviewController.submitAnswer);

/**
 * @route   GET /api/interviews/:id/report
 * @desc    Generate / fetch final evaluation report for an interview (Task 9)
 * @access  Public
 */
router.get('/:id/report', interviewController.getInterviewReport);

module.exports = router;
