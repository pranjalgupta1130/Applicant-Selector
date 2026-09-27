"""
Core data schemas for the BoardRoom AI RAG & Question Generation subsystem.
Conforms strictly to Hackathon Master Plan Section 9, 11.2, and 13.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# Candidate and Interview Context Models
# ---------------------------------------------------------

class CandidateProfile(BaseModel):
    id: Optional[str] = "cand_default"
    name: Optional[str] = "Anonymous Candidate"
    skills: List[str] = Field(default_factory=list, description="Extracted candidate skills (e.g. Python, SQL, REST)")
    experience_years: Optional[float] = Field(default=2.0, description="Years of relevant experience")
    education: Optional[str] = "B.Tech in Computer Engineering"
    notes: Optional[str] = None
    # DRDO / RAC Candidate Profile Extensions
    discipline: Optional[str] = Field(default="Computer Science & Engineering", description="Academic/Professional discipline")
    specialization: Optional[str] = Field(default=None, description="Detailed domain specialization")
    claimed_expertise: List[str] = Field(default_factory=list, description="Specific claims declared in CV/application")
    projects: List[str] = Field(default_factory=list, description="Candidate project titles or briefs")
    domain: Optional[str] = Field(default=None, description="Resolved scientific/engineering domain")
    self_declared_competencies: Dict[str, str] = Field(default_factory=dict, description="Candidate self-declared rating per competency")


class TargetRole(BaseModel):
    id: str = "backend_engineer"
    title: str = "Backend / Full-Stack Software Engineer"
    description: Optional[str] = "Designs, builds, and maintains server-side applications, APIs, and databases."
    required_skills: List[str] = Field(default_factory=lambda: ["Python", "SQL", "REST APIs", "System Design", "Git"])
    min_experience_years: Optional[float] = 1.0
    # DRDO Advertised Post Extensions
    domain: Optional[str] = Field(default=None, description="DRDO domain key, e.g. electronics_radar")
    discipline: Optional[str] = Field(default=None, description="Discipline, e.g. Electronics & Communication Engineering")
    advertised_post_id: Optional[str] = Field(default=None, description="Official post requisition ID")
    technical_requirements: List[str] = Field(default_factory=list, description="Essential advertised technical criteria")
    managerial_requirements: List[str] = Field(default_factory=list, description="Advertised techno-managerial / leadership criteria")


# ---------------------------------------------------------
# RAG Knowledge Chunk Models
# ---------------------------------------------------------

class RubricCriteria(BaseModel):
    poor: str = Field(..., description="Characteristics of an unsatisfactory answer (score 0-40)")
    acceptable: str = Field(..., description="Characteristics of an adequate answer (score 41-75)")
    excellent: str = Field(..., description="Characteristics of an outstanding answer (score 76-100)")


class KnowledgeChunk(BaseModel):
    id: str
    role_id: str
    competency: str
    stage: str
    difficulty_level: int = Field(ge=1, le=5)
    title: str
    content: str
    expected_concepts: List[str] = Field(default_factory=list)
    sample_questions: List[str] = Field(default_factory=list)
    rubric: RubricCriteria
    source: str = "KnowledgeBase-Internal"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # Domain-Aware Provenance Extensions
    domain: str = Field(default="cyber_computing", description="DRDO scientific domain key")
    discipline: Optional[str] = Field(default=None, description="Discipline identifier")
    topic: Optional[str] = Field(default=None, description="Specific technical topic")
    source_title: Optional[str] = Field(default=None, description="Formal source document/standard title")
    source_type: Optional[str] = Field(default=None, description="official_standard | textbook | research_paper")
    source_reference: Optional[str] = Field(default=None, description="Public citation/reference identifier")


# ---------------------------------------------------------
# Question Models (Section 11.2 Contract)
# ---------------------------------------------------------

class QuestionType(str, Enum):
    CONCEPTUAL = "conceptual"
    IMPLEMENTATION = "implementation"
    DEBUGGING = "debugging"
    TRADE_OFF = "trade_off"
    SCENARIO = "scenario"
    DESIGN = "design"
    FOLLOW_UP = "follow_up"


class QuestionObject(BaseModel):
    id: str = Field(..., description="Unique question ID")
    text: str = Field(..., description="The interview question text")
    stage: str = Field(..., description="Stage: ice_breaker | fundamentals | role_technical | deep_dive | scenario_managerial")
    competency: str = Field(..., description="Target competency (e.g. backend, database, system_design)")
    difficulty: int = Field(ge=1, le=5, description="Difficulty level 1-5")
    expectedConcepts: List[str] = Field(default_factory=list, description="Key concepts expected in a strong answer")
    rubric: RubricCriteria = Field(..., description="Grading criteria for the question")
    relevanceScore: int = Field(ge=0, le=100, description="Explainable question relevance score (0-100)")
    relevanceRationale: Optional[str] = Field(None, description="Explanation of why this question is relevant")
    sources: List[str] = Field(default_factory=list, description="Grounding source IDs or references")
    isFallback: bool = Field(default=False, description="Whether this question was loaded from the curated fallback bank")
    # Phase A: Interview Intelligence extensions (optional with safe defaults)
    questionType: Optional[str] = Field(default="conceptual", description="conceptual | implementation | debugging | trade_off | scenario | design | follow_up")
    adaptiveReason: Optional[str] = Field(default=None, description="Adaptive justification for question selection")
    questionExplanation: Optional[Dict[str, Any]] = Field(default=None, description="Internal explanation of role alignment, candidate alignment, difficulty, and target concepts")
    # DRDO Domain Extensions
    domain: Optional[str] = Field(default=None, description="DRDO domain key, e.g. electronics_radar")
    candidateClaim: Optional[str] = Field(default=None, description="Candidate claim being probed in expertise validation")



# ---------------------------------------------------------
# Question Relevance Breakdown Model (Section 7.1)
# ---------------------------------------------------------

class QuestionRelevanceBreakdown(BaseModel):
    roleAlignment: int = Field(ge=0, le=100, description="Weight 30%")
    candidateExpertiseAlignment: int = Field(ge=0, le=100, description="Weight 25%")
    targetCompetencyAlignment: int = Field(ge=0, le=100, description="Weight 20%")
    difficultyAppropriateness: int = Field(ge=0, le=100, description="Weight 15%")
    specificityClarity: int = Field(ge=0, le=100, description="Weight 10%")
    totalScore: int = Field(ge=0, le=100, description="Weighted total score")
    rationale: str = Field(..., description="Concise explainable rationale")
    domainAlignment: Optional[int] = Field(default=None, description="Domain boundary score (0-100)")
    groundingScore: Optional[int] = Field(default=None, description="Source provenance grounding score (0-100)")


# ---------------------------------------------------------
# Request & Response Contracts for APIs
# ---------------------------------------------------------

class RetrievalRequest(BaseModel):
    query: str
    role_id: Optional[str] = "backend_engineer"
    competency: Optional[str] = None
    stage: Optional[str] = None
    difficulty: Optional[int] = None
    top_k: int = Field(default=3, ge=1, le=10)
    domain: Optional[str] = Field(default=None, description="DRDO scientific domain key, e.g. electronics_radar")
    prohibited_domains: Optional[List[str]] = Field(default_factory=list, description="Strictly prohibited cross-domains")


class RetrievalResult(BaseModel):
    chunk_id: str
    title: str
    competency: str
    stage: str
    difficulty_level: int
    score: float
    content: str
    expected_concepts: List[str]
    rubric: RubricCriteria
    source: str
    domain: Optional[str] = Field(default="cyber_computing", description="DRDO scientific domain key")
    source_title: Optional[str] = None
    source_reference: Optional[str] = None


class RetrievalResponse(BaseModel):
    query: str
    total_found: int
    results: List[RetrievalResult]


class GenerateQuestionRequest(BaseModel):
    candidate: CandidateProfile = Field(default_factory=CandidateProfile)
    role: TargetRole = Field(default_factory=TargetRole)
    stage: str = Field("role_technical", description="ice_breaker | fundamentals | role_technical | deep_dive | scenario_managerial")
    competency: str = Field("backend", description="Competency name (e.g., backend, database, system_design)")
    difficulty: int = Field(3, ge=1, le=5)
    previousQuestions: List[str] = Field(default_factory=list, description="List of previous questions asked to avoid duplication")
    previousMissingConcepts: List[str] = Field(default_factory=list, description="Concepts missed in previous answer for adaptive probing")
    questionType: Optional[QuestionType] = Field(None, description="Optional question style: conceptual | implementation | debugging | trade_off | scenario | design | follow_up")
    adaptiveReason: Optional[str] = Field(None, description="Optional explanation for why this question is being asked adaptively")


class AdaptiveContextRequest(BaseModel):
    previousQuestions: List[str] = Field(default_factory=list)
    coveredConcepts: List[str] = Field(default_factory=list)
    missingConcepts: List[str] = Field(default_factory=list)
    currentDifficulty: int = Field(3, ge=1, le=5)
    lastScore: Optional[int] = Field(None, ge=0, le=100)
    currentCompetency: str = "backend"
    currentStage: str = "role_technical"


# ---------------------------------------------------------
# Phase C: Closed-Loop Turn & Orchestration Contracts
# ---------------------------------------------------------

class EvaluationResult(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Candidate answer score (0-100)")
    coveredConcepts: List[str] = Field(default_factory=list, description="Concepts successfully demonstrated in answer")
    missingConcepts: List[str] = Field(default_factory=list, description="Concepts missing or inadequately addressed")
    reasoning: str = Field(default="", description="Explainable rationale for the score and concept attribution")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Evaluator confidence in scoring")
    technicalCorrectness: str = Field(default="adequate", description="Evaluation of technical correctness: accurate | partially_accurate | inaccurate")
    completeness: str = Field(default="adequate", description="Evaluation of completeness: complete | partial | minimal")
    relevance: str = Field(default="relevant", description="Evaluation of relevance: directly_relevant | partially_relevant | off_topic")
    depth: str = Field(default="adequate", description="Evaluation of technical depth: deep | adequate | shallow")
    isFallback: bool = Field(default=False, description="Flag indicating if deterministic fallback was used instead of primary LLM")


class DecisionObject(BaseModel):
    strategy: str = Field(..., description="Adaptive strategy chosen")
    nextDifficulty: int = Field(..., ge=1, le=5, description="Calibrated difficulty for next question")
    nextCompetency: str = Field(..., description="Target competency for next question")
    targetConcepts: List[str] = Field(default_factory=list, description="Target concepts chosen for next question")
    questionType: str = Field(..., description="Recommended question type")
    reason: str = Field(..., description="Machine-readable decision rationale based on actual state")


class DecisionTrace(BaseModel):
    previousScore: Optional[int] = None
    trend: str = Field(default="neutral", description="improving | declining | stable | neutral")
    missingConcepts: List[str] = Field(default_factory=list)
    persistentWeaknesses: List[str] = Field(default_factory=list)
    prerequisiteIssues: List[str] = Field(default_factory=list)
    strategy: str
    nextDifficulty: int = Field(ge=1, le=5)
    nextCompetency: str
    questionType: str
    targetConcepts: List[str] = Field(default_factory=list)
    reason: str


class TerminationDecision(BaseModel):
    shouldTerminate: bool = Field(default=False, description="Whether the interview should conclude")
    reason: str = Field(..., description="Explainable termination rationale")
    evidenceCoverage: float = Field(default=0.0, ge=0.0, le=1.0, description="Evidence coverage proportion")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic criteria details")


class TurnObject(BaseModel):
    question: QuestionObject
    answer: str
    evaluation: EvaluationResult
    decision: DecisionObject


class TurnRequest(BaseModel):
    interviewState: Optional[Dict[str, Any]] = Field(default=None, description="Current interview state object (or None to initialize)")
    currentQuestion: QuestionObject = Field(..., description="The question being answered in this turn")
    candidateAnswer: str = Field(..., description="The candidate's response text")
    evaluation: Optional[EvaluationResult] = Field(default=None, description="Optional evaluation result from Member 4")
    candidate: Optional[CandidateProfile] = Field(default_factory=CandidateProfile)
    role: Optional[TargetRole] = Field(default_factory=TargetRole)


class TurnResponse(BaseModel):
    updatedState: Dict[str, Any] = Field(..., description="Serialized updated InterviewState")
    evaluation: EvaluationResult = Field(..., description="Result of answer evaluation")
    decision: DecisionObject = Field(..., description="Adaptive decision for the next step")
    nextQuestion: Optional[QuestionObject] = Field(None, description="Next generated question (None if terminated)")
    termination: TerminationDecision = Field(..., description="Structured termination evaluation")
    trace: DecisionTrace = Field(..., description="Machine-readable decision trace")


class InterviewStartRequest(BaseModel):
    candidate: Optional[CandidateProfile] = Field(default_factory=CandidateProfile)
    role: Optional[TargetRole] = Field(default_factory=TargetRole)


class InterviewStartResponse(BaseModel):
    interviewState: Dict[str, Any] = Field(..., description="Initialized clean InterviewState")
    openingQuestion: QuestionObject = Field(..., description="First interview question (ice_breaker)")


# ---------------------------------------------------------
# Phase D: Evidence-Based Competency Assessment & Scorecard
# ---------------------------------------------------------

class ConceptEvidenceProvenance(BaseModel):
    turnId: int
    questionId: str
    questionType: str
    stage: str
    score: int
    isDemonstrated: bool


class ConceptEvidence(BaseModel):
    concept: str
    competency: str
    testedCount: int = 0
    demonstratedCount: int = 0
    partialCount: int = 0
    missedCount: int = 0
    highestScore: int = 0
    latestScore: int = 0
    averageScore: float = 0.0
    questionTypes: List[str] = Field(default_factory=list)
    stages: List[str] = Field(default_factory=list)
    masteryLevel: str = "untested"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    provenance: List[ConceptEvidenceProvenance] = Field(default_factory=list)


class CompetencyEvidence(BaseModel):
    competency: str
    score: int = Field(ge=0, le=100, description="Observed quality of answers in this competency (0-100)")
    confidence: float = Field(ge=0.0, le=1.0, description="Evidence confidence based on demonstration depth (0.0-1.0)")
    coverage: float = Field(default=0.0, ge=0.0, le=1.0, description="Proportion of role concepts tested (0.0-1.0)")
    status: str = Field(..., description="demonstrated | partially_demonstrated | weak | insufficient_evidence | untested")
    testedConcepts: List[str] = Field(default_factory=list)
    demonstratedConcepts: List[str] = Field(default_factory=list)
    partialConcepts: List[str] = Field(default_factory=list)
    missingConcepts: List[str] = Field(default_factory=list)
    evidenceCount: int = Field(default=0, description="Total turns evaluating this competency")
    strongEvidence: List[str] = Field(default_factory=list)
    weakEvidence: List[str] = Field(default_factory=list)
    contradictoryEvidence: List[str] = Field(default_factory=list)
    reasoning: str = Field(..., description="Explainable rationale referencing turns and concepts")


class StrengthItem(BaseModel):
    area: str
    competency: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)
    supportingTurns: List[int] = Field(default_factory=list)


class GapItem(BaseModel):
    area: str
    competency: str
    evidence: str
    severity: str = Field(default="moderate", description="low | moderate | high")
    supportingTurns: List[int] = Field(default_factory=list)
    prerequisiteStatus: Optional[str] = None


class RoleAlignmentItem(BaseModel):
    requirement: str
    status: str = Field(..., description="demonstrated | partially_demonstrated | insufficiently_tested | missing")
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)


class RoleAlignmentAnalysis(BaseModel):
    roleId: str
    roleTitle: str
    alignmentScore: int = Field(ge=0, le=100)
    demonstratedRequirements: List[str] = Field(default_factory=list)
    partiallyDemonstratedRequirements: List[str] = Field(default_factory=list)
    insufficientlyTestedRequirements: List[str] = Field(default_factory=list)
    missingRequirements: List[str] = Field(default_factory=list)
    details: List[RoleAlignmentItem] = Field(default_factory=list)
    rationale: str


class EvidenceTimelineItem(BaseModel):
    turn: int
    stage: str
    competency: str
    difficulty: int
    questionId: str
    questionText: str
    questionType: str
    score: int
    coveredConcepts: List[str] = Field(default_factory=list)
    missingConcepts: List[str] = Field(default_factory=list)
    evidenceStatus: str = Field(..., description="demonstrated | partially_demonstrated | missing | recovered")
    summary: str


class CompetencyCoverageData(BaseModel):
    competency: str
    coverage: float = Field(ge=0.0, le=1.0)
    score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    status: str


class CoverageDashboardData(BaseModel):
    overallEvidenceCoverage: float = Field(ge=0.0, le=1.0)
    competencyCoverage: List[CompetencyCoverageData] = Field(default_factory=list)
    testedConceptsCount: int = 0
    demonstratedConceptsCount: int = 0
    missingConceptsCount: int = 0
    stagesVisitedCount: int = 0


class DecisionSupportReport(BaseModel):
    technicalEvidence: str
    managerialEvidence: str
    roleAlignmentEvidence: str
    areasRequiringFurtherAssessment: List[str] = Field(default_factory=list)
    recommendationNote: str = "Decision-support summary for human selector. BoardRoom AI does not make autonomous hiring decisions."


class FinalScorecard(BaseModel):
    candidate: CandidateProfile
    role: TargetRole
    overallScore: int = Field(ge=0, le=100, description="Weighted composite competency score (0-100)")
    overallConfidence: float = Field(ge=0.0, le=1.0, description="Weighted composite evidence confidence (0.0-1.0)")
    competencies: List[CompetencyEvidence] = Field(default_factory=list)
    strengths: List[StrengthItem] = Field(default_factory=list)
    gaps: List[GapItem] = Field(default_factory=list)
    coverage: CoverageDashboardData
    roleAlignment: RoleAlignmentAnalysis
    decisionSupport: DecisionSupportReport
    evidenceTimeline: List[EvidenceTimelineItem] = Field(default_factory=list)
    explanation: str


class ScorecardRequest(BaseModel):
    interviewState: Optional[Dict[str, Any]] = Field(default=None, description="Completed interview state dict or object")
    candidate: Optional[CandidateProfile] = Field(default_factory=CandidateProfile)
    role: Optional[TargetRole] = Field(default_factory=TargetRole)
    competencyWeights: Optional[Dict[str, float]] = Field(default=None, description="Optional custom weights per competency")


class ScorecardResponse(BaseModel):
    scorecard: FinalScorecard
    competencies: List[CompetencyEvidence]
    strengths: List[StrengthItem]
    gaps: List[GapItem]
    evidenceTimeline: List[EvidenceTimelineItem]
    coverage: CoverageDashboardData
    roleAlignment: RoleAlignmentAnalysis
    decisionSupport: DecisionSupportReport
    explanation: str


