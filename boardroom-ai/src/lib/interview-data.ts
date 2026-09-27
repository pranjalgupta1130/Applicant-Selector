/**
 * Mock data layer shaped to match the planned REST API so backend wiring is a
 * drop-in replacement later:
 *   POST /api/interviews/start
 *   GET  /api/interviews/:id/question
 *   POST /api/interviews/:id/answer
 *   GET  /api/interviews/:id/report
 */

export type InterviewStage =
  | "Ice-breaker"
  | "Fundamentals"
  | "Technical"
  | "Deep-dive"
  | "Scenario";

export type Role = {
  id: string;
  title: string;
  department: string;
  openings: number;
  summary: string;
};

export type Question = {
  id: string;
  roleId: string;
  stage: InterviewStage;
  difficulty: "Easy" | "Moderate" | "Hard";
  text: string;
  kind?: "derivation" | "reasoning" | undefined;
};

export type AnswerPayload = {
  questionId: string;
  mode: "draw" | "equation";
  canvasDataUrl?: string | undefined;
  latex?: string | undefined;
  secondsUsed: number;
  skipped: boolean;
};

export type CandidateProfile = {
  roleId: string;
  resumeName: string | null;
  yearsExperience: string;
  skills: string[];
};

export const ROLES: Role[] = [
  {
    id: "role-aero-sci-b",
    title: "Scientist 'B' — Aerodynamics",
    department: "Aeronautical Systems (ADE)",
    openings: 6,
    summary: "Compressible flow, flight loads and vehicle stability analysis.",
  },
  {
    id: "role-radar-sci-c",
    title: "Scientist 'C' — Radar Signal Processing",
    department: "Electronics & Radar (LRDE)",
    openings: 3,
    summary: "Detection theory, clutter modelling and adaptive beamforming.",
  },
  {
    id: "role-materials-sci-b",
    title: "Scientist 'B' — Composite Materials",
    department: "Advanced Materials (DMRL)",
    openings: 4,
    summary: "Fibre-matrix mechanics, failure criteria and thermal ageing.",
  },
  {
    id: "role-control-sci-c",
    title: "Scientist 'C' — Guidance & Control",
    department: "Missile Systems (RCI)",
    openings: 2,
    summary: "State estimation, nonlinear control and seeker integration.",
  },
];

export const QUESTION_BANK: Question[] = [
  {
    id: "q-1",
    roleId: "role-aero-sci-b",
    stage: "Fundamentals",
    difficulty: "Easy",
    text: "What is the difference between speed and velocity?",
    kind: "reasoning",
  },
  {
    id: "q-2",
    roleId: "role-radar-sci-c",
    stage: "Fundamentals",
    difficulty: "Easy",
    text: "What is radar used for? Give one simple example.",
    kind: "reasoning",
  },
  {
    id: "q-3",
    roleId: "role-materials-sci-b",
    stage: "Fundamentals",
    difficulty: "Easy",
    text: "Name one advantage of composite materials over ordinary metals.",
    kind: "reasoning",
  },
  {
    id: "q-4",
    roleId: "role-control-sci-c",
    stage: "Fundamentals",
    difficulty: "Easy",
    text: "Why do automatic control systems use feedback?",
    kind: "reasoning",
  },
];

export const DEFAULT_SETTINGS = {
  questionsPerInterview: 4,
  timerSeconds: 90,
  warningThresholdSeconds: 20,
  rubricWeights: {
    "Technical Correctness": 40,
    Completeness: 25,
    Communication: 15,
    "Problem Solving": 20,
  } as Record<string, number>,
};

/** Role-agnostic ice-breakers — always asked first. */
export const ICEBREAKERS: Question[] = [
  {
    id: "ib-1",
    roleId: "*",
    stage: "Ice-breaker",
    difficulty: "Easy",
    text: "Tell us briefly about yourself and why you want to work in research and development.",
    kind: "reasoning",
  },
  {
    id: "ib-2",
    roleId: "*",
    stage: "Ice-breaker",
    difficulty: "Easy",
    text: "Tell us about one simple project you enjoyed working on.",
    kind: "reasoning",
  },
];

/** Derivation questions get the chalkboard; theory/reasoning questions get a typing + voice space. */
export function questionKind(q: Question): "derivation" | "reasoning" {
  if (q.kind) return q.kind;
  return /deriv|obtain|relation|equation|from first principles/i.test(q.text)
    ? "derivation"
    : "reasoning";
}

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j]!, a[i]!];
  }
  return a;
}

