const { Candidate } = require('../models');
const { isValidId } = require('../storage/jsonStore');

/**
 * Service: Create a Candidate Profile
 */
const createCandidate = async (candidateData) => {
  const { name, email, experience, education, extractedSkills, resumeUrl } = candidateData;

  if (!name || typeof name !== 'string' || !name.trim()) {
    const err = new Error('Candidate name is required');
    err.statusCode = 400;
    throw err;
  }

  if (extractedSkills !== undefined && !Array.isArray(extractedSkills)) {
    const err = new Error('extractedSkills must be an array of strings');
    err.statusCode = 400;
    throw err;
  }

  const normalized = {
    name: name.trim(),
    email: email ? email.trim() : '',
    experience: experience ? experience.trim() : '',
    education: education ? education.trim() : '',
    extractedSkills: extractedSkills || [],
    resumeUrl: resumeUrl ? resumeUrl.trim() : ''
  };
  const existing = normalized.email ? await Candidate.findByEmail(normalized.email) : null;
  const newCandidate = existing
    ? await Candidate.findByIdAndUpdate(existing._id, normalized)
    : await Candidate.create(normalized);

  return newCandidate;
};

/**
 * Service: Update Candidate Resume Reference / URL
 */
const updateCandidateResume = async (id, { resumeUrl }) => {
  if (!isValidId(id)) {
    const err = new Error(`Invalid candidate ID format: ${id}`);
    err.statusCode = 400;
    throw err;
  }

  if (!resumeUrl || typeof resumeUrl !== 'string' || !resumeUrl.trim()) {
    const err = new Error('resumeUrl is required to update resume reference');
    err.statusCode = 400;
    throw err;
  }

  const candidate = await Candidate.findByIdAndUpdate(
    id,
    { resumeUrl: resumeUrl.trim() }
  );

  if (!candidate) {
    const err = new Error(`Candidate not found with ID: ${id}`);
    err.statusCode = 404;
    throw err;
  }

  return candidate;
};

/**
 * Service: Get Candidate by ID
 */
const getCandidateById = async (id) => {
  if (!isValidId(id)) {
    const err = new Error(`Invalid candidate ID format: ${id}`);
    err.statusCode = 400;
    throw err;
  }

  const candidate = await Candidate.findById(id);

  if (!candidate) {
    const err = new Error(`Candidate not found with ID: ${id}`);
    err.statusCode = 404;
    throw err;
  }

  return candidate;
};

module.exports = {
  createCandidate,
  updateCandidateResume,
  getCandidateById
};
