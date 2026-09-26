"""
Comprehensive Golden Test Suite for BoardRoom AI RAG & Question Generation Subsystem.
Covers all scenarios required by Hackathon Master Plan Phase 7, Section 15.1,
and Post-Audit Priorities 1, 3, 4, 5, 6, 7.
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from core.schemas import (
    CandidateProfile,
    TargetRole,
    QuestionObject,
    KnowledgeChunk,
    AdaptiveContextRequest
)
from core.config import settings
from rag.retriever import KnowledgeRetriever
from evaluator.relevance import QuestionRelevanceEvaluator
from generator.pipeline import QuestionGeneratorPipeline
from adaptive.strategy import AdaptiveInterviewEngine
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(scope="module")
def retriever():
    return KnowledgeRetriever()


@pytest.fixture(scope="module")
def generator(retriever):
    return QuestionGeneratorPipeline(retriever=retriever)


@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)


# -------------------------------------------------------------
# 1. Knowledge Base & Ingestion Schema Tests (Priority 2)
# -------------------------------------------------------------

def test_all_seed_knowledge_chunks_valid():
    """Verifies that all chunks in seed_knowledge.json conform to KnowledgeChunk schema."""
    kb_path = ROOT_DIR / "data" / "knowledge_base" / "seed_knowledge.json"
    assert kb_path.exists(), "Knowledge base file missing"

    with open(kb_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) >= 35, f"Expected 35-45 chunks for post-audit, got {len(data)}"
    for item in data:
        chunk = KnowledgeChunk(**item)
        assert chunk.id.startswith("chunk_")
        assert chunk.difficulty_level in [1, 2, 3, 4, 5]
        assert len(chunk.expected_concepts) >= 3
        assert len(chunk.sample_questions) >= 1
        assert chunk.rubric.poor
        assert chunk.rubric.acceptable
        assert chunk.rubric.excellent


# -------------------------------------------------------------
# 2. Retrieval Engine & Insufficient Context Tests (Priority 1)
# -------------------------------------------------------------

def test_retrieval_exact_metadata_and_ranking(retriever):
    """Tests exact metadata filtering and vector ranking."""
    res = retriever.retrieve(
        query="JWT access tokens and refresh token rotation with cookies",
        role_id="backend_engineer",
        competency="backend",
        stage="role_technical",
        difficulty=3,
        top_k=2
    )
    assert res.total_found > 0
    top = res.results[0]
    assert top.competency == "backend"
    assert top.difficulty_level == 3
    assert any("jwt" in c.lower() for c in top.expected_concepts)


def test_insufficient_retrieved_context_graceful_relaxation(retriever):
    """Tests that retriever gracefully relaxes strict constraints instead of returning 0 chunks."""
    res = retriever.retrieve(
        query="scalable distributed microservices",
        role_id="backend_engineer",
        competency="system_design",
        stage="ice_breaker",
        difficulty=5,
        top_k=2
    )
    assert res.total_found > 0
    assert any("system_design" in r.competency for r in res.results)


# -------------------------------------------------------------
# 3. Question Relevance Golden Tests (Phase 4 / Priority 6)
# -------------------------------------------------------------

def test_strong_question_relevance():
    """A well-targeted question matching candidate, role, and competency earns a high score (>= 80)."""
    cand = CandidateProfile(skills=["Python", "FastAPI", "PostgreSQL"], experience_years=3.0)
    role = TargetRole()
    q = "How would you design a secure token-based authentication system using JWTs, and how do you handle token revocation when a user logs out?"

    breakdown = QuestionRelevanceEvaluator.evaluate(
        question_text=q,
        role=role,
        candidate=cand,
        competency="backend",
        stage="role_technical",
        difficulty=3,
        expected_concepts=["JWT structure", "refresh token", "revocation strategy"]
    )
    assert breakdown.totalScore >= 80, f"Expected score >= 80, got {breakdown.totalScore}"
    assert breakdown.roleAlignment >= 80
    assert breakdown.targetCompetencyAlignment >= 85


def test_irrelevant_question_relevance():
    """A completely non-technical, irrelevant question is heavily penalized (<= 45)."""
    cand = CandidateProfile(skills=["Python", "PostgreSQL"], experience_years=3.0)
    role = TargetRole()
    q = "What is the best technique to knead pizza dough to get a crispy crust?"

    breakdown = QuestionRelevanceEvaluator.evaluate(
        question_text=q,
        role=role,
        candidate=cand,
        competency="backend",
        stage="role_technical",
        difficulty=3
    )
    assert breakdown.totalScore <= 45, f"Expected score <= 45 for baking question, got {breakdown.totalScore}"
    assert breakdown.roleAlignment <= 20
    assert breakdown.candidateExpertiseAlignment <= 20


def test_wrong_competency_penalized():
    """Asking a database B-tree indexing question under 'scenario_managerial' competency is penalized."""
    cand = CandidateProfile(skills=["Python", "SQL"], experience_years=3.0)
    role = TargetRole()
    q = "What is the difference between an SQL index lookup and a full table scan in terms of B-Tree traversal?"

    breakdown = QuestionRelevanceEvaluator.evaluate(
        question_text=q,
        role=role,
        candidate=cand,
        competency="scenario_managerial",
        stage="scenario_managerial",
        difficulty=4
    )
    assert breakdown.targetCompetencyAlignment <= 50, f"Expected competency score <= 50, got {breakdown.targetCompetencyAlignment}"


def test_wrong_difficulty_penalized():
    """Asking a difficulty 5 architectural question in an 'ice_breaker' stage is penalized."""
    cand = CandidateProfile(skills=["Python"], experience_years=1.0)
    role = TargetRole()
    q = "Explain the exact Raft consensus leader election protocol and network split split-brain resolution?"

    breakdown = QuestionRelevanceEvaluator.evaluate(
        question_text=q,
        role=role,
        candidate=cand,
        competency="cs_fundamentals",
        stage="ice_breaker",
        difficulty=5
    )
    assert breakdown.difficultyAppropriateness <= 40, f"Expected difficulty score <= 40, got {breakdown.difficultyAppropriateness}"


# -------------------------------------------------------------
# 4. LLM Real Path & Failure Fallback Tests (Priority 3)
# -------------------------------------------------------------

def test_successful_llm_path_verified(generator):
    """
    Explicitly tests the LLM generation path without falling back.
    Mocks the Gemini client to return valid structured JSON, asserting isFallback is False.
    """
    cand = CandidateProfile(skills=["Python", "Redis", "PostgreSQL"], experience_years=3.0)
    role = TargetRole()

    mock_llm_payload = json.dumps({
        "question": "How would you implement an idempotency key mechanism using Redis distributed locks to prevent duplicate payment processing?",
        "expectedConcepts": ["Idempotency-Key header", "Redis distributed lock", "cached response replay", "unique constraints"],
        "rubric": {
            "poor": "Fails to explain idempotency or lock mechanisms.",
            "acceptable": "Explains checking request keys in Redis before processing.",
            "excellent": "Covers lock leases, TTL expiration, in-flight request status, and response caching."
        },
        "relevanceRationale": "Directly probes payment idempotency matching candidate backend skills and difficulty 3."
    })

    # Mock the Gemini client call
    mock_response = MagicMock()
    mock_response.text = mock_llm_payload

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch.object(settings, "GEMINI_API_KEY", "test_mock_key"), \
         patch("google.genai.Client", return_value=mock_client):

        q = generator.generate(
            candidate=cand,
            role=role,
            stage="role_technical",
            competency="backend",
            difficulty=3
        )

        # MUST NOT be fallback
        assert q.isFallback is False, "LLM path was expected, but fallback was triggered!"
        assert "idempotency key" in q.text.lower()
        assert q.stage == "role_technical"
        assert q.competency == "backend"
        assert q.difficulty == 3
        assert len(q.expectedConcepts) >= 3
        assert q.relevanceScore >= 80
        assert len(q.sources) > 0

        # Audit quality
        quality = QuestionGeneratorPipeline.validate_question_quality(q, "role_technical", "backend", 3)
        assert quality["is_valid"] is True, f"Quality issues: {quality['issues']}"


def test_real_gemini_api_when_key_present(generator):
    """
    Performs real live API call to Gemini when GEMINI_API_KEY is configured in the environment.
    If key is not present, skips gracefully.
    """
    if not settings.GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY not configured in environment. Skipping live Gemini test.")

    cand = CandidateProfile(skills=["Python", "PostgreSQL", "FastAPI"], experience_years=3.0)
    role = TargetRole()

    q = generator.generate(
        candidate=cand,
        role=role,
        stage="role_technical",
        competency="database",
        difficulty=3
    )

    assert q is not None
    assert q.isFallback is False, "Live Gemini call failed and reverted to fallback!"
    assert q.relevanceScore >= 75
    assert len(q.expectedConcepts) > 0
    assert q.sources


def test_llm_api_failure_fallback_trigger(generator):
    """Tests that an exception during Gemini call seamlessly degrades to curated fallback."""
    cand = CandidateProfile(skills=["Python", "FastAPI"], experience_years=2.0)
    role = TargetRole()

    with patch.object(generator, "_generate_with_gemini", side_effect=RuntimeError("Simulated LLM API 500 error")):
        q = generator.generate(
            candidate=cand,
            role=role,
            stage="fundamentals",
            competency="backend",
            difficulty=2
        )
        assert q is not None
        assert q.isFallback is True
        assert len(q.expectedConcepts) > 0
        assert q.relevanceScore >= 75
        assert q.sources


def test_malformed_llm_json_handling(generator):
    """Tests that malformed or non-JSON LLM output triggers fallback rather than crashing."""
    malformed_raw = "Here is your question: What is REST? Note: it is good! {broken json"
    parsed = generator._clean_and_parse_json(malformed_raw)
    assert parsed is None, "Should have failed parsing cleanly and returned None"


# -------------------------------------------------------------
# 5. Question Quality & Deduplication (Priority 4 & 6)
# -------------------------------------------------------------

def test_rag_output_contract_fields(generator):
    """Verifies that QuestionObject strictly matches the frozen team contract."""
    cand = CandidateProfile(skills=["Python", "PostgreSQL"], experience_years=2.0)
    role = TargetRole()

    q = generator.generate(
        candidate=cand,
        role=role,
        stage="role_technical",
        competency="database",
        difficulty=3
    )

    # Required contract fields from Priority 4
    data = q.model_dump()
    expected_fields = [
        "id", "text", "stage", "competency", "difficulty",
        "expectedConcepts", "rubric", "relevanceScore", "sources", "isFallback"
    ]
    for field in expected_fields:
        assert field in data, f"Missing required contract field: {field}"

    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0, "Sources must identify retrieved knowledge"
    assert isinstance(data["expectedConcepts"], list)
    assert isinstance(data["rubric"], dict)
    assert "poor" in data["rubric"] and "acceptable" in data["rubric"] and "excellent" in data["rubric"]


def test_question_generation_deduplication(generator):
    """Verifies that the generator does not repeat questions listed in previous_questions."""
    cand = CandidateProfile(skills=["Python", "SQL"], experience_years=2.0)
    role = TargetRole()

    q1 = generator.generate(
        candidate=cand,
        role=role,
        stage="role_technical",
        competency="database",
        difficulty=3
    )

    q2 = generator.generate(
        candidate=cand,
        role=role,
        stage="role_technical",
        competency="database",
        difficulty=3,
        previous_questions=[q1.text]
    )

    assert q1.text != q2.text, "Duplicate question was returned"
    assert q2.relevanceScore >= 75


def test_adaptive_probing_missing_concepts(generator):
    """Verifies that missing concepts from previous evaluation are incorporated into the next question."""
    cand = CandidateProfile(skills=["Python", "REST APIs"], experience_years=2.0)
    role = TargetRole()

    q = generator.generate(
        candidate=cand,
        role=role,
        stage="deep_dive",
        competency="backend",
        difficulty=4,
        previous_missing_concepts=["refresh token rotation", "revocation"]
    )

    text_lower = q.text.lower()
    assert "token" in text_lower or "refresh" in text_lower or "revocation" in text_lower
    assert q.relevanceScore >= 80


# -------------------------------------------------------------
# 6. End-to-End API Integration Tests
# -------------------------------------------------------------

def test_api_health(test_client):
    res = test_client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["chunks_indexed"] >= 35


def test_api_generate_and_evaluate_flow(test_client):
    """End-to-end integration: generate a question then evaluate its relevance via API."""
    gen_res = test_client.post("/api/ai/generate-question", json={
        "candidate": {
            "name": "Jane Candidate",
            "skills": ["Python", "SQL", "Docker"],
            "experience_years": 3.0
        },
        "role": {
            "id": "backend_engineer",
            "title": "Backend Software Engineer"
        },
        "stage": "role_technical",
        "competency": "system_design",
        "difficulty": 3
    })
    assert gen_res.status_code == 200
    q_data = gen_res.json()
    assert "text" in q_data
    assert q_data["difficulty"] == 3
    assert q_data["relevanceScore"] >= 75

    eval_res = test_client.post("/api/ai/evaluate-question-relevance", json={
        "question_text": q_data["text"],
        "competency": "system_design",
        "stage": "role_technical",
        "difficulty": 3,
        "expected_concepts": q_data["expectedConcepts"]
    })
    assert eval_res.status_code == 200
    assert eval_res.json()["totalScore"] >= 75
