const interviewService = require('../services/interview.service');
const closedLoop = require('../services/closed-loop-interview.service');

/**
 * Controller: POST /api/interviews
 */
const createInterview = async (req, res, next) => {
  try {
    const interview = await closedLoop.createInterview(req.body);
    res.status(201).json({
      success: true,
      data: interview
    });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

/**
 * Controller: GET /api/interviews/:id
 */
const getInterviewById = async (req, res, next) => {
  try {
    const interview = await closedLoop.getInterview(req.params.id);
    res.status(200).json({
      success: true,
      data: interview
    });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

/**
 * Controller: POST /api/interviews/:id/start
 */
const startInterview = async (req, res, next) => {
  try {
    const interview = await closedLoop.startInterview(req.params.id);
    res.status(200).json({
      success: true,
      data: interview
    });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

/**
 * Controller: POST /api/interviews/:id/questions (Task 6)
 */
const createInterviewQuestion = async (req, res, next) => {
  try {
    const question = await interviewService.createInterviewQuestion(req.params.id, req.body);
    res.status(201).json({
      success: true,
      data: question
    });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

/**
 * Controller: GET /api/interviews/:id/questions (Task 6)
 */
const getInterviewQuestions = async (req, res, next) => {
  try {
    const questions = await interviewService.getInterviewQuestions(req.params.id);
    res.status(200).json({
      success: true,
      count: questions.length,
      data: questions
    });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

/**
 * Controller: GET /api/interviews/:id/questions/:questionId (Task 6)
 */
const getInterviewQuestionById = async (req, res, next) => {
  try {
    const question = await interviewService.getInterviewQuestionById(req.params.id, req.params.questionId);
    res.status(200).json({
      success: true,
      data: question
    });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

/**
 * Controller: POST /api/interviews/:id/answers (Task 6)
 */
const submitAnswer = async (req, res, next) => {
  try {
    const answer = await closedLoop.submitAnswer(req.params.id, req.body);
    res.status(201).json({
      success: true,
      data: answer
    });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

/**
 * Controller: GET /api/interviews/:id/report (Task 9)
 */
const getInterviewReport = async (req, res, next) => {
  try {
    const report = await closedLoop.getReport(req.params.id);
    res.status(200).json({
      success: true,
      data: report
    });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

const recordIntegrity = async (req, res, next) => {
  try {
    const data = await closedLoop.recordIntegrity(req.params.id, req.body.events, req.body.status);
    res.status(200).json({ success: true, data });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

module.exports = {
  createInterview,
  getInterviewById,
  startInterview,
  createInterviewQuestion,
  getInterviewQuestions,
  getInterviewQuestionById,
  submitAnswer,
  getInterviewReport,
  recordIntegrity
};
