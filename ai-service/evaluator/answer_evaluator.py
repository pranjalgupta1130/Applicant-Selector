"""
Answer Evaluation Layer & Adapters for BoardRoom AI (Phase C).
Maintains strict architectural boundary: RAG and question generation never score answers.
Consumes evaluation results from Member 4's evaluation layer or provides a deterministic
mock adapter for development, testing, and simulation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import re

from core.schemas import QuestionObject, EvaluationResult


class BaseAnswerEvaluator(ABC):
    """Abstract interface that all answer evaluators (Mock or Real Member 4) must implement."""

    @abstractmethod
    def evaluate(self, question: QuestionObject, candidate_answer: str) -> EvaluationResult:
        """Evaluates candidate response against question criteria and expected concepts."""
        pass


class MockAnswerEvaluator(BaseAnswerEvaluator):
    """
    Deterministic answer evaluator for simulation, testing, and decoupled development.
    Scores answers based on expected concept presence, rubric alignment, and response quality.
    """

    def evaluate(self, question: QuestionObject, candidate_answer: str) -> EvaluationResult:
        cleaned_answer = (candidate_answer or "").strip()
        answer_lower = cleaned_answer.lower()

        expected = question.expectedConcepts or []
        if not expected:
            # Fallback if question lacked explicit expected concepts
            expected = [question.competency]

        # Check for empty / refusal responses
        refusal_phrases = ["i don't know", "i do not know", "skip", "no idea", "pass", "unsure", "not sure"]
        if not cleaned_answer or any(phrase in answer_lower for phrase in refusal_phrases) and len(cleaned_answer) < 30:
            return EvaluationResult(
                score=25,
                coveredConcepts=[],
                missingConcepts=list(expected),
                reasoning="Candidate provided minimal or no technical response; all expected concepts were missing.",
                confidence=0.95
            )

        # Detect covered vs missing concepts deterministically
        covered: List[str] = []
        missing: List[str] = []

        for concept in expected:
            norm_concept = concept.lower().strip()
            # Tokenize concept keywords (ignoring short stopwords)
            tokens = [t for t in re.split(r"[\s\-_]+", norm_concept) if len(t) > 2]
            
            # Exact or phrase match
            if norm_concept in answer_lower:
                covered.append(concept)
            elif tokens and all(t in answer_lower for t in tokens):
                covered.append(concept)
            elif any(t in answer_lower for t in tokens) and len(tokens) <= 2:
                covered.append(concept)
            else:
                missing.append(concept)

        total_expected = len(expected)
        coverage_ratio = len(covered) / total_expected if total_expected > 0 else 0.0

        # Rubric alignment scoring
        rubric = question.rubric
        excellent_keywords = [w.lower() for w in re.split(r"\W+", rubric.excellent) if len(w) > 4]
        poor_keywords = [w.lower() for w in re.split(r"\W+", rubric.poor) if len(w) > 4]

        excellent_hits = sum(1 for w in excellent_keywords if w in answer_lower)
        poor_hits = sum(1 for w in poor_keywords if w in answer_lower)

        # Compute deterministic baseline score
        if coverage_ratio >= 0.85:
            base_score = 88
        elif coverage_ratio >= 0.60:
            base_score = 75
        elif coverage_ratio >= 0.30:
            base_score = 56
        elif coverage_ratio > 0.0:
            base_score = 44
        else:
            base_score = 30

        # Adjust for rubric cues and depth
        score_adj = min(8, excellent_hits * 2) - min(10, poor_hits * 3)
        final_score = max(0, min(100, base_score + score_adj))

        # Confidence: higher when evidence is clear (many concepts or clear answer)
        confidence = 0.80 + (0.10 if len(cleaned_answer) > 100 else 0.0) + (0.05 if coverage_ratio in (0.0, 1.0) else 0.0)
        confidence = min(0.95, round(confidence, 2))

        # Explainable reasoning
        if covered and not missing:
            reasoning = f"Candidate comprehensively addressed all expected concepts ({', '.join(covered)}) with strong technical clarity."
        elif covered and missing:
            reasoning = f"Candidate demonstrated understanding of {', '.join(covered)}, but omitted critical concepts: {', '.join(missing)}."
        else:
            reasoning = f"Candidate failed to address expected concepts: {', '.join(missing)}."

        return EvaluationResult(
            score=final_score,
            coveredConcepts=covered,
            missingConcepts=missing,
            reasoning=reasoning,
            confidence=confidence
        )


class AnswerEvaluationAdapter:
    """
    Adapter that normalizes external evaluation input (from Member 4's service)
    or delegates to a registered evaluator (such as MockAnswerEvaluator).
    Guarantees strict schema conformity and safe boundary separation.
    """

    def __init__(self, fallback_evaluator: Optional[BaseAnswerEvaluator] = None):
        self.fallback_evaluator = fallback_evaluator or MockAnswerEvaluator()

    def process_evaluation(
        self,
        question: QuestionObject,
        candidate_answer: str,
        incoming_evaluation: Optional[Any] = None
    ) -> EvaluationResult:
        """
        Consumes an evaluation from Member 4 if supplied, or deterministically evaluates.
        Safely validates and clamps scores to 0-100 and confidence to 0.0-1.0.
        """
        if incoming_evaluation is not None:
            # Handle incoming EvaluationResult model
            if isinstance(incoming_evaluation, EvaluationResult):
                return EvaluationResult(
                    score=max(0, min(100, incoming_evaluation.score)),
                    coveredConcepts=list(incoming_evaluation.coveredConcepts),
                    missingConcepts=list(incoming_evaluation.missingConcepts),
                    reasoning=incoming_evaluation.reasoning or "Evaluated by Member 4 Evaluation Service.",
                    confidence=max(0.0, min(1.0, incoming_evaluation.confidence))
                )

            # Handle raw dict from HTTP request
            if isinstance(incoming_evaluation, dict):
                raw_score = incoming_evaluation.get("score", 70)
                try:
                    score = max(0, min(100, int(raw_score)))
                except (ValueError, TypeError):
                    score = 70

                covered = incoming_evaluation.get("coveredConcepts", incoming_evaluation.get("covered_concepts", []))
                missing = incoming_evaluation.get("missingConcepts", incoming_evaluation.get("missing_concepts", []))
                reasoning = incoming_evaluation.get("reasoning", "Provided via evaluation input.")
                raw_conf = incoming_evaluation.get("confidence", 0.85)
                try:
                    confidence = max(0.0, min(1.0, float(raw_conf)))
                except (ValueError, TypeError):
                    confidence = 0.85

                return EvaluationResult(
                    score=score,
                    coveredConcepts=list(covered) if isinstance(covered, list) else [],
                    missingConcepts=list(missing) if isinstance(missing, list) else [],
                    reasoning=str(reasoning),
                    confidence=confidence
                )

        # No evaluation supplied: delegate to evaluator
        return self.fallback_evaluator.evaluate(question, candidate_answer)
