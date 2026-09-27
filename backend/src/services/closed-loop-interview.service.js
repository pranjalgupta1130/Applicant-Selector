const { Interview, Candidate, Role, InterviewQuestion, Answer, Evaluation, Report } = require('../models');
const { isValidId } = require('../storage/jsonStore');

const AI_URL = (process.env.AI_SERVICE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

async function callPython(path, payload) {
  let response;
  try {
    response = await fetch(`${AI_URL}/api/${path}`, {
      method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload)
    });
  } catch (cause) {
    const error = new Error(`Python AI service is unavailable at ${AI_URL}: ${cause.message}`);
    error.statusCode = 503;
    throw error;
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.detail || `Python AI service returned ${response.status}`);
    error.statusCode = 502;
    throw error;
  }
  return body;
}

const numericExperience = (value) => {
  const match = String(value || '').match(/[\d.]+/);
  return match ? Number(match[0]) : 0;
};

function toCandidate(candidate) {
  const skills = candidate.extractedSkills || [];
  const text = `${candidate.name || ''} ${skills.join(' ')}`.toLowerCase();
  let domain = 'cyber_computing';
  if (/radar|signal|dsp|electronics/.test(text)) domain = 'electronics_radar';
  else if (/aero|fluid|cfd|compressible|aerodynamic/.test(text)) domain = 'aerospace_aerodynamics';
  else if (/cyber|network|security/.test(text)) domain = 'cyber_computing';
  return {
    id: candidate._id, name: candidate.name, skills,
    experience_years: numericExperience(candidate.experience), education: candidate.education || '',
    specialization: skills.join(', '), claimed_expertise: skills, domain
  };
}

function toRole(role) {
  const text = `${role.title || ''} ${role.description || ''}`.toLowerCase();
  let domain = 'cyber_computing';
  if (/radar|signal|dsp|electronics/.test(text)) domain = 'electronics_radar';
  else if (/aero|fluid|cfd|aerodynamic/.test(text)) domain = 'aerospace_aerodynamics';
  else if (/cyber|network|security/.test(text)) domain = 'cyber_computing';
  const competencies = Array.isArray(role.competencies)
    ? role.competencies.map((c) => typeof c === 'string' ? c : c.name).filter(Boolean)
    : [];
  const evidenceRequirements = {
    electronics_radar: ['Nyquist-Shannon Sampling Theorem', 'Adaptive Beamforming', 'Radar Range Equation', 'Interrupt Latency & ISRs'],
    aerospace_aerodynamics: ['Navier-Stokes equations', 'finite-volume discretization', 'mesh independence', 'boundary-layer separation', 'Mach number'],
    cyber_computing: ['threat modeling', 'network segmentation', 'least privilege', 'incident triage', 'recovery']
  }[role.domain || domain] || competencies;
  return {
    id: role.aiRoleId || role._id, title: role.title, description: role.description,
    required_skills: evidenceRequirements, technical_requirements: evidenceRequirements, domain: role.domain || domain,
    discipline: domain === 'electronics_radar' ? 'Electronics & Communication Engineering' : domain === 'aerospace_aerodynamics' ? 'Aeronautical Engineering' : 'Computer Science & Engineering'
  };
}

function questionFields(q) {
  return {
    questionId: q.id, text: q.text, stage: q.stage, competency: q.competency,
    difficulty: q.difficulty, expectedConcepts: q.expectedConcepts || [],
    relevanceScore: Number(q.relevanceScore || 0) / (Number(q.relevanceScore || 0) > 1 ? 100 : 1),
    rubric: q.rubric || null, sourceChunkIds: q.sources || [], generated: !q.isFallback
  };
}