/** Short theory questions — answered by typing or voice. */
export const THEORY_QUESTIONS: Question[] = [
  { id: "th-1", roleId: "*", stage: "Technical", difficulty: "Easy", kind: "reasoning", text: "What is the difference between accuracy and precision?" },
  { id: "th-2", roleId: "*", stage: "Technical", difficulty: "Easy", kind: "reasoning", text: "Why is testing important before an engineering product is used?" },
  { id: "th-3", roleId: "*", stage: "Technical", difficulty: "Easy", kind: "reasoning", text: "What is one benefit of working in a team?" },
];

/** Simple numericals — answered on the chalkboard / equation space. */
export const NUMERICAL_QUESTIONS: Question[] = [
  { id: "nu-1", roleId: "*", stage: "Fundamentals", difficulty: "Easy", kind: "derivation", text: "A 2 kg object moves at 3 m/s. Find its kinetic energy." },
  { id: "nu-2", roleId: "*", stage: "Fundamentals", difficulty: "Easy", kind: "derivation", text: "A car travels 60 km in 2 hours. Find its average speed." },
  { id: "nu-3", roleId: "*", stage: "Fundamentals", difficulty: "Easy", kind: "derivation", text: "A force of 10 N moves an object by 2 m. Find the work done." },
];

const pick = <T,>(arr: T[]): T => shuffle(arr)[0]!;

/** Exactly 4 questions: ice-breaker → role question (2 follow-ups) → theory → simple numerical. */
export function buildQuestionSet(roleId: string, _count = 4): Question[] {
  const forRole = QUESTION_BANK.filter((q) => q.roleId === roleId && q.stage !== "Ice-breaker");
  const core = pick(forRole.length ? forRole : QUESTION_BANK.filter((q) => q.stage !== "Ice-breaker"));
  return [pick(ICEBREAKERS), core, pick(THEORY_QUESTIONS), pick(NUMERICAL_QUESTIONS)];
}


/* ---------- Panel review mock report data (GET /api/interviews/:id/report) ---------- */

export type RubricScore = {
  label: "Relevance" | "Technical Correctness" | "Completeness" | "Reasoning" | "Clarity";
  score: number;
};

export type QuestionEvaluation = {
  questionId: string;
  stage: InterviewStage;
  question: string;
  submissionType: "Digital chalkboard" | "Typed equation" | "Not attempted";
  submissionPreview: string;
  score: number;
  note: string;
};

export type CandidateReport = {
  id: string;
  name: string;
  roleTitle: string;
  status: "In Progress" | "Completed" | "Caught cheating";
  overallScore: number | null;
  submittedAt: string;
  rubric: RubricScore[];
  coveredConcepts: string[];
  missingConcepts: string[];
  reasoningSummary: string;
  perQuestion: QuestionEvaluation[];
};

