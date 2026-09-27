"""
Contract tests for the answer-evaluation endpoints.

These protect the backend and frontend from silent drift: if a response field is
renamed, this suite fails instead of the demo.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))

pytest.importorskip("fastapi")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from api.evaluation_routes import router  # noqa: E402

FROZEN_CORE = {"score", "coveredConcepts", "missingConcepts", "reasoning", "confidence"}
ADDITIVE = {
    "subScores", "partialConcepts", "conceptDetail", "scoreBreakdown",
    "flags", "evaluationMode", "strategyHint",
}
SUBSCORES = {
    "relevance", "technicalCorrectness", "completeness", "reasoning", "clarity",
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


VALID = {
    "questionId": "q_db_01",
    "questionText": "What is a SQL index and when does it hurt performance?",
    "answerText": (
        "An index lets the engine do a B-tree lookup instead of a full table "
        "scan, but each write must maintain the index, so write overhead grows."
    ),
    "expectedConcepts": ["index lookup", "full table scan", "write overhead"],
    "stage": "fundamentals",
    "competency": "database",
    "difficulty": 2,
}


def test_response_contract_is_frozen(client):
    body = client.post("/api/ai/evaluate-answer", json=VALID).json()
    missing = (FROZEN_CORE | ADDITIVE) - set(body)
    assert not missing, f"contract drift, missing: {missing}"
    assert set(body["subScores"]) == SUBSCORES


def test_always_200_for_a_valid_body(client):
    for answer in ["", "x", "I don't know.", VALID["answerText"] * 8]:
        r = client.post("/api/ai/evaluate-answer", json=dict(VALID, answerText=answer))
        assert r.status_code == 200, (answer[:20], r.status_code)
        assert 0 <= r.json()["score"] <= 100


def test_422_on_a_malformed_body(client):
    assert client.post(
        "/api/ai/evaluate-answer", json=dict(VALID, difficulty=99)
    ).status_code == 422


def test_accepts_a_full_question_object(client):
    """A QuestionObject from /ai/generate-question passes straight through."""
    payload = {
        "question": {
            "id": "q_auth_01",
            "text": "How do you handle JWT revocation on logout?",
            "stage": "role_technical",
            "competency": "backend",
            "difficulty": 3,
            "expectedConcepts": ["revocation strategy", "denylist"],
            "rubric": {"poor": "p", "acceptable": "a", "excellent": "e"},
            "relevanceScore": 88,
        },
        "answerText": (
            "Because JWTs are stateless I keep a denylist of token IDs in Redis "
            "with a TTL matching the token lifetime, which is my revocation "
            "strategy on logout."
        ),
    }
    body = client.post("/api/ai/evaluate-answer", json=payload).json()
    assert body["coveredConcepts"], body
    assert body["score"] > 50, body["score"]


def test_batch_endpoint_preserves_order_and_shape(client):
    r = client.post("/api/ai/evaluate-answers", json={"items": [
        dict(VALID, questionId="a"),
        dict(VALID, questionId="b", answerText="Index is faster."),
    ]})
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    assert items[0]["score"] > items[1]["score"]
    assert "insufficient_length" in items[1]["flags"]


def test_health_reports_mode_without_leaking_the_key(client):
    body = client.get("/api/ai/evaluation-health").json()
    assert body["scoringMode"] in ("deterministic", "llm_assisted")
    assert isinstance(body["llmConfigured"], bool)
    assert "not a hiring decision" in body["disclaimer"]
    blob = str(body).lower()
    for leak in ("aiza", "sk-", "api_key="):
        assert leak not in blob, "health must not echo a key"


def test_evaluation_router_is_mounted_in_the_app():
    """main.py must actually include the router -- not just define it."""
    import main  # noqa: PLC0415

    paths = {
        route.path
        for route in main.app.routes
        if getattr(route, "path", None)
    }
    # Some Starlette versions expose included routers as wrappers rather than
    # flattened routes, so fall back to the OpenAPI schema, which is what a
    # caller actually sees.
    if "/api/ai/evaluate-answer" not in paths:
        paths = set(main.app.openapi()["paths"])
    assert "/api/ai/evaluate-answer" in paths, sorted(paths)
    assert "/api/ai/evaluation-health" in paths, sorted(paths)
