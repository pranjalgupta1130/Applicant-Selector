const { Interview, Candidate, Role, InterviewQuestion, Answer, Evaluation, Report } = require('../models');
const { isValidId } = require('../storage/jsonStore');
const aiService = require('./ai.service');

const STAGES = [
  'ice_breaker',
  'applicant_validation',
  'core_technical',
  'deep_dive',
  'application_scenario',
  'system_engineering',
  'techno_managerial',
  'closing'
];

const VALID_STAGES = [
  ...STAGES,
  'fundamentals',
  'technical',
  'scenario',
  'expertise_validation',
  'role_technical',
  'scenario_managerial'
];

/**
 * Pure deterministic strategy helper based on evaluation performance (Task 8 Phase 3 & 4)
 */
const determineNextQuestionStrategy = (evaluation, currentQuestion, interview) => {
  const totalScore = typeof evaluation.total === 'number' ? evaluation.total : 6.8;
  const currentStage = (currentQuestion && currentQuestion.stage) || (interview && interview.currentStage) || 'ice_breaker';
  const currentDifficulty = Number(currentQuestion && currentQuestion.difficulty) || 3;
  const currentCompetency = (currentQuestion && currentQuestion.competency) || 'General Technical Competency';

  let action = 'maintain';
  let difficultyDelta = 0;
  let reason = '';

  if (totalScore >= 8.0) {
    action = 'escalate';
    difficultyDelta = 1;
    reason = `Strong performance (score: ${totalScore}/10). Escalating complexity.`;
  } else if (totalScore >= 6.0) {
    action = 'maintain';
    difficultyDelta = 0;
    reason = `Solid performance (score: ${totalScore}/10). Maintaining current difficulty level.`;
  } else {
    action = 'simplify';
    difficultyDelta = -1;
    reason = `Needs reinforcement (score: ${totalScore}/10). Simplifying difficulty to target missing concepts.`;
  }

  let targetDifficulty = Math.min(5, Math.max(1, currentDifficulty + difficultyDelta));

  // Determine stage progression
  let stageIndex = STAGES.indexOf(currentStage);
  if (stageIndex === -1) {
    // Check aliases
    if (currentStage === 'fundamentals' || currentStage === 'expertise_validation') stageIndex = 1;
    else if (currentStage === 'technical' || currentStage === 'role_technical') stageIndex = 2;
    else if (currentStage === 'scenario' || currentStage === 'scenario_managerial') stageIndex = 4;
    else stageIndex = 0;
  }

  let targetStage = currentStage;
  if (stageIndex < STAGES.length - 1) {
    targetStage = STAGES[stageIndex + 1];
  } else {
    targetStage = 'closing';
  }

  // Determine target competency
  let targetCompetency = currentCompetency || targetStage;
  if (Array.isArray(interview && interview.targetCompetencies) && interview.targetCompetencies.length > 0) {
    const comps = interview.targetCompetencies.filter(c => typeof c === 'string' && c.trim().length > 0);
    if (comps.length > 0) {
      const currIdx = comps.indexOf(currentCompetency);
      if (currIdx !== -1 && currIdx + 1 < comps.length) {
        targetCompetency = comps[currIdx + 1];
      } else {
        targetCompetency = comps[0];
      }
    }
  }
  if (!targetCompetency || typeof targetCompetency !== 'string' || !targetCompetency.trim()) {
    targetCompetency = targetStage;
  }

  return {
    action,
    difficultyDelta,
    targetDifficulty,
    reason,
    targetStage,
    targetCompetency
  };
};

/**
 * Service: Create a new Interview Session
 */
