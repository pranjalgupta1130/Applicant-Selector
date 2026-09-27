const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';
const DEFAULT_TIMEOUT_MS = Number(process.env.AI_SERVICE_TIMEOUT_MS) || 5000;

/**
 * Helper to make HTTP POST request with timeout
 */
const postToAiService = async (endpoint, payload, timeoutMs = DEFAULT_TIMEOUT_MS) => {
  const url = `${AI_SERVICE_URL}${endpoint}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
      signal: controller.signal
    });

    clearTimeout(timer);

    if (!res.ok) {
      throw new Error(`AI service returned HTTP ${res.status}`);
    }

    return await res.json();
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
};

/**
 * Helper to make HTTP GET request with timeout
 */
const getFromAiService = async (endpoint, timeoutMs = DEFAULT_TIMEOUT_MS) => {
  const url = `${AI_SERVICE_URL}${endpoint}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      signal: controller.signal
    });

    clearTimeout(timer);

    if (!res.ok) {
      throw new Error(`AI service returned HTTP ${res.status}`);
    }

    return await res.json();
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
};

/**
 * Check health status of Python AI Service
 */
const checkHealth = async () => {
  try {
    const data = await getFromAiService('/health', 3000);
    return {
      status: 'ok',
      aiServiceUrl: AI_SERVICE_URL,
      details: data
    };
  } catch (err) {
    return {
      status: 'unavailable',
      aiServiceUrl: AI_SERVICE_URL,
      error: err.message
    };
  }
};

/**
 * Fallback questions by stage
 */
const STAGE_FALLBACK_QUESTIONS = {
  ice_breaker: 'Could you introduce yourself and describe your experience relevant to this role?',
  fundamentals: 'What are the key architecture and design principles you rely on in software development?',
  technical: 'How would you design a highly available REST API service handling concurrent user requests?',
  deep_dive: 'Can you detail a complex bug or performance bottleneck you resolved recently?',
  scenario: 'How do you handle production outages or high-priority incidents under tight deadlines?',
  closing: 'Do you have any questions for us regarding the technical environment or team workflow?'
};

/**
 * Generate Question via Python AI/RAG Service with Fallback
 * 
 * Frozen Question Contract:
 * {
 *   text: string,
 *   stage: string,
 *   competency: string,
 *   difficulty: number,
 *   expectedConcepts: string[],
 *   relevanceScore: number,
 *   rubric: object|null,
 *   sourceChunkIds: string[]
 * }
 */
const generateQuestion = async ({
  candidate,
  role,
  stage = 'fundamentals',
  competency = 'General Technical Competency',
  difficulty = 3,
  previousQuestions = [],
  targetCompetencies = []
} = {}) => {
  const payload = {
    candidate: candidate ? {
      name: candidate.name,
      experience: candidate.experience,
      education: candidate.education,
      skills: candidate.extractedSkills || candidate.skills || []
    } : null,
    role: role ? {
      title: role.title,
      description: role.description,
      requirements: role.requirements || []
    } : null,
    stage,
    competency,
    difficulty,
    previousQuestions: previousQuestions.map(q => q.text || q),
    targetCompetencies
  };

  try {
    const response = await postToAiService('/api/ai/generate-question', payload);
    const data = response.data || response;

    if (data && data.text && typeof data.text === 'string' && data.text.trim()) {
      return {
        text: data.text.trim(),
        stage: data.stage || stage,
        competency: data.competency || competency,
        difficulty: typeof data.difficulty === 'number' ? data.difficulty : difficulty,
        expectedConcepts: Array.isArray(data.expectedConcepts) ? data.expectedConcepts : ['core principles', 'practical application'],
        relevanceScore: typeof data.relevanceScore === 'number' ? data.relevanceScore : 0.85,
        rubric: data.rubric || null,
        sourceChunkIds: Array.isArray(data.sourceChunkIds) ? data.sourceChunkIds : []
      };
    }
  } catch (err) {
    console.warn(`[AI Service] Question generation call failed (${err.message}). Using fallback question.`);
  }

  // Fallback response matching Question schema
  const fallbackText = STAGE_FALLBACK_QUESTIONS[stage] || STAGE_FALLBACK_QUESTIONS.fundamentals;
  return {
    text: fallbackText,
    stage,
    competency,
    difficulty: Number(difficulty) || 3,
    expectedConcepts: ['core principles', 'problem solving', 'best practices'],
    relevanceScore: 0.8,
    rubric: {
      keyCriteria: ['Clarity', 'Technical Accuracy', 'Completeness'],
      passingScore: 6
    },
    sourceChunkIds: []
  };
};

