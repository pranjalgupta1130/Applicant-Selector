"""
Answer-evaluation endpoints (Member 4).

Mounted by main.py alongside api/routes.py. These are the direct-call endpoints
for the backend and frontend; the closed-loop pipeline reaches the same engine
through AnswerEvaluationAdapter instead.

    POST /api/ai/evaluate-answer     -> EvaluationResult (full detail)
    POST /api/ai/evaluate-answers    -> batch, same shape per item
    GET  /api/ai/evaluation-health   -> which scoring path is live right now
"""

from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.config import settings
from core.schemas import EvaluationResult, QuestionObject, RubricCriteria
from evaluator.matching import COVERAGE_THRESHOLD, embedding_backend_available
from evaluator.real_evaluator import RealAnswerEvaluator, _force_deterministic
from evaluator.scoring import (
    MIN_SUBSTANTIVE_TOKENS,
    NOVELTY_FLOOR,
    OFF_TOPIC_RELEVANCE,
    WEIGHTS,
)

router = APIRouter(prefix="/api", tags=["Answer Evaluation"])

_evaluator = RealAnswerEvaluator()

_DEFAULT_RUBRIC = RubricCriteria(
    poor="Does not address the expected concepts.",
    acceptable="Addresses the main expected concepts without depth.",
    excellent="Addresses all expected concepts with specifics and trade-offs.",
)


class EvaluateAnswerRequest(BaseModel):
    """
    Accepts either a full QuestionObject (preferred -- pass straight through
    from /ai/generate-question) or the loose fields, for callers that only have
    the question text to hand.
    """

    question: Optional[QuestionObject] = None
    questionId: str = "q_adhoc"
    questionText: str = ""
    answerText: str = ""
    expectedConcepts: List[str] = Field(default_factory=list)
    rubric: Optional[RubricCriteria] = None
    stage: str = "role_technical"
    competency: str = "general"
    difficulty: int = Field(default=3, ge=1, le=5)

    def to_question(self) -> QuestionObject:
        if self.question is not None:
            return self.question
        return QuestionObject(
            id=self.questionId,
            text=self.questionText,
            stage=self.stage,
            competency=self.competency,
            difficulty=self.difficulty,
            expectedConcepts=self.expectedConcepts,
            rubric=self.rubric or _DEFAULT_RUBRIC,
            relevanceScore=0,
        )


class BatchEvaluateRequest(BaseModel):
    items: List[EvaluateAnswerRequest] = Field(default_factory=list)


@router.post(
    "/ai/evaluate-answer",
    response_model=EvaluationResult,
    summary="Evaluate a candidate answer with explainable sub-scores",
)
async def evaluate_answer_endpoint(req: EvaluateAnswerRequest) -> EvaluationResult:
    """
    Always 200 with a complete EvaluationResult for a valid body; 422 only for a
    malformed request. If the LLM is unavailable the response carries
    evaluationMode="deterministic" rather than failing, so the interview never
    dead-ends mid-demo.
    """
    return _evaluator.evaluate(req.to_question(), req.answerText)


@router.post(
    "/ai/evaluate-answers",
    response_model=List[EvaluationResult],
    summary="Batch-evaluate answers (same contract per item)",
)
async def evaluate_answers_endpoint(
    req: BatchEvaluateRequest,
) -> List[EvaluationResult]:
    return [_evaluator.evaluate(i.to_question(), i.answerText) for i in req.items]


@router.get(
    "/ai/evaluation-health",
    summary="Report the live answer-evaluation configuration",
)
async def evaluation_health() -> dict:
    """
    Check this before the demo. Reports which path will run and why. Never
    returns the key itself, only whether one is configured.
    """
    forced = _force_deterministic()
    has_key = bool(settings.GEMINI_API_KEY)
    return {
        "status": "healthy",
        "component": "Answer Evaluation Subsystem (Member 4)",
        "scoringMode": "deterministic" if (forced or not has_key) else "llm_assisted",
        "llmConfigured": has_key,
        "llmModel": settings.DEFAULT_LLM_MODEL,
        "forcedDeterministic": forced,
        "closedLoopUsesRealEvaluator": os.getenv("EVAL_USE_REAL", "").strip().lower()
        in ("1", "true", "yes", "on"),
        "embeddingBackend": (
            "sentence-transformers"
            if embedding_backend_available()
            else "lexical_fallback"
        ),
        "answerWeights": WEIGHTS,
        "thresholds": {
            "coverageThreshold": COVERAGE_THRESHOLD,
            "offTopicRelevance": OFF_TOPIC_RELEVANCE,
            "minSubstantiveTokens": MIN_SUBSTANTIVE_TOKENS,
            "noveltyFloor": NOVELTY_FLOOR,
        },
        "disclaimer": (
            "AI-assisted simulation. Scores are decision support for a human "
            "panel, not a hiring decision."
        ),
    }