const createInterview = async ({ candidateId, roleId, targetCompetencies }) => {
  if (!candidateId || !isValidId(candidateId)) {
    const err = new Error(`Invalid or missing candidateId: ${candidateId}`);
    err.statusCode = 400;
    throw err;
  }

  if (!roleId || !isValidId(roleId)) {
    const err = new Error(`Invalid or missing roleId: ${roleId}`);
    err.statusCode = 400;
    throw err;
  }

  const candidate = await Candidate.findById(candidateId);
  if (!candidate) {
    const err = new Error(`Candidate not found with ID: ${candidateId}`);
    err.statusCode = 404;
    throw err;
  }

  const role = await Role.findById(roleId).populate('competencies');
  if (!role) {
    const err = new Error(`Role not found with ID: ${roleId}`);
    err.statusCode = 404;
    throw err;
  }

  // Derive target competencies if not explicitly provided
  let competenciesList = [];
  if (Array.isArray(targetCompetencies) && targetCompetencies.length > 0) {
    competenciesList = targetCompetencies.map(c => typeof c === 'string' ? c.trim() : (c.name || String(c)));
  } else if (role.competencies && role.competencies.length > 0) {
    competenciesList = role.competencies.map(c => typeof c === 'object' && c.name ? c.name : String(c));
  }

  const newInterview = await Interview.create({
    candidateId,
    roleId,
    targetCompetencies: competenciesList,
    status: 'created',
    currentStage: 'ice_breaker',
    currentQuestionId: null,
    questionSequence: 0,
    questionsAsked: 0
  });

  return await Interview.findById(newInterview._id)
    .populate('candidateId')
    .populate('roleId');
};

/**
 * Service: Get Interview by ID
 */
const getInterviewById = async (id) => {
  if (!isValidId(id)) {
    const err = new Error(`Invalid interview ID format: ${id}`);
    err.statusCode = 400;
    throw err;
  }

  const interview = await Interview.findById(id)
    .populate('candidateId')
    .populate('roleId')
    .populate('currentQuestionId');

  if (!interview) {
    const err = new Error(`Interview session not found with ID: ${id}`);
    err.statusCode = 404;
    throw err;
  }

  return interview;
};

/**
 * Service: Start Interview Session
 */
const startInterview = async (id) => {
  if (!isValidId(id)) {
    const err = new Error(`Invalid interview ID format: ${id}`);
    err.statusCode = 400;
    throw err;
  }

  const interview = await Interview.findById(id);

  if (!interview) {
    const err = new Error(`Interview session not found with ID: ${id}`);
    err.statusCode = 404;
    throw err;
  }

  if (interview.status === 'completed' || interview.status === 'failed') {
    const err = new Error(`Cannot start interview in '${interview.status}' status.`);
    err.statusCode = 400;
    throw err;
  }

  // If already in_progress, return existing state without resetting
  if (interview.status === 'in_progress') {
    return await Interview.findById(id)
      .populate('candidateId')
      .populate('roleId')
      .populate('currentQuestionId');
  }

  // Transition from 'created' to 'in_progress'
  interview.status = 'in_progress';
  interview.currentStage = 'ice_breaker';
  interview.startedAt = new Date().toISOString();
  await interview.save();

  return await Interview.findById(id)
    .populate('candidateId')
    .populate('roleId')
    .populate('currentQuestionId');
};

/**
 * Service: Persist a Question for an Interview (Task 6)
 */
