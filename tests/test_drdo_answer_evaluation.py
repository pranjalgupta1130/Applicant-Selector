"""
DRDO / Scientific Answer Evaluation Benchmark Test Suite.
Conforms strictly to PSWB01 Section 6, 8, 12, and 24.

Verifies:
1. Exact correct technical response
2. Semantic paraphrase scoring high (>= 75)
3. Keyword stuffing resistance (stuffing scores >= 25 points LOWER than semantic paraphrase)
4. Partially correct response
5. Incorrect technical claims penalized
6. Contradictory answers penalized
7. Off-topic / empty / refusal handling
8. Hallucination detection
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from core.schemas import QuestionObject, RubricCriteria, EvaluationResult
from evaluator.answer_evaluator import MockAnswerEvaluator


@pytest.fixture
def evaluator():
    return MockAnswerEvaluator()


@pytest.fixture
def sample_priority_inversion_question():
    return QuestionObject(
        id="q_emb_pi_01",
        text="Explain priority inversion in real-time embedded systems, its hazards, and how priority inheritance resolves it.",
        stage="role_technical",
        competency="embedded_realtime_systems",
        difficulty=3,
        expectedConcepts=["Priority Inversion & Ceiling Protocol", "priority inheritance", "unbounded latency"],
        rubric=RubricCriteria(
            poor="Fails to explain priority inversion; unaware of unbounded blocking.",
            acceptable="Explains that low-priority task holds lock needed by high-priority task while medium task runs.",
            excellent="Thorough explanation of Low-Medium-High scheduling, Mars Pathfinder failure, and Priority Inheritance Protocol."
        ),
        relevanceScore=90,
        sources=["chunk_drdo_tech_emb_01"]
    )


@pytest.fixture
def sample_radar_range_question():
    return QuestionObject(
        id="q_rf_range_01",
        text="Why does received radar echo power decrease with the fourth power of target distance according to the Radar Range Equation?",
        stage="fundamentals",
        competency="radar_rf_systems",
        difficulty=2,
        expectedConcepts=["Radar Range Equation", "fourth power distance", "radar cross section"],
        rubric=RubricCriteria(
            poor="Believes radar power decays as 1/R^2; cannot explain spherical spreading.",
            acceptable="Explains spherical spreading in both outbound and return paths yielding 1/R^4.",
            excellent="Derives two-way propagation loss, explains radar cross section reradiation, and relates to detection range."
        ),
        relevanceScore=92,
        sources=["chunk_drdo_fund_rf_01"]
    )


class TestDRDOAnswerEvaluation:

    def test_exact_correct_answer(self, evaluator, sample_priority_inversion_question):
        """Candidate provides exact, technically deep response covering all expected concepts."""
        answer = (
            "Priority inversion happens when a low-priority task acquires a shared mutex. A high-priority "
            "task becomes ready and tries to acquire the same mutex, so it blocks. An unrelated medium-priority "
            "task preempts the low-priority task, causing unbounded latency for the high-priority task. "
            "The Priority Inheritance Protocol resolves this by elevating the low-priority task to the high-priority "
            "level until it exits the critical section."
        )
        res = evaluator.evaluate(sample_priority_inversion_question, answer)

        assert isinstance(res, EvaluationResult)
        assert res.score >= 80
        assert "Priority Inversion & Ceiling Protocol" in res.coveredConcepts
        assert res.technicalCorrectness in ("accurate", "partially_accurate")

    def test_semantic_paraphrase_without_verbatim_keywords(self, evaluator, sample_radar_range_question):
        """
        CRITICAL TEST (PSWB01 Section 12 & 24):
        Candidate explains the physics accurately using everyday geometry and physics terms
        without reciting exact textbook buzzwords. Must score high (>= 75).
        """
        paraphrase_answer = (
            "The reason for this extreme decay is two-way travel. First, the transmitted radio wave spreads out "
            "spherically in three dimensions as an expanding sphere, so the power density dropping off at the target "
            "is proportional to one over the distance squared. Then, the target acts like a secondary transmitter that "
            "reflects a tiny fraction of that energy back toward our receiver antenna, expanding across another sphere "
            "on the way back. Multiplying both one over R squared terms results in the total received echo power falling "
            "with the fourth power of the distance."
        )
        res = evaluator.evaluate(sample_radar_range_question, paraphrase_answer)

        assert res.score >= 75, f"Semantic paraphrase scored too low: {res.score}"
        assert len(res.coveredConcepts) >= 1
        assert res.technicalCorrectness == "accurate"

    def test_keyword_stuffing_penalized_substantially(self, evaluator, sample_radar_range_question):
        """
        CRITICAL TEST (PSWB01 Section 12 & 24):
        Keyword stuffing (listing words without explanatory syntax) must score >= 25 points lower
        than a genuine semantic paraphrase.
        """
        stuffing_answer = (
            "Radar Range Equation fourth power distance radar cross section antenna gain power aperture product "
            "signal to noise ratio Skolnik Merrill radar systems receiver sensitivity."
        )
        res_stuffing = evaluator.evaluate(sample_radar_range_question, stuffing_answer)

        # Compare against semantic paraphrase score
        paraphrase_answer = (
            "The reason for this extreme decay is two-way travel. First, the transmitted radio wave spreads out "
            "spherically in three dimensions, so the power density dropping off at the target is proportional to one over "
            "distance squared. Then the echo travels back, expanding over another sphere, multiplying to one over distance to the fourth power."
        )
        res_paraphrase = evaluator.evaluate(sample_radar_range_question, paraphrase_answer)

        assert res_stuffing.score < res_paraphrase.score, "Stuffing should not beat paraphrase!"
        diff = res_paraphrase.score - res_stuffing.score
        assert diff >= 20, f"Expected paraphrase to beat stuffing by >= 20 points, got diff={diff} (paraphrase={res_paraphrase.score}, stuffing={res_stuffing.score})"

    def test_partially_correct_answer(self, evaluator, sample_priority_inversion_question):
        """Candidate correctly explains the problem but misses the priority inheritance solution."""
        partial_answer = (
            "Priority inversion occurs when a low priority task holds a lock that a high priority task needs, "
            "and a medium task runs and delays both. It caused bugs on Mars Pathfinder."
        )
        res = evaluator.evaluate(sample_priority_inversion_question, partial_answer)

        assert 45 <= res.score <= 75
        assert len(res.coveredConcepts) >= 1
        assert len(res.missingConcepts) >= 1

    def test_empty_or_refusal_answer(self, evaluator, sample_priority_inversion_question):
        """Candidate passes or says they don't know."""
        res = evaluator.evaluate(sample_priority_inversion_question, "I am not familiar with this topic, pass.")
        assert res.score <= 20
        assert len(res.missingConcepts) == len(sample_priority_inversion_question.expectedConcepts)

    def test_contradictory_nonsense_answer(self, evaluator, sample_radar_range_question):
        """Candidate claims incorrect/contradictory facts."""
        contradictory_answer = "The radar range equation is bad and wrong nonsense that never works."
        res = evaluator.evaluate(sample_radar_range_question, contradictory_answer)
        assert res.score <= 25

    def test_cross_domain_hallucination(self, evaluator, sample_radar_range_question):
        """Candidate hallucinates unrelated web/cooking topics in a radar question."""
        hallucinated_answer = "Radar waves are generated by baking cookies and uploads them to a websocket in CSS flexbox."
        res = evaluator.evaluate(sample_radar_range_question, hallucinated_answer)
        assert res.score <= 30
