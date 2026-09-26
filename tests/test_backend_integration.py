"""
Backend Integration Test Suite for BoardRoom AI RAG & Question Generation Subsystem.
Simulates the exact HTTP requests sent by Member 2 (Node.js Backend) and Member 4 (Evaluation).
Verifies:
- Frozen 10-field API contract
- previousQuestions deduplication
- previousMissingConcepts adaptation
- Deterministic fallback on LLM failure
- Graceful recovery from malformed LLM JSON
- Pydantic input validation (HTTP 422)
- Empty query retrieval resilience
- Adaptive strategy handoff
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from fastapi.testclient import TestClient
from main import app
from core.config import settings

client = TestClient(app)

FROZEN_CONTRACT_FIELDS = [
    "id",
    "text",
    "stage",
    "competency",
    "difficulty",
    "expectedConcepts",
    "rubric",
    "relevanceScore",
    "sources",
    "isFallback"
]


# -----------------------------------------------------------------
# 1. Standard Backend Contract Validation
# -----------------------------------------------------------------

def test_backend_standard_generate_question_contract():
    """
    Simulates standard request from Node.js Express server to /api/ai/generate-question.
    Verifies that the response matches the frozen 10-field contract exactly.
    """
    payload = {
        "candidate": {
            "id": "cand_backend_01",
            "name": "Jordan Smith",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience_years": 3.0,
            "education": "B.S. in Computer Science"
        },
        "role": {
            "id": "backend_engineer",
            "title": "Backend / Full-Stack Software Engineer",
            "required_skills": ["Python", "SQL", "REST APIs", "System Design"]
        },
        "stage": "role_technical",
        "competency": "backend",
        "difficulty": 3,
        "previousQuestions": [],
        "previousMissingConcepts": []
    }

    res = client.post("/api/ai/generate-question", json=payload)
    assert res.status_code == 200, f"Expected 200 OK, got {res.status_code}: {res.text}"

    data = res.json()

    # 1. Check all 10 frozen contract fields
    for field in FROZEN_CONTRACT_FIELDS:
        assert field in data, f"Missing required frozen contract field: '{field}'"

    # 2. Field type and content assertions
    assert isinstance(data["id"], str) and data["id"].startswith("q_")
    assert isinstance(data["text"], str) and len(data["text"]) > 10 and data["text"].strip().endswith("?")
    assert data["stage"] == "role_technical"
    assert data["competency"] == "backend"
    assert data["difficulty"] == 3
    assert isinstance(data["expectedConcepts"], list) and len(data["expectedConcepts"]) >= 2
    assert all(isinstance(c, str) for c in data["expectedConcepts"])

    # 3. Rubric structure
    assert isinstance(data["rubric"], dict)
    for rubric_key in ["poor", "acceptable", "excellent"]:
        assert rubric_key in data["rubric"]
        assert isinstance(data["rubric"][rubric_key], str) and len(data["rubric"][rubric_key]) > 0

    # 4. Relevance score & sources
    assert isinstance(data["relevanceScore"], int)
    assert 0 <= data["relevanceScore"] <= 100
    assert data["relevanceScore"] >= 70, f"Question relevance unexpectedly low: {data['relevanceScore']}"
    assert isinstance(data["sources"], list) and len(data["sources"]) >= 1
    assert isinstance(data["isFallback"], bool)


# -----------------------------------------------------------------
# 2. Deduplication via previousQuestions
# -----------------------------------------------------------------

def test_backend_deduplication_via_previous_questions():
    """
    Verifies that passing previousQuestions ensures the next generated question is unique.
    """
    base_payload = {
        "candidate": {
            "name": "Taylor Candidate",
            "skills": ["Python", "SQL"],
            "experience_years": 2.5
        },
        "role": {
            "id": "backend_engineer",
            "title": "Backend Software Engineer"
        },
        "stage": "role_technical",
        "competency": "database",
        "difficulty": 3,
        "previousQuestions": []
    }

    # First request
    res1 = client.post("/api/ai/generate-question", json=base_payload)
    assert res1.status_code == 200
    q1_text = res1.json()["text"]

    # Second request with q1 in previousQuestions
    payload2 = dict(base_payload)
    payload2["previousQuestions"] = [q1_text]
    res2 = client.post("/api/ai/generate-question", json=payload2)
    assert res2.status_code == 200
    q2_text = res2.json()["text"]

    assert q1_text != q2_text, "Backend received duplicate question despite passing previousQuestions!"


# -----------------------------------------------------------------
# 3. Adaptive Probing via previousMissingConcepts
# -----------------------------------------------------------------

def test_backend_adaptive_missing_concepts():
    """
    Verifies that previousMissingConcepts are integrated into the question for adaptive follow-up.
    """
    payload = {
        "candidate": {
            "name": "Morgan Candidate",
            "skills": ["Python", "FastAPI"],
            "experience_years": 2.0
        },
        "role": {
            "id": "backend_engineer",
            "title": "Backend Software Engineer"
        },
        "stage": "deep_dive",
        "competency": "backend",
        "difficulty": 4,
        "previousQuestions": ["Explain JWT vs Sessions"],
        "previousMissingConcepts": ["refresh token rotation", "revocation"]
    }

    res = client.post("/api/ai/generate-question", json=payload)
    assert res.status_code == 200
    data = res.json()

    text_lower = data["text"].lower()
    concepts_lower = [c.lower() for c in data["expectedConcepts"]]

    # Must address missed concepts
    has_gap_in_text = any(term in text_lower for term in ["refresh", "token", "revocation"])
    has_gap_in_concepts = any(any(term in c for term in ["refresh", "token", "revocation"]) for c in concepts_lower)
    assert has_gap_in_text or has_gap_in_concepts, "Adaptive question failed to incorporate previousMissingConcepts"


# -----------------------------------------------------------------
# 4. Fallback Behavior & Malformed LLM Recovery
# -----------------------------------------------------------------

def test_backend_deterministic_fallback():
    """
    Verifies that when LLM key is omitted or LLM is offline,
    the endpoint returns 200 OK with isFallback=True.
    """
    payload = {
        "candidate": {"skills": ["Python"]},
        "role": {"id": "backend_engineer", "title": "Backend Engineer"},
        "stage": "fundamentals",
        "competency": "cs_fundamentals",
        "difficulty": 2
    }

    # Force fallback by mocking _generate_with_gemini to return None
    with patch("generator.pipeline.QuestionGeneratorPipeline._generate_with_gemini", return_value=None):
        res = client.post("/api/ai/generate-question", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["isFallback"] is True
        assert len(data["text"]) > 10
        assert data["relevanceScore"] >= 70
        assert len(data["sources"]) >= 1


def test_backend_malformed_llm_output_recovery():
    """
    Verifies that corrupted/non-JSON output from an LLM does not crash the endpoint
    or return 500 to the backend; it recovers cleanly to fallback.
    """
    payload = {
        "candidate": {"skills": ["Python", "FastAPI"]},
        "role": {"id": "backend_engineer", "title": "Backend Engineer"},
        "stage": "role_technical",
        "competency": "backend",
        "difficulty": 3
    }

    # Mock Gemini returning invalid broken JSON
    mock_resp = MagicMock()
    mock_resp.text = "This is not JSON: {question: broken... "

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    with patch.object(settings, "GEMINI_API_KEY", "mock_key"), \
         patch("google.genai.Client", return_value=mock_client):

        res = client.post("/api/ai/generate-question", json=payload)
        assert res.status_code == 200, f"Expected 200 with fallback, got {res.status_code}"
        data = res.json()
        assert data["isFallback"] is True
        assert len(data["text"]) > 10


# -----------------------------------------------------------------
# 5. Invalid Input Validation (FastAPI Pydantic Rejection)
# -----------------------------------------------------------------

def test_backend_invalid_input_rejection():
    """
    Verifies that malformed payloads from the backend are rejected with HTTP 422
    providing clear validation errors.
    """
    # 1. Invalid difficulty (difficulty must be 1 to 5)
    invalid_diff_payload = {
        "stage": "role_technical",
        "competency": "backend",
        "difficulty": 99  # Out of range!
    }
    res1 = client.post("/api/ai/generate-question", json=invalid_diff_payload)
    assert res1.status_code == 422
    err_detail = res1.json()["detail"]
    assert any("difficulty" in str(e["loc"]) for e in err_detail)

    # 2. Negative difficulty
    invalid_neg_payload = {
        "stage": "role_technical",
        "competency": "backend",
        "difficulty": -1
    }
    res2 = client.post("/api/ai/generate-question", json=invalid_neg_payload)
    assert res2.status_code == 422


# -----------------------------------------------------------------
# 6. Empty Retrieval Query Resilience
# -----------------------------------------------------------------

def test_backend_empty_retrieval_query():
    """
    Verifies that querying /api/rag/retrieve with empty whitespace returns 200 without crashing.
    """
    res = client.post("/api/rag/retrieve", json={
        "query": "   ",
        "competency": "database",
        "top_k": 2
    })
    assert res.status_code == 200
    data = res.json()
    assert data["total_found"] > 0
    assert len(data["results"]) > 0


# -----------------------------------------------------------------
# 7. Adaptive Handoff Validation (No Answer Evaluation)
# -----------------------------------------------------------------

def test_backend_adaptive_context_handoff():
    """
    Verifies that /api/ai/adaptive-context exposes:
    covered concepts, missing concepts, expected next strategy, next difficulty,
    and explicitly DOES NOT perform candidate answer scoring.
    """
    adaptive_payload = {
        "previousQuestions": ["Explain SQL index vs table scan"],
        "coveredConcepts": ["SQL index", "table scan"],
        "missingConcepts": ["B-Tree update overhead", "write amplification"],
        "currentDifficulty": 3,
        "lastScore": 55,
        "currentCompetency": "database",
        "currentStage": "role_technical"
    }

    res = client.post("/api/ai/adaptive-context", json=adaptive_payload)
    assert res.status_code == 200
    data = res.json()

    assert "next_stage" in data
    assert "next_competency" in data
    assert "next_difficulty" in data
    assert "strategy" in data
    assert "missing_concepts_to_probe" in data
    assert "rationale" in data

    # Verify strategy and missing concepts handoff
    assert data["strategy"] == "probe_missing_concept"
    assert len(data["missing_concepts_to_probe"]) > 0
    assert any("B-Tree" in c or "write" in c for c in data["missing_concepts_to_probe"])

    # Confirm that candidate answer evaluation keys are NOT in this response
    # (Member 4 owns answer evaluation)
    for forbidden in ["technicalCorrectness", "candidateScore", "completenessScore"]:
        assert forbidden not in data