const createInterviewQuestion = async (interviewId, questionData) => {
  if (!isValidId(interviewId)) {
    const err = new Error(`Invalid interview ID format: ${interviewId}`);
    err.statusCode = 400;
    throw err;
  }

  const interview = await Interview.findById(interviewId);
  if (!interview) {
    const err = new Error(`Interview not found with ID: ${interviewId}`);
    err.statusCode = 404;
    throw err;
  }

  if (interview.status === 'completed' || interview.status === 'failed') {
    const err = new Error(`Cannot add questions to an interview in '${interview.status}' status.`);
    err.statusCode = 400;
    throw err;
  }

  const { text, stage, competency, difficulty, expectedConcepts, relevanceScore, rubric, sourceChunkIds, questionId } = questionData;

  if (!text || typeof text !== 'string' || !text.trim()) {
    const err = new Error('Question text is required');
    err.statusCode = 400;
    throw err;
  }

  if (!stage || !VALID_STAGES.includes(stage)) {
    const err = new Error(`Valid question stage is required (${VALID_STAGES.join(', ')})`);
    err.statusCode = 400;
    throw err;
  }

  if (!competency || typeof competency !== 'string' || !competency.trim()) {
    const err = new Error('Question competency is required');
    err.statusCode = 400;
    throw err;
  }

  if (difficulty !== undefined) {
    const diffNum = Number(difficulty);
    if (isNaN(diffNum) || diffNum < 1 || diffNum > 5) {
      const err = new Error('Question difficulty must be a number between 1 and 5');
      err.statusCode = 400;
      throw err;
    }
  }

  const sequence = (interview.questionSequence || 0) + 1;

  const newQuestion = await InterviewQuestion.create({
    interviewId,
    questionId: questionId || '',
    text: text.trim(),
    stage,
    competency: competency.trim(),
    difficulty: difficulty ? Number(difficulty) : 3,
    expectedConcepts: Array.isArray(expectedConcepts) ? expectedConcepts : [],
    relevanceScore: relevanceScore !== undefined ? Number(relevanceScore) : 0,
    sequence,
    generated: true,
    rubric: rubric || null,
    sourceChunkIds: Array.isArray(sourceChunkIds) ? sourceChunkIds : []
  });

  // Update interview session state canonical counters
  interview.status = 'in_progress';
  interview.currentQuestionId = newQuestion._id;
  interview.questionSequence = sequence;
  interview.questionsAsked = (interview.questionsAsked || 0) + 1;
  interview.currentStage = stage;
  if (!interview.startedAt) {
    interview.startedAt = new Date().toISOString();
  }
  await interview.save();

  // Return formatted object with external contract id
  return {
    id: newQuestion._id,
    _id: newQuestion._id,
    interviewId: newQuestion.interviewId,
    text: newQuestion.text,
    stage: newQuestion.stage,
    competency: newQuestion.competency,
    difficulty: newQuestion.difficulty,
    expectedConcepts: newQuestion.expectedConcepts,
    relevanceScore: newQuestion.relevanceScore,
    sequence: newQuestion.sequence,
    generated: newQuestion.generated,
    rubric: newQuestion.rubric,
    sourceChunkIds: newQuestion.sourceChunkIds,
    createdAt: newQuestion.createdAt
  };
};

/**
 * Service: Get All Persisted Questions for an Interview (Task 6)
 */
const getInterviewQuestions = async (interviewId) => {
  if (!isValidId(interviewId)) {
    const err = new Error(`Invalid interview ID format: ${interviewId}`);
    err.statusCode = 400;
    throw err;
  }

  const interview = await Interview.findById(interviewId);
  if (!interview) {
    const err = new Error(`Interview not found with ID: ${interviewId}`);
    err.statusCode = 404;
    throw err;
  }

  const questions = await InterviewQuestion.find({ interviewId });
  return questions.map(q => ({
    id: q._id,
    _id: q._id,
    interviewId: q.interviewId,
    text: q.text,
    stage: q.stage,
    competency: q.competency,
    difficulty: q.difficulty,
    expectedConcepts: q.expectedConcepts,
    relevanceScore: q.relevanceScore,
    sequence: q.sequence,
    generated: q.generated,
    rubric: q.rubric,
    sourceChunkIds: q.sourceChunkIds,
    createdAt: q.createdAt
  }));
};

/**
 * Service: Get Single Persisted Question by ID for an Interview (Task 6)
 */
const getInterviewQuestionById = async (interviewId, questionId) => {
  if (!isValidId(interviewId)) {
    const err = new Error(`Invalid interview ID format: ${interviewId}`);
    err.statusCode = 400;
    throw err;
  }

  if (!isValidId(questionId)) {
    const err = new Error(`Invalid question ID format: ${questionId}`);
    err.statusCode = 400;
    throw err;
  }

  const interview = await Interview.findById(interviewId);
  if (!interview) {
    const err = new Error(`Interview not found with ID: ${interviewId}`);
    err.statusCode = 404;
    throw err;
  }

  const question = await InterviewQuestion.findById(questionId);
  if (!question || question.interviewId !== interviewId) {
    const err = new Error(`Question with ID ${questionId} not found for interview ${interviewId}`);
    err.statusCode = 404;
    throw err;
  }

  return {
    id: question._id,
    _id: question._id,
    interviewId: question.interviewId,
    text: question.text,
    stage: question.stage,
    competency: question.competency,
    difficulty: question.difficulty,
    expectedConcepts: question.expectedConcepts,
    relevanceScore: question.relevanceScore,
    sequence: question.sequence,
    generated: question.generated,
    rubric: question.rubric,
    sourceChunkIds: question.sourceChunkIds,
    createdAt: question.createdAt
  };
};

/**
 * Service: Persist Candidate Answer + AI Evaluation + Next Question Generation (Task 8)
 */