export const CANDIDATE_REPORTS: CandidateReport[] = [
  {
    id: "cand-1",
    name: "Ananya Raghavan",
    roleTitle: "Scientist 'B' — Aerodynamics",
    status: "Completed",
    overallScore: 84,
    submittedAt: "26 Sep 2026, 14:20",
    rubric: [
      { label: "Relevance", score: 88 },
      { label: "Technical Correctness", score: 86 },
      { label: "Completeness", score: 76 },
      { label: "Reasoning", score: 90 },
      { label: "Clarity", score: 80 },
    ],
    coveredConcepts: [
      "Conservation of momentum",
      "Isentropic assumptions stated before use",
      "Area–Mach coupling",
      "Shock-induced separation",
      "Dimensional consistency checks",
    ],
    missingConcepts: ["Boundary-layer displacement effect", "Sweep correction on critical Mach"],
    reasoningSummary:
      "The candidate reasons forward from governing equations rather than recalling end results. Each assumption was introduced at the point it became necessary, and when the derivation branched she chose the branch with a stated physical justification. Under time pressure she preserved structure over completeness — the final step of the oblique-shock question was left unresolved, but the path she had set up was correct. Depth of understanding is evident; breadth on viscous corrections is the gap a panel should probe further.",
    perQuestion: [
      {
        questionId: "q-2",
        stage: "Fundamentals",
        question: "Derive the one-dimensional isentropic area–Mach number relation.",
        submissionType: "Digital chalkboard",
        submissionPreview:
          "dA/A = (M² − 1) dV/V  →  continuity + Euler combined, isentropic stated at step 2",
        score: 90,
        note: "Complete derivation. Assumptions declared as used, not retro-fitted.",
      },
      {
        questionId: "q-3",
        stage: "Technical",
        question: "What governs the drag rise near Mach 0.82?",
        submissionType: "Typed equation",
        submissionPreview: "M_{cr} \\approx \\frac{1}{\\sqrt{1 + \\frac{\\gamma-1}{2}M^2}}",
        score: 82,
        note: "Correct mechanism identified; sweep correction not considered.",
      },
      {
        questionId: "q-4",
        stage: "Deep-dive",
        question: "Obtain the oblique shock θ–β–M relation.",
        submissionType: "Digital chalkboard",
        submissionPreview: "tan θ = 2 cot β · (M²sin²β − 1) / (M²(γ + cos 2β) + 2) — final algebra incomplete",
        score: 74,
        note: "Setup correct throughout. Time expired before the detachment discussion.",
      },
    ],
  },
  {
    id: "cand-2",
    name: "Vikram Deshpande",
    roleTitle: "Scientist 'C' — Radar Signal Processing",
    status: "Completed",
    overallScore: 71,
    submittedAt: "26 Sep 2026, 11:05",
    rubric: [
      { label: "Relevance", score: 74 },
      { label: "Technical Correctness", score: 70 },
      { label: "Completeness", score: 68 },
      { label: "Reasoning", score: 72 },
      { label: "Clarity", score: 76 },
    ],
    coveredConcepts: ["Range equation scaling", "Noise figure reasoning", "Threshold detection"],
    missingConcepts: ["CFAR loss", "Clutter statistics beyond Gaussian", "Coherent integration gain"],
    reasoningSummary:
      "Derivations are reproduced accurately but largely from memory; when the panel varied the premise, the candidate returned to the memorised form rather than re-deriving. Communication is clear and well-ordered. Recommend a second round focused on non-Gaussian clutter to establish whether the understanding is structural or recalled.",
    perQuestion: [
      {
        questionId: "q-6",
        stage: "Fundamentals",
        question: "Derive the radar range equation.",
        submissionType: "Digital chalkboard",
        submissionPreview: "P_r = P_t G² λ² σ / (4π)³ R⁴ — scaling discussed term by term",
        score: 80,
        note: "Accurate. Scaling argument sound.",
      },
      {
        questionId: "q-7",
        stage: "Deep-dive",
        question: "Probability of false alarm for a square-law detector.",
        submissionType: "Not attempted",
        submissionPreview: "Time expired with an empty board.",
        score: 0,
        note: "Auto-skipped at 0 seconds. Not revisitable per interview format.",
      },
    ],
  },
  {
    id: "cand-3",
    name: "Priya Nandakumar",
    roleTitle: "Scientist 'B' — Composite Materials",
    status: "In Progress",
    overallScore: null,
    submittedAt: "—",
    rubric: [],
    coveredConcepts: [],
    missingConcepts: [],
    reasoningSummary: "Session active. Evaluation becomes available once the interview closes.",
    perQuestion: [],
  },
  {
    id: "cand-4",
    name: "Rohit Sathe",
    roleTitle: "Scientist 'C' — Guidance & Control",
    status: "Completed",
    overallScore: 63,
    submittedAt: "25 Sep 2026, 16:42",
    rubric: [
      { label: "Relevance", score: 66 },
      { label: "Technical Correctness", score: 58 },
      { label: "Completeness", score: 60 },
      { label: "Reasoning", score: 64 },
      { label: "Clarity", score: 70 },
    ],
    coveredConcepts: ["State-space formulation", "Observability intuition"],
    missingConcepts: ["Covariance propagation", "Gain limit as noise vanishes", "Bias handling"],
    reasoningSummary:
      "Comfortable with structure and notation, less so with the probabilistic core. The derivation stalled at covariance propagation, which suggests the estimator is understood as a recipe rather than as a consequence of minimising error variance.",
    perQuestion: [
      {
        questionId: "q-9",
        stage: "Deep-dive",
        question: "Derive the Kalman gain for a scalar system.",
        submissionType: "Typed equation",
        submissionPreview: "K = \\frac{P^-}{P^- + R}",
        score: 63,
        note: "Correct final form, derivation not established.",
      },
    ],
  },
];
