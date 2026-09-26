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


class TargetRole(BaseModel):
    id: str = "backend_engineer"
    title: str = "Backend / Full-Stack Software Engineer"
    description: Optional[str] = "Designs, builds, and maintains server-side applications, APIs, and databases."
    required_skills: List[str] = Field(default_factory=lambda: ["Python", "SQL", "REST APIs", "System Design", "Git"])
    min_experience_years: Optional[float] = 1.0


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