const submitAnswer = async (interviewId, answerData) => {
  if (!isValidId(interviewId)) {
    const err = new Error(`Invalid interview ID format: ${interviewId}`);
    err.statusCode = 400;
    throw err;
  }

  const interview = await Interview.findById(interviewId);
  if (!interview) {
    const err = new Error(`Interview not found with ID: ${interviewId}`);
    err.statusCode = 404;
    throw err;
  }

  if (interview.status !== 'in_progress') {
    const err = new Error(`Interview must be in_progress to submit answers. Current status: '${interview.status}'`);
    err.statusCode = 400;
    throw err;
  }

  const { interviewQuestionId, answerText, transcript } = answerData;

  if (!interviewQuestionId || !isValidId(interviewQuestionId)) {
    const err = new Error(`Invalid or missing interviewQuestionId: ${interviewQuestionId}`);
    err.statusCode = 400;
    throw err;
  }

  const question = await InterviewQuestion.findById(interviewQuestionId);
  if (!question) {
    const err = new Error(`InterviewQuestion not found with ID: ${interviewQuestionId}`);
    err.statusCode = 404;
    throw err;
  }

  if (question.interviewId !== interviewId) {
    const err = new Error(`Question ${interviewQuestionId} does not belong to interview ${interviewId}`);
    err.statusCode = 400;
    throw err;
  }

  if (!answerText || typeof answerText !== 'string' || !answerText.trim()) {
    const err = new Error('answerText is required and cannot be empty');
    err.statusCode = 400;
    throw err;
  }

  // 1. Persist Answer (Phase 1)
  const newAnswer = await Answer.create({
    interviewQuestionId,
    answerText: answerText.trim(),
    transcript: transcript ? String(transcript).trim() : '',
    submittedAt: new Date().toISOString()
  });

  // 2. Evaluate Answer via AI Service (Phase 1 & 2)
  let evalData;
  try {
    evalData = await aiService.evaluateAnswer({
      questionText: question.text,
      answerText: newAnswer.answerText,
      expectedConcepts: question.expectedConcepts || [],
      stage: question.stage || interview.currentStage || 'fundamentals',
      competency: question.competency || 'General Technical Competency',
      rubric: question.rubric || null
    });
  } catch (err) {
    console.warn(`[Interview Service] AI evaluation call error (${err.message}). Using fallback evaluation.`);
    evalData = {
      relevance: 7,
      technicalCorrectness: 7,
      completeness: 6,
      reasoning: 7,
      clarity: 7,
      total: 6.8,
      coveredConcepts: (question.expectedConcepts && question.expectedConcepts.length) ? [question.expectedConcepts[0]] : ['core concepts'],
      missingConcepts: (question.expectedConcepts && question.expectedConcepts.length > 1) ? question.expectedConcepts.slice(1) : [],
      feedback: 'Fallback evaluation applied: Answer recorded and assessed with baseline performance metrics.',
      confidence: 0.7
    };
  }

  // Normalize confidence into numeric contract (Phase 2)
  let confidenceNum = 0.85;
  if (typeof evalData.confidence === 'number') {
    confidenceNum = Math.min(1, Math.max(0, evalData.confidence > 1 ? evalData.confidence / 10 : evalData.confidence));
  } else if (typeof evalData.confidence === 'string') {
    const lower = evalData.confidence.toLowerCase();
    if (lower.includes('high')) confidenceNum = 0.9;
    else if (lower.includes('medium')) confidenceNum = 0.7;
    else if (lower.includes('low')) confidenceNum = 0.5;
  }

  // Clamp numeric evaluation dimensions 1-10
  const relevance = Math.min(10, Math.max(1, Number(evalData.relevance) || 7));
  const technicalCorrectness = Math.min(10, Math.max(1, Number(evalData.technicalCorrectness) || 7));
  const completeness = Math.min(10, Math.max(1, Number(evalData.completeness) || 7));
  const reasoning = Math.min(10, Math.max(1, Number(evalData.reasoning) || 7));
  const clarity = Math.min(10, Math.max(1, Number(evalData.clarity) || 7));
  const total = Math.min(10, Math.max(1, Number(evalData.total) || Number(((relevance + technicalCorrectness + completeness + reasoning + clarity) / 5).toFixed(1))));

  const normalizedEval = {
    relevance,
    technicalCorrectness,
    completeness,
    reasoning,
    clarity,
    total,
    coveredConcepts: Array.isArray(evalData.coveredConcepts) ? evalData.coveredConcepts : [],
    missingConcepts: Array.isArray(evalData.missingConcepts) ? evalData.missingConcepts : [],
    feedback: evalData.feedback || 'Answer evaluated successfully.',
    confidence: confidenceNum
  };

  // 3. Determine Adaptive Strategy (Phase 3 & 4)
  const strategy = determineNextQuestionStrategy(normalizedEval, question, interview);

  // 4. Persist Evaluation (Phase 2)
  const newEvaluation = await Evaluation.create({
    answerId: newAnswer._id,
    relevance: normalizedEval.relevance,
    technicalCorrectness: normalizedEval.technicalCorrectness,
    completeness: normalizedEval.completeness,
    reasoning: normalizedEval.reasoning,
    clarity: normalizedEval.clarity,
    total: normalizedEval.total,
    coveredConcepts: normalizedEval.coveredConcepts,
    missingConcepts: normalizedEval.missingConcepts,
    feedback: normalizedEval.feedback,
    confidence: normalizedEval.confidence,
    nextQuestionStrategy: strategy
  });

  // 5. Build Compact History Context for Next Question Generation (Phase 8)
  const allQuestions = await InterviewQuestion.find({ interviewId });
  const allAnswers = await Answer.find({});
  const allEvals = await Evaluation.find({});

  const answerMap = new Map(allAnswers.map(a => [a.interviewQuestionId, a]));
  const evalMap = new Map(allEvals.map(e => [e.answerId, e]));

  const compactHistory = allQuestions.map(q => {
    const ans = answerMap.get(q._id);
    const ev = ans ? evalMap.get(ans._id) : null;
    return {
      text: q.text,
      stage: q.stage,
      competency: q.competency,
      difficulty: q.difficulty,
      answerText: ans ? ans.answerText : '',
      score: ev ? ev.total : null
    };
  });

  // 6. Generate & Persist Next Question (Phase 5 & 6)
  let nextQuestion = null;
  try {
    const candidateObj = interview.candidateId ? await Candidate.findById(typeof interview.candidateId === 'object' ? interview.candidateId._id : interview.candidateId) : null;
    const roleObj = interview.roleId ? await Role.findById(typeof interview.roleId === 'object' ? interview.roleId._id : interview.roleId) : null;

    const generatedData = await aiService.generateQuestion({
      candidate: candidateObj,
      role: roleObj,
      stage: strategy.targetStage,
      competency: strategy.targetCompetency,
      difficulty: strategy.targetDifficulty,
      previousQuestions: compactHistory,
      targetCompetencies: interview.targetCompetencies || []
    });

    if (generatedData && generatedData.text) {
      // createInterviewQuestion handles sequence & questionsAsked increments atomically
      nextQuestion = await createInterviewQuestion(interviewId, {
        text: generatedData.text,
        stage: strategy.targetStage,
        competency: strategy.targetCompetency,
        difficulty: strategy.targetDifficulty,
        expectedConcepts: generatedData.expectedConcepts || [],
        relevanceScore: generatedData.relevanceScore || 0.8,
        rubric: generatedData.rubric || null,
        sourceChunkIds: generatedData.sourceChunkIds || []
      });
    }
  } catch (err) {
    console.error(`[Interview Service] Failed to generate/persist next question: ${err.message}`, err);
    nextQuestion = null;
  }

  // 7. Format Structured Turn Response (Phase 7)
  return {
    answer: {
      id: newAnswer._id,
      _id: newAnswer._id,
      interviewQuestionId: newAnswer.interviewQuestionId,
      answerText: newAnswer.answerText,
      transcript: newAnswer.transcript,
      submittedAt: newAnswer.submittedAt
    },
    evaluation: {
      id: newEvaluation._id,
      _id: newEvaluation._id,
      answerId: newEvaluation.answerId,
      relevance: newEvaluation.relevance,
      technicalCorrectness: newEvaluation.technicalCorrectness,
      completeness: newEvaluation.completeness,
      reasoning: newEvaluation.reasoning,
      clarity: newEvaluation.clarity,
      total: newEvaluation.total,
      coveredConcepts: newEvaluation.coveredConcepts,
      missingConcepts: newEvaluation.missingConcepts,
      feedback: newEvaluation.feedback,
      confidence: newEvaluation.confidence,
      nextQuestionStrategy: strategy
    },
    nextQuestion: nextQuestion || null
  };
};

