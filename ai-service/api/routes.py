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
    TargetRole
)
from rag.retriever import KnowledgeRetriever
from generator.pipeline import QuestionGeneratorPipeline
from evaluator.relevance import QuestionRelevanceEvaluator
from adaptive.strategy import AdaptiveInterviewEngine, AdaptiveRecommendation
from adaptive.state import InterviewState
from adaptive.policy import AdaptiveInterviewPolicy, PolicyDecision

router = APIRouter(prefix="/api", tags=["RAG & Question Generation"])

# Shared pipeline instances
_retriever = KnowledgeRetriever()
_pipeline = QuestionGeneratorPipeline(retriever=_retriever)


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


@router.post("/ai/adaptive-context", response_model=AdaptiveRecommendation, summary="Determine adaptive next step")
async def get_adaptive_context(req: AdaptiveContextRequest):
    """
    Recommends next interview stage, competency, and difficulty calibration based on concept gaps.
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