function questionDiagnostics(question, interview) {
  const explanation = question?.questionExplanation || {};
  return question ? {
    retrievalInvoked: explanation.retrieval_invoked === true,
    retrievalCount: explanation.retrieval_count || 0,
    retrievalMode: explanation.retrieval_mode || 'unknown',
    retrievalScores: (explanation.retrieved_sources || []).map((source) => ({ id: source.id, title: source.title, score: source.score, domain: source.domain })),
    contextReachedGeneration: explanation.context_reached_generation === true,
    question: question.text, candidateExpertise: interview.candidateSnapshot.claimed_expertise,
    advertisedPost: interview.roleSnapshot.title, competency: question.competency,
    stage: question.stage, retrievedSources: question.sources || [],
    questionRelevanceScore: question.relevanceScore, isFallback: question.isFallback,
    generationMode: explanation.generation_mode || (question.isFallback ? 'curated_fallback' : 'unknown')
  } : null;
}

async function createInterview(input) {
  const { candidateId, roleId, targetCompetencies } = input;
  if (!isValidId(candidateId) || !isValidId(roleId)) {
    const error = new Error('Valid candidateId and roleId are required'); error.statusCode = 400; throw error;
  }
  const [candidate, role] = await Promise.all([Candidate.findById(candidateId), Role.findById(roleId).populate('competencies')]);
  if (!candidate || !role) { const error = new Error(!candidate ? 'Candidate not found' : 'Role not found'); error.statusCode = 404; throw error; }
  const comps = targetCompetencies || (role.competencies || []).map((c) => typeof c === 'object' ? c.name : c).filter(Boolean);
  const interview = await Interview.create({ candidateId, roleId, targetCompetencies: comps, status: 'created', currentStage: 'ice_breaker', candidateSnapshot: toCandidate(candidate), roleSnapshot: toRole(role) });
  return interview;
}

async function getInterview(id) {
  const interview = await Interview.findById(id);
  if (!interview) { const error = new Error('Interview session not found'); error.statusCode = 404; throw error; }
  return interview;
}

async function persistQuestion(interview, question) {
  if (!question) return null;
  const saved = await InterviewQuestion.create({ interviewId: interview._id, ...questionFields(question), sequence: (interview.questionSequence || 0) + 1 });
  interview.currentQuestionId = saved._id;
  interview.currentStage = saved.stage;
  interview.questionSequence = saved.sequence;
  interview.questionsAsked = (interview.questionsAsked || 0) + 1;
  interview.aiActiveQuestion = question;
  await interview.save();
  return { ...saved, id: saved._id, _id: saved._id };
}

async function startInterview(id) {
  const interview = await getInterview(id);
  if (interview.status === 'in_progress' && interview.aiActiveQuestion) return { ...interview, question: interview.aiActiveQuestion };
  if (interview.status !== 'created') { const error = new Error(`Cannot start interview in '${interview.status}' status`); error.statusCode = 400; throw error; }
  const result = await callPython('interview/start', { candidate: interview.candidateSnapshot, role: interview.roleSnapshot });
  interview.aiState = result.interviewState;
  interview.status = 'in_progress';
  interview.startedAt = new Date().toISOString();
  await interview.save();
  const question = await persistQuestion(interview, result.openingQuestion);
  console.info('[Live RAG question]', JSON.stringify({ interviewId: id, ...questionDiagnostics(result.openingQuestion, interview) }));
  return { ...interview, question };
}

