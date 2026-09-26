"""
Standalone RAG Evaluation Suite for BoardRoom AI.
Covers 20 core test cases evaluating retrieval, generation, relevance, and fault tolerance
without requiring external services or dependencies on other members.

Can be run directly:
    python tests/test_standalone_eval_suite.py
Or via pytest:
    pytest tests/test_standalone_eval_suite.py -v
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from core.schemas import CandidateProfile, TargetRole, QuestionObject
from rag.retriever import KnowledgeRetriever
from generator.pipeline import QuestionGeneratorPipeline
from evaluator.relevance import QuestionRelevanceEvaluator
from fastapi.testclient import TestClient
from main import app


# -------------------------------------------------------------
# Test Harness Helper
# -------------------------------------------------------------

def evaluate_case(case_num: int, name: str, check_fn) -> bool:
    """Runs a single test case, prints formatted PASS/FAIL with reason, and returns success boolean."""
    try:
        passed, reason = check_fn()
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] Case {case_num:02d}: {name} -> {reason}")
        return passed
    except Exception as e:
        print(f"[FAIL] Case {case_num:02d}: {name} -> Unhandled Exception: {str(e)}")
        return False


# -------------------------------------------------------------
# Individual Test Implementations
# -------------------------------------------------------------

class StandaloneRAGEvalSuite:
    def __init__(self):
        self.retriever = KnowledgeRetriever()
        self.generator = QuestionGeneratorPipeline(retriever=self.retriever)
        self.client = TestClient(app)
        self.role = TargetRole(
            id="backend_engineer",
            title="Backend / Full-Stack Software Engineer",
            required_skills=["Python", "SQL", "REST APIs", "System Design", "Git"]
        )
        self.candidate = CandidateProfile(
            name="Alex Mercer",
            skills=["Python", "FastAPI", "PostgreSQL", "Redis"],
            experience_years=3.0
        )

    # Case 1: Backend Authentication
    def test_case_01_backend_auth(self):
        res = self.retriever.retrieve(
            query="JWT access token and refresh token rotation with httpOnly cookies",
            competency="backend",
            top_k=2
        )
        passed = len(res.results) > 0 and any("jwt" in c.lower() for c in res.results[0].expected_concepts)
        return passed, f"Top chunk '{res.results[0].chunk_id}' matches JWT authentication concepts (score: {res.results[0].score})"

    # Case 2: REST APIs
    def test_case_02_rest_apis(self):
        res = self.retriever.retrieve(
            query="REST API statelessness HTTP verbs idempotency PUT POST DELETE",
            competency="backend",
            top_k=2
        )
        passed = len(res.results) > 0 and "chunk_fund_rest_01" in [r.chunk_id for r in res.results]
        return passed, f"Retrieved REST API fundamental chunk with idempotency guarantees (top: {res.results[0].chunk_id})"

    # Case 3: Database / Indexing
    def test_case_03_db_indexing(self):
        res = self.retriever.retrieve(
            query="B-Tree index lookup vs sequential table scan query planner",
            competency="database",
            top_k=2
        )
        passed = len(res.results) > 0 and res.results[0].chunk_id == "chunk_tech_idx_01"
        return passed, f"Ranked B-Tree indexing chunk #1 with score {res.results[0].score}"

    # Case 4: SQL Transactions
    def test_case_04_sql_transactions(self):
        res = self.retriever.retrieve(
            query="ACID transaction isolation levels MVCC Repeatable Read Serializable phantom reads",
            competency="database",
            top_k=2
        )
        passed = len(res.results) > 0 and any(r.chunk_id in ["chunk_deep_db_trans_01", "chunk_fund_db_01"] for r in res.results)
        return passed, f"Retrieved transaction isolation and MVCC chunk '{res.results[0].chunk_id}'"

    # Case 5: System Design
    def test_case_05_system_design(self):
        res = self.retriever.retrieve(
            query="CAP theorem PACELC consistency availability network partition",
            competency="system_design",
            top_k=2
        )
        passed = len(res.results) > 0 and "chunk_deep_cap_01" in [r.chunk_id for r in res.results]
        return passed, f"Retrieved CAP/PACELC distributed systems chunk '{res.results[0].chunk_id}'"

    # Case 6: Caching
    def test_case_06_caching(self):
        res = self.retriever.retrieve(
            query="Redis distributed cache-aside write-through cache stampede thundering herd TTL",
            competency="system_design",
            top_k=2
        )
        passed = len(res.results) > 0 and "chunk_tech_cache_01" in [r.chunk_id for r in res.results]
        return passed, f"Retrieved distributed caching chunk '{res.results[0].chunk_id}'"

    # Case 7: OS / Networking / CS Fundamentals
    def test_case_07_os_networking(self):
        res = self.retriever.retrieve(
            query="TCP 3-way handshake SYN ACK TIME_WAIT socket states ephemeral port exhaustion",
            competency="cs_fundamentals",
            top_k=2
        )
        passed = len(res.results) > 0 and "chunk_fund_net_01" in [r.chunk_id for r in res.results]
        return passed, f"Retrieved TCP handshake and TIME_WAIT chunk '{res.results[0].chunk_id}'"

    # Case 8: Semantic Paraphrase Retrieval
    def test_case_08_semantic_paraphrase(self):
        # Query intentionally avoids words "snowflake" or "idempotency key"
        res = self.retriever.retrieve(
            query="preventing duplicate credit card charges when client connection drops and retries with headers",
            competency="backend",
            top_k=2
        )
        passed = len(res.results) > 0 and res.results[0].chunk_id == "chunk_tech_idempotency_01"
        return passed, f"Correctly retrieved idempotency chunk '{res.results[0].chunk_id}' via semantic paraphrase (score: {res.results[0].score})"

    # Case 9: Metadata Filtering
    def test_case_09_metadata_filtering(self):
        res = self.retriever.retrieve(
            query="high volume queries",
            competency="database",
            top_k=3
        )
        passed = len(res.results) > 0 and all(r.competency == "database" for r in res.results)
        return passed, f"All {len(res.results)} returned chunks strictly conform to competency='database'"

    # Case 10: Stage Filtering
    def test_case_10_stage_filtering(self):
        res = self.retriever.retrieve(
            query="candidate technical experience and background",
            stage="ice_breaker",
            top_k=2
        )
        passed = len(res.results) > 0 and all(r.stage == "ice_breaker" for r in res.results)
        return passed, f"All returned chunks strictly conform to stage='ice_breaker'"

    # Case 11: Difficulty 1 vs 5 Calibration
    def test_case_11_difficulty_calibration(self):
        res_diff1 = self.retriever.retrieve(query="version control Git merge rebase", difficulty=1, top_k=1)
        res_diff5 = self.retriever.retrieve(query="distributed consensus Raft leader election", difficulty=5, top_k=1)
        d1 = res_diff1.results[0].difficulty_level if res_diff1.results else 0
        d5 = res_diff5.results[0].difficulty_level if res_diff5.results else 0
        passed = d1 <= 2 and d5 >= 4
        return passed, f"Diff 1 query returned level {d1} chunk; Diff 5 query returned level {d5} chunk"

    # Case 12: Previous-Question Deduplication
    def test_case_12_deduplication(self):
        q1 = self.generator.generate(
            candidate=self.candidate, role=self.role, stage="role_technical", competency="database", difficulty=3
        )
        q2 = self.generator.generate(
            candidate=self.candidate, role=self.role, stage="role_technical", competency="database", difficulty=3,
            previous_questions=[q1.text]
        )
        passed = q1.text != q2.text
        return passed, f"Successfully avoided duplicate question (Q1: '{q1.text[:40]}...' vs Q2: '{q2.text[:40]}...')"

    # Case 13: Missing-Concept Probing
    def test_case_13_missing_concept_probing(self):
        gap = "token revocation strategy"
        q = self.generator.generate(
            candidate=self.candidate, role=self.role, stage="deep_dive", competency="backend", difficulty=4,
            previous_missing_concepts=[gap]
        )
        text_lower = q.text.lower()
        passed = "token" in text_lower or "revocation" in text_lower or any(gap in c.lower() for c in q.expectedConcepts)
        return passed, f"Adaptive question successfully probed missed concept '{gap}'"

    # Case 14: Empty Retrieval Query Resilience
    def test_case_14_empty_retrieval(self):
        res = self.retriever.retrieve(query="     ", competency="backend", top_k=2)
        passed = len(res.results) > 0 and all(r.competency == "backend" for r in res.results)
        return passed, f"Whitespace query gracefully handled, returning {len(res.results)} candidate chunks"

    # Case 15: Invalid Input Pydantic Validation
    def test_case_15_invalid_input_validation(self):
        res = self.client.post("/api/ai/generate-question", json={
            "stage": "role_technical",
            "competency": "backend",
            "difficulty": 99  # Invalid > 5
        })
        passed = res.status_code == 422
        return passed, f"Invalid difficulty=99 properly rejected with HTTP 422 Unprocessable Entity"

    # Case 16: Malformed LLM Output Recovery
    def test_case_16_malformed_llm_recovery(self):
        mock_resp = MagicMock()
        mock_resp.text = "Here is a broken non-JSON response {bad: data... "
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_resp

        with patch("core.config.settings.GEMINI_API_KEY", "mock_key"), \
             patch("google.genai.Client", return_value=mock_client):
            q = self.generator.generate(
                candidate=self.candidate, role=self.role, stage="role_technical", competency="backend", difficulty=3
            )
            passed = q is not None and q.isFallback is True and len(q.text) > 10
            return passed, f"Malformed LLM JSON gracefully intercepted; triggered curated fallback (isFallback={q.isFallback})"

    # Case 17: Deterministic Fallback on LLM Failure
    def test_case_17_deterministic_fallback(self):
        with patch.object(self.generator, "_generate_with_gemini", side_effect=RuntimeError("LLM 503 Outage")):
            q = self.generator.generate(
                candidate=self.candidate, role=self.role, stage="fundamentals", competency="database", difficulty=2
            )
            passed = q is not None and q.isFallback is True and q.relevanceScore >= 70
            return passed, f"LLM exception gracefully degraded to curated question '{q.text[:45]}...' with score {q.relevanceScore}"

    # Case 18: QuestionObject Schema Validation (Frozen 10 Fields)
    def test_case_18_schema_validation(self):
        q = self.generator.generate(
            candidate=self.candidate, role=self.role, stage="role_technical", competency="system_design", difficulty=3
        )
        d = q.model_dump()
        frozen_fields = ["id", "text", "stage", "competency", "difficulty", "expectedConcepts", "rubric", "relevanceScore", "sources", "isFallback"]
        missing = [f for f in frozen_fields if f not in d]
        passed = len(missing) == 0 and len(d["expectedConcepts"]) >= 2 and isinstance(d["rubric"], dict)
        return passed, f"QuestionObject strictly contains all 10 frozen fields with complete rubric and {len(d['expectedConcepts'])} expected concepts"

    # Case 19: Source Citation Presence
    def test_case_19_source_citation(self):
        q = self.generator.generate(
            candidate=self.candidate, role=self.role, stage="deep_dive", competency="system_design", difficulty=4
        )
        passed = len(q.sources) >= 1 and all(isinstance(s, str) and len(s) > 0 for s in q.sources)
        return passed, f"Question verified with {len(q.sources)} grounding source citations: {q.sources}"

    # Case 20: Relevance Score Bounds & Explainability
    def test_case_20_relevance_score_bounds(self):
        q_strong = "How would you design a distributed caching layer using Redis with cache-aside and prevent cache stampede?"
        eval_strong = QuestionRelevanceEvaluator.evaluate(
            question_text=q_strong, role=self.role, candidate=self.candidate,
            competency="system_design", stage="role_technical", difficulty=3,
            expected_concepts=["cache-aside", "Redis", "cache stampede"]
        )
        q_offtopic = "What is the best way to bake sourdough bread with whole wheat flour in an oven?"
        eval_offtopic = QuestionRelevanceEvaluator.evaluate(
            question_text=q_offtopic, role=self.role, candidate=self.candidate,
            competency="system_design", stage="role_technical", difficulty=3
        )
        passed = eval_strong.totalScore >= 80 and eval_offtopic.totalScore <= 45 and (0 <= eval_strong.totalScore <= 100)
        return passed, f"Strong technical question scored {eval_strong.totalScore}/100; off-topic baking question scored {eval_offtopic.totalScore}/100"


# -------------------------------------------------------------
# Standalone CLI Runner
# -------------------------------------------------------------

def run_standalone_evaluation() -> bool:
    print("=" * 75)
    print("      BOARDROOM AI — STANDALONE RAG EVALUATION SUITE (20 CASES)")
    print("=" * 75)

    suite = StandaloneRAGEvalSuite()

    test_cases = [
        (1, "Backend Authentication", suite.test_case_01_backend_auth),
        (2, "REST APIs & Idempotency", suite.test_case_02_rest_apis),
        (3, "Database / B-Tree Indexing", suite.test_case_03_db_indexing),
        (4, "SQL Transactions & Isolation", suite.test_case_04_sql_transactions),
        (5, "System Design & CAP Theorem", suite.test_case_05_system_design),
        (6, "Distributed Caching Strategies", suite.test_case_06_caching),
        (7, "OS / Networking Fundamentals", suite.test_case_07_os_networking),
        (8, "Semantic Paraphrase Retrieval", suite.test_case_08_semantic_paraphrase),
        (9, "Metadata Filtering Isolation", suite.test_case_09_metadata_filtering),
        (10, "Stage Filtering Alignment", suite.test_case_10_stage_filtering),
        (11, "Difficulty Calibration (1 vs 5)", suite.test_case_11_difficulty_calibration),
        (12, "Previous-Question Deduplication", suite.test_case_12_deduplication),
        (13, "Missing-Concept Probing", suite.test_case_13_missing_concept_probing),
        (14, "Empty Retrieval Query Resilience", suite.test_case_14_empty_retrieval),
        (15, "Invalid Input Rejection (HTTP 422)", suite.test_case_15_invalid_input_validation),
        (16, "Malformed LLM Output Recovery", suite.test_case_16_malformed_llm_recovery),
        (17, "Deterministic Fallback on Outage", suite.test_case_17_deterministic_fallback),
        (18, "Frozen QuestionObject Schema (10 Fields)", suite.test_case_18_schema_validation),
        (19, "Source Citation Presence", suite.test_case_19_source_citation),
        (20, "Relevance Score Bounds & Explainability", suite.test_case_20_relevance_score_bounds),
    ]

    passed_count = 0
    total_count = len(test_cases)

    for num, name, fn in test_cases:
        if evaluate_case(num, name, fn):
            passed_count += 1

    failed_count = total_count - passed_count
    print("=" * 75)
    print(f"EVALUATION SUMMARY: {passed_count}/{total_count} PASSED ({passed_count/total_count:.1%}) | {failed_count} FAILED")
    print("=" * 75)

    return failed_count == 0


# -------------------------------------------------------------
# Pytest Integration Bindings
# -------------------------------------------------------------

@pytest.fixture(scope="module")
def suite_instance():
    return StandaloneRAGEvalSuite()

def test_01_backend_auth(suite_instance):
    passed, reason = suite_instance.test_case_01_backend_auth()
    assert passed, reason

def test_02_rest_apis(suite_instance):
    passed, reason = suite_instance.test_case_02_rest_apis()
    assert passed, reason

def test_03_db_indexing(suite_instance):
    passed, reason = suite_instance.test_case_03_db_indexing()
    assert passed, reason

def test_04_sql_transactions(suite_instance):
    passed, reason = suite_instance.test_case_04_sql_transactions()
    assert passed, reason

def test_05_system_design(suite_instance):
    passed, reason = suite_instance.test_case_05_system_design()
    assert passed, reason

def test_06_caching(suite_instance):
    passed, reason = suite_instance.test_case_06_caching()
    assert passed, reason

def test_07_os_networking(suite_instance):
    passed, reason = suite_instance.test_case_07_os_networking()
    assert passed, reason

def test_08_semantic_paraphrase(suite_instance):
    passed, reason = suite_instance.test_case_08_semantic_paraphrase()
    assert passed, reason

def test_09_metadata_filtering(suite_instance):
    passed, reason = suite_instance.test_case_09_metadata_filtering()
    assert passed, reason

def test_10_stage_filtering(suite_instance):
    passed, reason = suite_instance.test_case_10_stage_filtering()
    assert passed, reason

def test_11_difficulty_calibration(suite_instance):
    passed, reason = suite_instance.test_case_11_difficulty_calibration()
    assert passed, reason

def test_12_deduplication(suite_instance):
    passed, reason = suite_instance.test_case_12_deduplication()
    assert passed, reason

def test_13_missing_concept_probing(suite_instance):
    passed, reason = suite_instance.test_case_13_missing_concept_probing()
    assert passed, reason

def test_14_empty_retrieval(suite_instance):
    passed, reason = suite_instance.test_case_14_empty_retrieval()
    assert passed, reason

def test_15_invalid_input_validation(suite_instance):
    passed, reason = suite_instance.test_case_15_invalid_input_validation()
    assert passed, reason

def test_16_malformed_llm_recovery(suite_instance):
    passed, reason = suite_instance.test_case_16_malformed_llm_recovery()
    assert passed, reason

def test_17_deterministic_fallback(suite_instance):
    passed, reason = suite_instance.test_case_17_deterministic_fallback()
    assert passed, reason

def test_18_schema_validation(suite_instance):
    passed, reason = suite_instance.test_case_18_schema_validation()
    assert passed, reason

def test_19_source_citation(suite_instance):
    passed, reason = suite_instance.test_case_19_source_citation()
    assert passed, reason

def test_20_relevance_score_bounds(suite_instance):
    passed, reason = suite_instance.test_case_20_relevance_score_bounds()
    assert passed, reason


if __name__ == "__main__":
    success = run_standalone_evaluation()
    sys.exit(0 if success else 1)
