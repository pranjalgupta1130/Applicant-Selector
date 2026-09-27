const candidateService = require('../services/candidate.service');

/**
 * Controller: POST /api/candidates
 */
const createCandidate = async (req, res, next) => {
  try {
    const candidate = await candidateService.createCandidate(req.body);
    res.status(201).json({
      success: true,
      data: candidate
    });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

/**
 * Controller: POST /api/candidates/:id/resume
 */
const updateCandidateResume = async (req, res, next) => {
  try {
    const candidate = await candidateService.updateCandidateResume(req.params.id, req.body);
    res.status(200).json({
      success: true,
      data: candidate
    });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

/**
 * Controller: GET /api/candidates/:id
 */
const getCandidateById = async (req, res, next) => {
  try {
    const candidate = await candidateService.getCandidateById(req.params.id);
    res.status(200).json({
      success: true,
      data: candidate
    });
  } catch (error) {
    res.status(error.statusCode || 500);
    next(error);
  }
};

module.exports = {
  createCandidate,
  updateCandidateResume,
  getCandidateById
};