async function submitAnswer(id, body) {
  const interview = await getInterview(id);
  if (interview.status !== 'in_progress') { const error = new Error(`Interview is ${interview.status}`); error.statusCode = 400; throw error; }
  if (!interview.aiActiveQuestion) { const error = new Error('Interview has no active question'); error.statusCode = 409; throw error; }
  const answerText = String(body.answerText || '').trim();
  if (!answerText) { const error = new Error('answerText is required'); error.statusCode = 400; throw error; }
  if (body.interviewQuestionId && body.interviewQuestionId !== interview.currentQuestionId) { const error = new Error('Answer does not match the active question'); error.statusCode = 409; throw error; }

  const result = await callPython('interview/turn', {
    interviewState: interview.aiState, currentQuestion: interview.aiActiveQuestion,
    candidateAnswer: answerText, candidate: interview.candidateSnapshot, role: interview.roleSnapshot
  });
  const answer = await Answer.create({ interviewQuestionId: interview.currentQuestionId, answerText, transcript: body.transcript || '' });
  const ev = result.evaluation || {};
  const subs = ev.subScores || {};
  const toTen = (v) => Math.max(0, Math.min(10, Number(v || 0) / 10));
  const toTenOrNull = (v) => (v === null || v === undefined) ? null : Math.max(0, Math.min(10, Number(v) / (Number(v) > 10 ? 10 : 1)));
  const evaluation = await Evaluation.create({
    answerId: answer._id,
    relevance: toTenOrNull(subs.relevance),
    technicalCorrectness: subs.technicalCorrectness === null ? null : toTenOrNull(subs.technicalCorrectness ?? ev.score),
    completeness: toTenOrNull(subs.completeness),
    reasoning: toTenOrNull(subs.depth),
    clarity: toTenOrNull(subs.clarity),
    total: toTen(ev.score),
    coveredConcepts: ev.coveredConcepts || [],
    missingConcepts: ev.missingConcepts || [],
    feedback: ev.reasoning || '',
    confidence: ev.confidence,
    nextQuestionStrategy: result.decision?.reason || result.decision?.strategy || ''
  });
  interview.aiState = result.updatedState;
  const nextQuestion = await persistQuestion(interview, result.nextQuestion);
  const pythonStage = result.nextQuestion ? result.nextQuestion.stage : (result.decision?.nextStage || 'closing');
  const nodePersistedStage = interview.currentStage;
  const nextRequestStage = nextQuestion ? nextQuestion.stage : 'closing';
  console.info('[STAGE TRACK]', JSON.stringify({ PYTHON_STAGE: pythonStage, NODE_PERSISTED_STAGE: nodePersistedStage, NEXT_REQUEST_STAGE: nextRequestStage }));
  let report = null;
  if (result.termination?.shouldTerminate || !result.nextQuestion) {
    report = await finalizeInterview(interview);
  }
  const diagnostics = questionDiagnostics(result.nextQuestion, interview);
  if (diagnostics) console.info('[Live RAG question]', JSON.stringify({ interviewId: id, ...diagnostics }));
  return { answer, evaluation, nextQuestion, decision: result.decision, trace: result.trace, termination: result.termination, report, diagnostics };
}

async function finalizeInterview(interview) {
  if (interview.scorecard) return interview.scorecard;
  const scorecard = await callPython('interview/scorecard', { interviewState: interview.aiState, candidate: interview.candidateSnapshot, role: interview.roleSnapshot });
  interview.scorecard = scorecard;
  interview.status = 'completed';
  interview.completedAt = new Date().toISOString();
  await interview.save();
  const core = scorecard.scorecard || {};
  const report = await Report.create({
    interviewId: interview._id, overallScore: core.subjectKnowledgeScore ?? core.overallScore ?? 0,
    competencyScores: (scorecard.competencies || []).map((c) => ({ competency: c.competency || c.name, score: c.score })),
    strengths: (scorecard.strengths || []).map((s) => typeof s === 'string' ? s : s.description || s.evidence || JSON.stringify(s)),
    gaps: (scorecard.gaps || []).map((s) => typeof s === 'string' ? s : s.description || s.evidence || JSON.stringify(s)),
    recommendations: [scorecard.explanation || scorecard.decisionSupport?.summary || 'Review evidence and use panel judgment.'], scorecard
  });
  return report;
}

async function getReport(id) {
  const interview = await getInterview(id);
  if (interview.status !== 'completed') { const error = new Error('Interview scorecard is not ready'); error.statusCode = 409; throw error; }
  return await Report.findOne({ interviewId: id });
}

async function recordIntegrity(id, events, status) {
  const interview = await getInterview(id);
  interview.integrityEvents = Array.isArray(events) ? events : [];
  interview.warnings = interview.integrityEvents.length;
  if (status === 'disqualified' && interview.status === 'in_progress') {
    interview.status = 'disqualified';
    interview.completedAt = new Date().toISOString();
  }
  await interview.save();
  return { status: interview.status, warnings: interview.warnings };
}

module.exports = { createInterview, startInterview, submitAnswer, getInterview, getReport, recordIntegrity };
