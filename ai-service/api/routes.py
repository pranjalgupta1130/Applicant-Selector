"""
FastAPI router exposing RAG and Question Generation endpoints.
Directly implements Master Plan Section 9 and 11.2.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

from core.schemas import (
    RetrievalRequest,
    RetrievalResponse,
    GenerateQuestionRequest,
    QuestionObject,
    QuestionRelevanceBreakdown,
    AdaptiveContextRequest,
    CandidateProfile,
    TargetRole,
    TurnRequest,
    TurnResponse,
    InterviewStartRequest,
    InterviewStartResponse,
    ScorecardRequest,
    ScorecardResponse
)
from rag.retriever import KnowledgeRetriever
from generator.pipeline import QuestionGeneratorPipeline
from evaluator.relevance import QuestionRelevanceEvaluator
from adaptive.strategy import AdaptiveInterviewEngine, AdaptiveRecommendation
from adaptive.state import InterviewState
from adaptive.policy import AdaptiveInterviewPolicy, PolicyDecision
from adaptive.orchestrator import InterviewOrchestrator
from adaptive.scorecard_engine import ScorecardEngine

router = APIRouter(prefix="/api", tags=["RAG & Question Generation"])


# Shared pipeline instances
_retriever = KnowledgeRetriever()
_pipeline = QuestionGeneratorPipeline(retriever=_retriever)
_orchestrator = InterviewOrchestrator(retriever=_retriever, generator=_pipeline)


class QuestionRelevanceRequest(BaseModel):
    question_text: str
    role: Optional[TargetRole] = TargetRole()
    candidate: Optional[CandidateProfile] = CandidateProfile()
    competency: str = "backend"
    stage: str = "role_technical"
    difficulty: int = 3
    expected_concepts: Optional[List[str]] = None


@router.post("/rag/retrieve", response_model=RetrievalResponse, summary="Retrieve top-k grounding knowledge chunks")
async def retrieve_knowledge(req: RetrievalRequest):
    """
    Retrieves grounded role, competency, and rubric context using metadata filtering and vector ranking.
    """
    try:
        response = _retriever.retrieve(
            query=req.query,
            role_id=req.role_id,
            competency=req.competency,
            stage=req.stage,
            difficulty=req.difficulty,
            top_k=req.top_k
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")


@router.post("/ai/generate-question", response_model=QuestionObject, summary="Generate structured interview question")
async def generate_interview_question(req: GenerateQuestionRequest):
    """
    Generates a structured, grounded interview question with expected concepts, rubric,
    and explainable relevance score according to candidate profile, role, stage, and competency.
    """
    try:
        question = _pipeline.generate(
            candidate=req.candidate,
            role=req.role,
            stage=req.stage,
            competency=req.competency,
            difficulty=req.difficulty,
            previous_questions=req.previousQuestions,
            previous_missing_concepts=req.previousMissingConcepts,
            question_type=req.questionType,
            adaptive_reason=req.adaptiveReason
        )
        return question
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


@router.post("/ai/evaluate-question-relevance", response_model=QuestionRelevanceBreakdown, summary="Audit question relevance")
async def evaluate_question_relevance(req: QuestionRelevanceRequest):
    """
    Evaluates question relevance across Role (30%), Candidate (25%), Competency (20%),
    Difficulty (15%), and Clarity (10%).
    """
    try:
        breakdown = QuestionRelevanceEvaluator.evaluate(
            question_text=req.question_text,
            role=req.role or TargetRole(),
            candidate=req.candidate or CandidateProfile(),
            competency=req.competency,
            stage=req.stage,
            difficulty=req.difficulty,
            expected_concepts=req.expected_concepts
        )
        return breakdown
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Relevance evaluation failed: {str(e)}")


@router.post(
    "/ai/adaptive-context",
    response_model=AdaptiveRecommendation,
    deprecated=True,
    summary="[DEPRECATED] Stateless adaptive context recommendation"
)
async def get_adaptive_context(req: AdaptiveContextRequest):
    """
    [DEPRECATED] Legacy stateless adaptive context endpoint.
    CANONICAL INTERVIEW FLOW: Use the stateful closed-loop interview engine at:
      - POST /api/interview/start
      - POST /api/interview/turn
      - POST /api/interview/scorecard
    This endpoint is preserved strictly for backwards compatibility and is marked deprecated.
    """
    try:
        recommendation = AdaptiveInterviewEngine.recommend_next_step(req)
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adaptive analysis failed: {str(e)}")



@router.post("/ai/adaptive-policy-step", response_model=PolicyDecision, summary="Deterministic adaptive policy evaluation")
async def evaluate_adaptive_policy_step(state: InterviewState):
    """
    Evaluates the full InterviewState model and deterministically decides:
    - difficulty calibration (escalate / de-escalate / maintain)
    - concept gap probing (triggers follow-up question targeting specific missing concept)
    - competency progression and transition
    - stage ladder progression (ice_breaker -> fundamentals -> role_technical -> deep_dive -> scenario_managerial)
    - interview conclusion
    """
    try:
        decision = AdaptiveInterviewPolicy.evaluate_next_step(state)
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adaptive policy evaluation failed: {str(e)}")


@router.post("/interview/start", response_model=InterviewStartResponse, summary="Initialize clean interview state and opening question")
async def start_interview_session(req: Optional[InterviewStartRequest] = None):
    """
    Initializes a fresh InterviewState and generates the opening ice-breaker question.
    """
    try:
        req = req or InterviewStartRequest()
        return _orchestrator.start_interview(
            candidate=req.candidate,
            role=req.role
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interview initiation failed: {str(e)}")


@router.post("/interview/turn", response_model=TurnResponse, summary="Process completed interview turn closed-loop")
async def process_interview_turn(req: TurnRequest):
    """
    Executes one complete closed-loop turn:
    Candidate Answer -> Answer Evaluation -> Concept Coverage -> Mastery Update ->
    Trend/Streak Update -> Adaptive Policy Decision -> Target Concept Selection ->
    RAG Retrieval -> Next Question.
    """
    try:
        response = _orchestrator.process_turn(
            current_question=req.currentQuestion,
            candidate_answer=req.candidateAnswer,
            interview_state=req.interviewState,
            evaluation=req.evaluation,
            candidate=req.candidate,
            role=req.role
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Closed-loop turn processing failed: {str(e)}")


@router.post("/interview/scorecard", response_model=ScorecardResponse, summary="Generate evidence-based competency scorecard")
async def generate_candidate_scorecard(req: ScorecardRequest):
    """
    Synthesizes the complete interview trajectory into an evidence-based FinalScorecard.
    Aggregates:
    - Competency scores and confidence
    - Evidence-backed strengths & gaps
    - Role alignment analysis
    - Chronological evidence timeline
    - Dashboard coverage metrics
    - Human decision support (strictly non-autonomous)
    """
    try:
        raw_state = req.interviewState
        if isinstance(raw_state, InterviewState):
            state = raw_state
        elif isinstance(raw_state, dict) and raw_state:
            state = InterviewState(**raw_state)
        else:
            state = InterviewState(
                candidate_id=req.candidate.id or "cand_default",
                role_id=req.role.id or "backend_engineer"
            )

        scorecard = ScorecardEngine.generate_scorecard(
            state=state,
            candidate=req.candidate,
            role=req.role,
            custom_weights=req.competencyWeights
        )

        import logging
        logging.getLogger(__name__).info(
            f"[REPORT TRACE] location=Python scorecard_engine candidateId={req.candidate.id} "
            f"roleId={req.role.id} turnCount={len(state.previous_questions)} "
            f"evaluatedTurnCount={len(state.score_history)} scorecardOverall={scorecard.overallScore} "
            f"coverage={scorecard.coverage.overallEvidenceCoverage} confidence={scorecard.coverage.overallConfidence} "
            f"competencies={[c.competency for c in scorecard.competencies]}"
        )

        return ScorecardResponse(
            scorecard=scorecard,
            competencies=scorecard.competencies,
            strengths=scorecard.strengths,
            gaps=scorecard.gaps,
            evidenceTimeline=scorecard.evidenceTimeline,
            coverage=scorecard.coverage,
            roleAlignment=scorecard.roleAlignment,
            decisionSupport=scorecard.decisionSupport,
            explanation=scorecard.explanation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scorecard generation failed: {str(e)}")