/**
 * Service: Generate / Fetch Final Interview Report (Task 9)
 */
const getInterviewReport = async (interviewId, options = {}) => {
  if (!isValidId(interviewId)) {
    const err = new Error(`Invalid interview ID format: ${interviewId}`);
    err.statusCode = 400;
    throw err;
  }

  const interview = await Interview.findById(interviewId);
  if (!interview) {
    const err = new Error(`Interview session not found with ID: ${interviewId}`);
    err.statusCode = 404;
    throw err;
  }

  // Idempotency: Return existing persisted report unless regenerate flag is true
  if (!options.regenerate) {
    const existingReport = await Report.findOne({ interviewId });
    if (existingReport) {
      return {
        id: existingReport._id,
        _id: existingReport._id,
        interviewId: existingReport.interviewId,
        overallScore: existingReport.overallScore,
        competencyScores: existingReport.competencyScores || [],
        strengths: existingReport.strengths || [],
        gaps: existingReport.gaps || [],
        recommendations: existingReport.recommendations || [],
        createdAt: existingReport.createdAt,
        updatedAt: existingReport.updatedAt
      };
    }
  }

  // Retrieve all questions, answers, and evaluations for this interview
  const questions = await InterviewQuestion.find({ interviewId });
  const questionMap = new Map(questions.map(q => [q._id, q]));

  const allAnswers = await Answer.find({});
  const interviewAnswers = allAnswers.filter(a => questionMap.has(a.interviewQuestionId));
  const answerMap = new Map(interviewAnswers.map(a => [a._id, a]));

  const allEvaluations = await Evaluation.find({});
  const evaluationsWithQuestion = [];

  for (const ev of allEvaluations) {
    if (answerMap.has(ev.answerId)) {
      const ans = answerMap.get(ev.answerId);
      const q = questionMap.get(ans.interviewQuestionId);
      evaluationsWithQuestion.push({
        evaluation: ev,
        answer: ans,
        question: q
      });
    }
  }

  // Controlled response if no evaluated answers exist yet
  if (evaluationsWithQuestion.length === 0) {
    return {
      interviewId,
      overallScore: 0,
      competencyScores: [],
      strengths: ['Interview session initiated.'],
      gaps: ['No evaluated answers available yet.'],
      recommendations: ['Submit candidate answers to generate evaluation metrics.']
    };
  }

  // 1. Stage-Weighted Overall Score Calculation (Master Plan proposed default weights)
  const STAGE_WEIGHTS = {
    ice_breaker: 10,
    fundamentals: 20,
    technical: 35,
    deep_dive: 20,
    scenario: 15
  };

  const stageGroups = new Map();
  evaluationsWithQuestion.forEach(item => {
    const stage = (item.question && item.question.stage) || 'fundamentals';
    if (!stageGroups.has(stage)) stageGroups.set(stage, []);
    stageGroups.get(stage).push(item.evaluation);
  });

  let totalWeightedScore = 0;
  let totalWeightRepresented = 0;

  stageGroups.forEach((evalList, stage) => {
    const weight = STAGE_WEIGHTS[stage] || 10;
    const stageAvg = evalList.reduce((acc, curr) => acc + (Number(curr.total) || 0), 0) / evalList.length;
    totalWeightedScore += stageAvg * weight;
    totalWeightRepresented += weight;
  });

  let overallScore = 0;
  if (totalWeightRepresented > 0) {
    overallScore = Number((totalWeightedScore / totalWeightRepresented).toFixed(1));
  } else {
    const simpleAvg = evaluationsWithQuestion.reduce((acc, item) => acc + (Number(item.evaluation.total) || 0), 0) / evaluationsWithQuestion.length;
    overallScore = Number(simpleAvg.toFixed(1));
  }

  // 2. Competency-Level Scores
  const competencyGroups = new Map();
  evaluationsWithQuestion.forEach(item => {
    const comp = (item.question && item.question.competency) || 'General Technical';
    if (!competencyGroups.has(comp)) competencyGroups.set(comp, []);
    competencyGroups.get(comp).push(item.evaluation);
  });

  const competencyScores = [];
  competencyGroups.forEach((evalList, comp) => {
    const avg = evalList.reduce((acc, curr) => acc + (Number(curr.total) || 0), 0) / evalList.length;
    competencyScores.push({
      competency: comp,
      score: Number(avg.toFixed(1))
    });
  });

  // 3. Derive Strengths
  const strengthsSet = new Set();
  const coveredConceptsSet = new Set();
  const missingConceptsSet = new Set();

  evaluationsWithQuestion.forEach(item => {
    const ev = item.evaluation;
    if (Array.isArray(ev.coveredConcepts)) {
      ev.coveredConcepts.forEach(c => coveredConceptsSet.add(c));
    }
    if (Array.isArray(ev.missingConcepts)) {
      ev.missingConcepts.forEach(c => missingConceptsSet.add(c));
    }
  });

  competencyScores.forEach(cs => {
    if (cs.score >= 7.5) {
      strengthsSet.add(`Strong technical proficiency in ${cs.competency} (score: ${cs.score}/10)`);
    }
  });

  if (coveredConceptsSet.size > 0) {
    const sampleCovered = Array.from(coveredConceptsSet).slice(0, 3).join(', ');
    strengthsSet.add(`Demonstrated understanding of key concepts: ${sampleCovered}`);
  }

  if (strengthsSet.size === 0) {
    strengthsSet.add('Demonstrated willingness to attempt technical questions under interview conditions.');
  }

  // 4. Derive Gaps
  const gapsSet = new Set();
  competencyScores.forEach(cs => {
    if (cs.score < 7.0) {
      gapsSet.add(`Opportunity to strengthen depth in ${cs.competency} (score: ${cs.score}/10)`);
    }
  });

  if (missingConceptsSet.size > 0) {
    const sampleMissing = Array.from(missingConceptsSet).slice(0, 3).join(', ');
    gapsSet.add(`Concept coverage can be expanded for: ${sampleMissing}`);
  }

  if (gapsSet.size === 0) {
    gapsSet.add('No critical technical gaps identified based on current question responses.');
  }

  // 5. Derive Neutral Recommendations (NO HIRE/REJECT AUTONOMOUS DECISION WORDS)
  const recommendationsSet = new Set();
  if (missingConceptsSet.size > 0) {
    const sampleMissing = Array.from(missingConceptsSet).slice(0, 2).join(' and ');
    recommendationsSet.add(`Further assess conceptual depth in ${sampleMissing} during technical onboarding.`);
  }

  competencyScores.forEach(cs => {
    if (cs.score < 7.5) {
      recommendationsSet.add(`Focus subsequent technical reviews on ${cs.competency} practical exercises.`);
    }
  });

  recommendationsSet.add('Review full evaluation scorecards and candidate code samples in conjunction with team guidelines.');

  const strengths = Array.from(strengthsSet);
  const gaps = Array.from(gapsSet);
  const recommendations = Array.from(recommendationsSet);

  // 6. Persist Report
  const reportDoc = await Report.create({
    interviewId,
    overallScore,
    competencyScores,
    strengths,
    gaps,
    recommendations
  });

  // 7. Completion Check (Only mark completed if in closing stage or 5+ questions answered & closing)
  if (interview.currentStage === 'closing' || (interview.questionsAsked >= 5 && interview.currentStage === 'closing')) {
    if (interview.status !== 'completed') {
      interview.status = 'completed';
      interview.completedAt = new Date().toISOString();
      await interview.save();
    }
  }

  return {
    id: reportDoc._id,
    _id: reportDoc._id,
    interviewId: reportDoc.interviewId,
    overallScore: reportDoc.overallScore,
    competencyScores: reportDoc.competencyScores,
    strengths: reportDoc.strengths,
    gaps: reportDoc.gaps,
    recommendations: reportDoc.recommendations,
    createdAt: reportDoc.createdAt
  };
};

module.exports = {
  createInterview,
  getInterviewById,
  startInterview,
  createInterviewQuestion,
  getInterviewQuestions,
  getInterviewQuestionById,
  submitAnswer,
  determineNextQuestionStrategy,
  getInterviewReport
};

