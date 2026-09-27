"""
RealAnswerEvaluator -- the production evaluation path (Member 4).

Implements the same BaseAnswerEvaluator interface as MockAnswerEvaluator, so it
drops into AnswerEvaluationAdapter and the orchestrator without touching either:

    from evaluator.real_evaluator import RealAnswerEvaluator
    adapter = AnswerEvaluationAdapter(fallback_evaluator=RealAnswerEvaluator())

Differences from the mock, which existed to unblock the adaptive pipeline:

  * Concept coverage is semantic (embeddings, lexical fallback) rather than
    substring matching, so "token expiry" matches "short-lived access tokens"
    and a paraphrase is not scored as a miss.
  * The score is a weighted formula over five sub-scores (Section 7.2), not a
    coverage-ratio ladder, and the full breakdown ships with every result.
  * Five deterministic guardrails cap or penalise off-topic, too-short, refused,
    zero-coverage and factually-incorrect answers.
  * Optional LLM sub-scores for correctness, reasoning and clarity -- which the
    mock cannot judge at all -- while the LLM is still barred from setting the total.
  * Every concept carries the candidate's own sentence as evidence.

The mock stays in place as the default, so existing tests and any offline
development flow are unaffected.
"""

from __future__ import annotations

import os
from typing import Optional

from core.schemas import (
    AnswerSubScores,
    ConceptCoverageDetail,
    EvaluationResult,
    QuestionObject,
)

from .answer_evaluator import BaseAnswerEvaluator, MockAnswerEvaluator
from .scoring import score_answer


def _force_deterministic() -> bool:
    """Demo-safety switch: EVAL_FORCE_DETERMINISTIC=1 pins the offline path."""
    return os.getenv("EVAL_FORCE_DETERMINISTIC", "").strip().lower() in (
        "1", "true", "yes", "on",
    )


class RealAnswerEvaluator(BaseAnswerEvaluator):
    """
    Weighted, explainable answer evaluation with optional LLM sub-scores.

    Args:
        use_llm: None (default) reads the environment -- LLM path when a key is
                 configured and EVAL_FORCE_DETERMINISTIC is unset. True/False
                 pins the behaviour, which the test suite relies on.
    """

    def __init__(self, use_llm: Optional[bool] = None) -> None:
        self._use_llm = use_llm

    @property
    def use_llm(self) -> bool:
        if self._use_llm is not None:
            return self._use_llm
        return not _force_deterministic()

    def evaluate(
        self, question: QuestionObject, candidate_answer: str
    ) -> EvaluationResult:
        """Never raises. Returns a complete EvaluationResult in every path."""
        result = score_answer(question, candidate_answer, use_llm=self.use_llm)

        return EvaluationResult(
            # --- frozen core, consumed by orchestrator + scorecard engine ----
            score=result["total"],
            coveredConcepts=result["coveredConcepts"],
            missingConcepts=result["missingConcepts"],
            reasoning=result["reasoning"],
            confidence=result["confidence"],
            # --- additive explainability -------------------------------------
            subScores=AnswerSubScores(**result["subScores"]),
            partialConcepts=result["partialConcepts"],
            conceptDetail=[
                ConceptCoverageDetail(**d) for d in result["conceptDetail"]
            ],
            scoreBreakdown=result["scoreBreakdown"],
            flags=result["flags"],
            evaluationMode=result["mode"],
            strategyHint=result["strategyHint"],
        )


def get_default_evaluator() -> BaseAnswerEvaluator:
    """
    Which evaluator the service should use.

    Defaults to the mock so existing behaviour and tests are unchanged; set
    EVAL_USE_REAL=1 (or call RealAnswerEvaluator directly) to switch the
    closed-loop pipeline onto the real engine. Flip it in .env once the team has
    agreed, rather than changing code paths under each other mid-hackathon.
    """
    if os.getenv("EVAL_USE_REAL", "").strip().lower() in ("1", "true", "yes", "on"):
        return RealAnswerEvaluator()
    return MockAnswerEvaluator()
