"""
Golden Evaluation Suite for Candidate Answer Evaluation (Section 3 of Ralph Master Mission).
Tests all 10 critical evaluation categories:
1. Exact correct answer
2. Correct semantic paraphrase (MUST NOT score substantially lower)
3. Partial answer
4. Keyword stuffing but wrong reasoning (MUST NOT score highly)
5. Incorrect answer
6. Off-topic answer
7. Deep / excellent answer
8. Shallow but technically correct answer
9. Contradictory answer
10. Empty / minimal answer

Also tests malformed JSON handling, timeout fallback, score clamping,
and schema invariants across both GeminiAnswerEvaluator and deterministic fallback.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

import pytest
from unittest.mock import MagicMock, patch

from core.schemas import QuestionObject, RubricCriteria, EvaluationResult
from evaluator.answer_evaluator import (
    BaseAnswerEvaluator,
    MockAnswerEvaluator,
    DeterministicAnswerEvaluator,
    GeminiAnswerEvaluator,
    AnswerEvaluationAdapter
)


# ---------------------------------------------------------
# Test Fixtures & Questions
# ---------------------------------------------------------

@pytest.fixture
def indexing_question() -> QuestionObject:
    return QuestionObject(
        id="q_test_idx_01",
        text="How does database indexing using B-Trees improve query performance, and what are the trade-offs?",
        stage="role_technical",
        competency="database",
        difficulty=3,
        expectedConcepts=["database indexing", "b-tree", "avoid full scan"],
        relevanceScore=90,
        rubric=RubricCriteria(
            poor="Cannot explain how an index works or confuses it with a cache.",
            acceptable="Explains tree structure, faster lookups, and mentions write overhead.",
            excellent="Deep explanation of balanced search tree, logarithmic disk lookups, leaf node scans, and write amplification."
        ),
        sources=["chunk_fund_db_01"]
    )


@pytest.fixture
def jwt_question() -> QuestionObject:
    return QuestionObject(
        id="q_test_jwt_01",
        text="How does JWT-based stateless authentication work and how do you handle token revocation?",
        stage="role_technical",
        competency="backend",
        difficulty=3,
        expectedConcepts=["jwt", "stateless auth", "token revocation"],
        relevanceScore=90,
        rubric=RubricCriteria(
            poor="Does not understand JWT signature or claims.",
            acceptable="Explains signed payload and token verification without database lookup.",
            excellent="Covers header/payload/signature, cryptographic verification, short TTLs, and blacklist/Redis revocation."
        ),
        sources=["chunk_tech_jwt_01"]
    )


@pytest.fixture
def caching_question() -> QuestionObject:
    return QuestionObject(
        id="q_test_cache_01",
        text="What is in-memory caching and how does it prevent database overload?",
        stage="fundamentals",
        competency="backend",
        difficulty=2,
        expectedConcepts=["in-memory caching", "redis", "bypass disk"],
        relevanceScore=90,
        rubric=RubricCriteria(
            poor="Cannot define cache or explains it incorrectly.",
            acceptable="Explains storing hot data in RAM to reduce database query load.",
            excellent="Detailed analysis of volatile memory speed, cache-aside pattern, TTLs, and database offloading."
        ),
        sources=["chunk_tech_redis_01"]
    )


@pytest.fixture
def evaluator() -> DeterministicAnswerEvaluator:
    return DeterministicAnswerEvaluator()


# ---------------------------------------------------------
# 10 Golden Evaluation Category Tests
# ---------------------------------------------------------

class TestGoldenAnswerEvaluation:
    """Verifies all 10 semantic grading categories mandated by Master Mission."""

    def test_01_exact_correct_answer(self, indexing_question, evaluator):
        """Exact correct answer containing standard terminology scores high."""
        answer = (
            "Database indexing uses a B-Tree structure to avoid full scan of tables. "
            "It organizes keys in a balanced tree on disk, allowing logarithmic search time "
            "for lookups while trading off write performance on inserts and updates."
        )
        res = evaluator.evaluate(indexing_question, answer)
        assert res.score >= 80, f"Expected >= 80, got {res.score}"
        assert "database indexing" in res.coveredConcepts
        assert res.technicalCorrectness == "accurate"
        assert res.isFallback is True

    def test_02_correct_semantic_paraphrase(self, indexing_question, evaluator):
        """
        CRITICAL TEST: A semantically correct paraphrase MUST NOT score
        substantially lower merely because it avoids exact keyword literals.
        """
        # Does not say "database indexing" or "full scan", uses descriptive synonyms
        answer = (
            "The system creates an ordered hierarchical search tree on column values. "
            "Instead of scanning every row in the storage block, the engine traverses tree levels "
            "directly to row pointers, locating records efficiently."
        )
        res = evaluator.evaluate(indexing_question, answer)
        # Paraphrase score should be solid (>= 70) and recognize the concept
        assert res.score >= 70, f"Semantic paraphrase scored too low ({res.score}), penalizing non-literal phrasing!"
        assert len(res.coveredConcepts) >= 1, "Failed to identify underlying demonstrated concept"
        assert res.technicalCorrectness in ("accurate", "partially_accurate")

    def test_03_partial_answer(self, indexing_question, evaluator):
        """Partial answer receives proportional credit with identified gaps."""
        answer = "An index uses a balanced tree to make lookups fast."
        res = evaluator.evaluate(indexing_question, answer)
        assert 45 <= res.score <= 75, f"Partial score out of expected range: {res.score}"
        assert len(res.coveredConcepts) >= 1
        assert len(res.missingConcepts) >= 1
        assert res.completeness == "partial"

    def test_04_keyword_stuffing_without_reasoning(self, indexing_question, evaluator):
        """
        CRITICAL TEST: Buzzword dropping without explanatory grammar
        MUST NOT achieve high scores.
        """
        answer = "B-tree database indexing avoid full scan index cache redis sql acid token"
        res = evaluator.evaluate(indexing_question, answer)
        assert res.score <= 35, f"Keyword-stuffed answer scored dangerously high ({res.score})!"
        assert res.technicalCorrectness == "inaccurate"
        assert "stuffing" in res.reasoning.lower() or "keyword" in res.reasoning.lower()

    def test_05_incorrect_answer(self, indexing_question, evaluator):
        """Factually wrong technical answer receives low score and inaccurate rating."""
        answer = "Database indexing compresses PNG images and uploads them to a WebSocket server for video streaming."
        res = evaluator.evaluate(indexing_question, answer)
        assert res.score <= 35
        assert res.technicalCorrectness == "inaccurate"
        assert len(res.missingConcepts) == len(indexing_question.expectedConcepts)

    def test_06_off_topic_answer(self, indexing_question, evaluator):
        """Off-topic answer receives minimal score and off_topic relevance."""
        answer = "My favorite recipe is Italian carbonara pasta with farm fresh eggs, pecorino cheese, and cured guanciale."
        res = evaluator.evaluate(indexing_question, answer)
        assert res.score <= 20
        assert res.relevance == "off_topic"
        assert res.technicalCorrectness == "inaccurate"

    def test_07_deep_and_excellent_answer(self, indexing_question, evaluator):
        """Comprehensive answer detailing mechanics and trade-offs gets top marks."""
        answer = (
            "Database indexing creates balanced multi-way B+Tree structures stored on disk. "
            "Internal nodes store search keys and page pointers, while leaf nodes form a doubly-linked list "
            "enabling both O(log N) point queries and fast sequential range scans, which avoids full table scan. "
            "The primary trade-offs are write amplification because every insert or delete requires page splits "
            "and rebalancing, along with significant additional disk storage overhead for large tables."
        )
        res = evaluator.evaluate(indexing_question, answer)
        assert res.score >= 88
        assert res.depth == "deep"
        assert res.completeness == "complete"
        assert res.technicalCorrectness == "accurate"
        assert not res.missingConcepts

    def test_08_shallow_but_technically_correct_answer(self, indexing_question, evaluator):
        """Brief but accurate answer receives passing mark with shallow depth."""
        answer = "It is an ordered tree structure that lets the database find rows without reading every record."
        res = evaluator.evaluate(indexing_question, answer)
        assert 60 <= res.score <= 85
        assert res.depth in ("shallow", "adequate")
        assert res.technicalCorrectness in ("accurate", "partially_accurate")

    def test_09_contradictory_nonsense_answer(self, indexing_question, evaluator):
        """Answers claiming established patterns are bad/nonsense are rejected."""
        answer = "Database indexes are totally useless nonsense, they make queries 100x slower and corrupt all your data."
        res = evaluator.evaluate(indexing_question, answer)
        assert res.score <= 25
        assert res.technicalCorrectness == "inaccurate"

    def test_10_empty_and_refusal_answers(self, indexing_question, evaluator):
        """Empty answers and explicit refusals are graded strictly."""
        # Empty string
        res_empty = evaluator.evaluate(indexing_question, "")
        assert res_empty.score <= 15
        assert res_empty.completeness == "minimal"

        # Explicit refusal
        res_refusal = evaluator.evaluate(indexing_question, "I don't know, pass.")
        assert res_refusal.score <= 15
        assert res_refusal.completeness == "minimal"
        assert len(res_refusal.missingConcepts) == len(indexing_question.expectedConcepts)


# ---------------------------------------------------------
# Multiple Concept Domain Golden Tests
# ---------------------------------------------------------

class TestMultiDomainEvaluation:
    """Verifies semantic evaluation across caching and authentication domains."""

    def test_caching_paraphrase_and_exact(self, caching_question, evaluator):
        # Semantic paraphrase
        answer_paraphrase = (
            "We keep frequently requested query answers in volatile system RAM using a fast key-value store, "
            "so the backend does not have to read slow persistent disks on every HTTP call."
        )
        res_para = evaluator.evaluate(caching_question, answer_paraphrase)
        assert res_para.score >= 70, f"Caching paraphrase scored too low: {res_para.score}"
        assert len(res_para.coveredConcepts) >= 1

    def test_jwt_evaluation(self, jwt_question, evaluator):
        # Good answer
        answer = (
            "JSON Web Tokens provide stateless authentication because the user claims are cryptographically signed "
            "by the server using HMAC or RSA. The server verifies the signature without checking a database. "
            "For token revocation before expiry, you can maintain a Redis blacklist of revoked JTI IDs or use short TTLs."
        )
        res = evaluator.evaluate(jwt_question, answer)
        assert res.score >= 80
        assert "jwt" in res.coveredConcepts
        assert res.technicalCorrectness == "accurate"


# ---------------------------------------------------------
# Robustness, Adapter, & Gemini Fallback Tests
# ---------------------------------------------------------

class TestEvaluatorRobustnessAndContract:
    """Tests schema conformance, clamping, timeouts, and adapter behavior."""

    def test_gemini_evaluator_falls_back_when_no_api_key(self, indexing_question):
        """When GEMINI_API_KEY is unset, GeminiAnswerEvaluator delegates cleanly to fallback."""
        with patch("core.config.settings.GEMINI_API_KEY", ""):
            gemini_eval = GeminiAnswerEvaluator()
            res = gemini_eval.evaluate(indexing_question, "Database indexing uses a B-tree.")
            assert isinstance(res, EvaluationResult)
            assert res.isFallback is True

    def test_gemini_evaluator_malformed_json_recovery(self, indexing_question):
        """Malformed JSON with markdown fences is recovered via regex extraction."""
        fake_response = MagicMock()
        fake_response.text = """
        Here is the evaluation:
        ```json
        {
            "score": 85,
            "coveredConcepts": ["database indexing", "b-tree"],
            "missingConcepts": ["avoid full scan"],
            "confidence": 0.9,
            "reasoning": "Solid answer with good grasp of tree indexes.",
            "technicalCorrectness": "accurate",
            "completeness": "complete",
            "relevance": "directly_relevant",
            "depth": "adequate"
        }
        ```
        Hope this helps!
        """
        gemini_eval = GeminiAnswerEvaluator()
        parsed = gemini_eval._clean_and_parse_json(fake_response.text)
        assert parsed is not None
        assert parsed["score"] == 85
        assert "database indexing" in parsed["coveredConcepts"]

    def test_gemini_evaluator_handles_api_exception(self, indexing_question):
        """If Gemini API raises an exception (timeout, 500), it safely falls back."""
        with patch("core.config.settings.GEMINI_API_KEY", "fake_key_for_test"):
            gemini_eval = GeminiAnswerEvaluator()
            with patch.object(gemini_eval, "_evaluate_with_gemini", side_effect=RuntimeError("API Gateway Timeout")):
                res = gemini_eval.evaluate(indexing_question, "Database indexing uses a B-tree.")
                assert isinstance(res, EvaluationResult)
                assert res.isFallback is True

    def test_adapter_preserves_evaluation_boundary(self, indexing_question):
        """Adapter accepts dict or EvaluationResult and clamps bounds."""
        adapter = AnswerEvaluationAdapter()

        # 1. Test raw dict input with out-of-bounds score
        raw_dict = {
            "score": 150,  # Needs clamping to 100
            "coveredConcepts": ["b-tree"],
            "missingConcepts": [],
            "confidence": 1.8,  # Needs clamping to 1.0
            "reasoning": "External evaluation test"
        }
        res = adapter.process_evaluation(indexing_question, "ignored", incoming_evaluation=raw_dict)
        assert res.score == 100
        assert res.confidence == 1.0
        assert res.coveredConcepts == ["b-tree"]

        # 2. Test negative score clamping
        negative_dict = {
            "score": -20,
            "confidence": -0.5
        }
        res2 = adapter.process_evaluation(indexing_question, "ignored", incoming_evaluation=negative_dict)
        assert res2.score == 0
        assert res2.confidence == 0.0