/**
 * Evaluate Answer via Python AI/RAG Service with Fallback
 * 
 * Frozen Evaluation Contract:
 * {
 *   relevance: number (1-10),
 *   technicalCorrectness: number (1-10),
 *   completeness: number (1-10),
 *   reasoning: number (1-10),
 *   clarity: number (1-10),
 *   total: number (1-10),
 *   coveredConcepts: string[],
 *   missingConcepts: string[],
 *   feedback: string,
 *   confidence: string
 * }
 */
const evaluateAnswer = async ({
  questionText,
  answerText,
  expectedConcepts = [],
  stage = 'fundamentals',
  competency = 'General Technical Competency',
  rubric = null
} = {}) => {
  const payload = {
    questionText,
    answerText,
    expectedConcepts,
    stage,
    competency,
    rubric
  };

  try {
    const response = await postToAiService('/api/ai/evaluate-answer', payload);
    const data = response.data || response;

    if (data && typeof data.relevance === 'number') {
      const relevance = Math.min(10, Math.max(1, Number(data.relevance) || 7));
      const technicalCorrectness = Math.min(10, Math.max(1, Number(data.technicalCorrectness) || 7));
      const completeness = Math.min(10, Math.max(1, Number(data.completeness) || 7));
      const reasoning = Math.min(10, Math.max(1, Number(data.reasoning) || 7));
      const clarity = Math.min(10, Math.max(1, Number(data.clarity) || 7));

      const totalCalculated = Number(((relevance + technicalCorrectness + completeness + reasoning + clarity) / 5).toFixed(1));
      const total = typeof data.total === 'number' ? Math.min(10, Math.max(1, Number(data.total))) : totalCalculated;

      let confidenceNum = 0.85;
      if (typeof data.confidence === 'number') {
        confidenceNum = Math.min(1, Math.max(0, data.confidence > 1 ? data.confidence / 10 : data.confidence));
      } else if (typeof data.confidence === 'string') {
        const lower = data.confidence.toLowerCase();
        if (lower.includes('high')) confidenceNum = 0.9;
        else if (lower.includes('medium')) confidenceNum = 0.7;
        else if (lower.includes('low')) confidenceNum = 0.5;
      }

      return {
        relevance,
        technicalCorrectness,
        completeness,
        reasoning,
        clarity,
        total,
        coveredConcepts: Array.isArray(data.coveredConcepts) ? data.coveredConcepts : (expectedConcepts.length ? [expectedConcepts[0]] : []),
        missingConcepts: Array.isArray(data.missingConcepts) ? data.missingConcepts : (expectedConcepts.length > 1 ? expectedConcepts.slice(1) : []),
        feedback: data.feedback || 'Answer evaluated successfully.',
        confidence: confidenceNum
      };
    }
  } catch (err) {
    console.warn(`[AI Service] Answer evaluation call failed (${err.message}). Using fallback evaluation.`);
  }

  // Fallback response matching Evaluation schema with numeric confidence
  const covered = expectedConcepts.length > 0 ? [expectedConcepts[0]] : ['core concepts'];
  const missing = expectedConcepts.length > 1 ? expectedConcepts.slice(1) : [];

  return {
    relevance: 7,
    technicalCorrectness: 7,
    completeness: 6,
    reasoning: 7,
    clarity: 7,
    total: 6.8,
    coveredConcepts: covered,
    missingConcepts: missing,
    feedback: 'Fallback evaluation applied: Answer recorded and assessed with baseline performance metrics.',
    confidence: 0.7
  };
};

/**
 * Retrieve Context via Python RAG Service with Fallback
 */
const retrieveContext = async (query, topK = 3) => {
  try {
    const response = await postToAiService('/api/rag/retrieve', { query, topK });
    const data = response.data || response;
    return Array.isArray(data.chunks) ? data.chunks : (Array.isArray(data) ? data : []);
  } catch (err) {
    console.warn(`[AI Service] RAG retrieval call failed (${err.message}). Returning empty context.`);
    return [];
  }
};

module.exports = {
  checkHealth,
  generateQuestion,
  evaluateAnswer,
  retrieveContext,
  getAiServiceUrl: () => AI_SERVICE_URL
};
