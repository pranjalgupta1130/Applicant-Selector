"""
Test Suite for Phase A — Interview Intelligence.
Verifies:
1. InterviewState & Concept-level Coverage Tracking (demonstrated vs partial vs missing)
2. Deterministic Adaptive Policy (difficulty escalation, de-escalation, gap probing)
3. Question Diversity and Quality Gates
4. 5 Standalone Simulated Interview Archetypes (Strong, Weak, Specialist with Gap, Resume-heavy, Outage Fallback)
"""

import sys
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from core.schemas import CandidateProfile, TargetRole, QuestionObject
from rag.retriever import KnowledgeRetriever
from generator.pipeline import QuestionGeneratorPipeline
from adaptive.state import InterviewState
from adaptive.policy import AdaptiveInterviewPolicy, PolicyDecision
from adaptive.simulator import InterviewSimulator, run_all_5_golden_simulations


@pytest.fixture(scope="module")
def retriever():
    return KnowledgeRetriever()


@pytest.fixture(scope="module")
def generator(retriever):
    return QuestionGeneratorPipeline(retriever=retriever)


# -------------------------------------------------------------
# 1. InterviewState & Concept Coverage Tracking Tests
# -------------------------------------------------------------

def test_interview_state_concept_tracking():
    """Verifies that InterviewState accurately categorizes demonstrated, partial, and missing knowledge."""
    state = InterviewState(candidate_id="cand_test", role_id="backend_engineer")

    # Turn 1: High score -> demonstrated
    state.record_turn(
        question_id="q1",
        question_text="Explain REST idempotency",
        question_type="conceptual",
        stage="fundamentals",
        competency="backend",
        difficulty=2,
        score=88,
        covered_concepts=["HTTP verbs", "idempotency"],
        missing_concepts=[]
    )
    assert "idempotency" in state.demonstrated_concepts
    assert "idempotency" in state.strong_concepts
    assert state.concept_map["idempotency"] == "demonstrated"

    # Turn 2: Low score with missing concepts -> missing / weak
    state.record_turn(
        question_id="q2",
        question_text="Explain B-Tree indexing update overhead",
        question_type="trade_off",
        stage="role_technical",
        competency="database",
        difficulty=3,
        score=45,
        covered_concepts=["B-Tree search"],
        missing_concepts=["write amplification", "index maintenance"]
    )
    assert "write amplification" in state.missing_concepts
    assert "write amplification" in state.weak_concepts
    assert state.concept_map["write amplification"] == "missing"

    # Turn 3: Adaptive turn resolving previous gap -> moves from missing to demonstrated
    state.record_turn(
        question_id="q3",
        question_text="Why does an index slow down writes?",
        question_type="follow_up",
        stage="role_technical",
        competency="database",
        difficulty=3,
        score=82,
        covered_concepts=["write amplification"],
        missing_concepts=[]
    )
    assert "write amplification" in state.demonstrated_concepts
    assert "write amplification" not in state.missing_concepts
    assert state.concept_map["write amplification"] == "demonstrated"

    summary = state.get_concept_coverage_summary()
    assert summary["demonstrated_count"] >= 2
    assert summary["total_concepts_tracked"] >= 3


# -------------------------------------------------------------
# 2. Deterministic Adaptive Policy Tests
# -------------------------------------------------------------

def test_policy_difficulty_escalation_on_high_score():
    """Policy escalates difficulty when candidate scores >= 82."""
    state = InterviewState(difficulty=2, current_stage="fundamentals", current_competency="backend")
    state.score_history.append(88)

    decision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.next_difficulty == 3, f"Expected difficulty escalated to 3, got {decision.next_difficulty}"
    assert "escalat" in decision.rationale.lower()


def test_policy_difficulty_deescalation_on_low_score():
    """Policy reduces difficulty when candidate scores < 50."""
    state = InterviewState(difficulty=4, current_stage="deep_dive", current_competency="system_design")
    state.score_history.append(42)

    decision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.next_difficulty == 3, f"Expected difficulty reduced to 3, got {decision.next_difficulty}"
    assert "reduc" in decision.rationale.lower()


def test_policy_gap_probing_triggers_follow_up():
    """Policy immediately triggers probe_missing_concept when unresolved gaps exist and score < 68."""
    state = InterviewState(difficulty=3, current_stage="role_technical", current_competency="backend")
    state.score_history.append(55)
    state.missing_concepts.append("token revocation")

    decision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.strategy == "probe_missing_concept"
    assert decision.recommended_question_type == "follow_up"
    assert "token revocation" in decision.target_concepts


def test_policy_stage_quota_advancement():
    """Policy advances to next stage when current stage quota is satisfied."""
    state = InterviewState(current_stage="ice_breaker", current_competency="ice_breaker", difficulty=1)
    state.previous_questions.append("Q1: Tell us about your background")
    state.stage_question_counts["ice_breaker"] = 1
    state.score_history.append(80)

    decision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.next_stage == "fundamentals"
    assert decision.strategy == "progress_stage"


# -------------------------------------------------------------
# 3. Question Diversity & Quality Gate Tests
# -------------------------------------------------------------

def test_question_diversity_and_internal_explanation(generator):
    """Verifies that generated questions contain questionType and questionExplanation."""
    cand = CandidateProfile(skills=["Python", "PostgreSQL"], experience_years=3.0)
    role = TargetRole()

    q = generator.generate(
        candidate=cand,
        role=role,
        stage="role_technical",
        competency="database",
        difficulty=3,
        question_type="trade_off",
        adaptive_reason="Testing database index trade-offs"
    )

    assert q.questionType == "trade_off"
    assert q.adaptiveReason is not None
    assert q.questionExplanation is not None
    assert "role_alignment" in q.questionExplanation
    assert "difficulty_rationale" in q.questionExplanation
    assert "targeted_concepts" in q.questionExplanation


def test_quality_gates_reject_invalid_and_fallback(generator):
    """Verifies quality gates detect invalid conditions and trigger fallback."""
    # Build an invalid mock question object
    q_invalid = QuestionObject(
        id="q_bad",
        text="As an AI, can you tell me a little bit about coding?",
        stage="role_technical",
        competency="backend",
        difficulty=3,
        expectedConcepts=["too_few"],  # < 2 concepts
        rubric={"poor": "", "acceptable": "", "excellent": ""},  # empty rubric
        relevanceScore=40,  # below threshold
        sources=[],  # missing sources
        isFallback=False
    )

    passed, issues = generator._check_quality_gates(
        question=q_invalid,
        stage="role_technical",
        competency="backend",
        difficulty=3,
        previous_questions=[]
    )
    assert passed is False
    assert len(issues) >= 3, f"Expected multiple gate failures, got {issues}"


# -------------------------------------------------------------
# 4. Standalone 5-Archetype Interview Simulations
# -------------------------------------------------------------

def test_simulations_all_5_archetypes():
    """
    Executes all 5 simulated interviews:
    1. Strong candidate -> escalates difficulty to 5, high scores
    2. Weak candidate -> difficulty stays at 1-2, gaps probed
    3. Backend specialist with system-design weakness -> gap probed on system design
    4. Resume-heavy candidate -> fundamental gaps probed
    5. LLM outage scenario -> all 6 turns execute via fallback without crash
    """
    results = run_all_5_golden_simulations()

    # 1. Strong Candidate Assertions
    strong = results["strong_candidate"]
    assert strong["turns_completed"] >= 5
    assert max(strong["difficulty_trend"]) == 5, f"Strong candidate should escalate to diff 5, got {strong['difficulty_trend']}"
    assert strong["concept_summary"]["demonstrated_count"] >= 5
    assert len(strong["concept_summary"]["missing"]) == 0

    # 2. Weak Candidate Assertions
    weak = results["weak_candidate"]
    assert weak["turns_completed"] >= 5
    assert max(weak["difficulty_trend"]) <= 2, f"Weak candidate difficulty should remain low, got {weak['difficulty_trend']}"
    assert len(weak["concept_summary"]["missing"]) >= 1
    # Check that a gap probe occurred
    strategies = [t["strategy"] for t in weak["turns"]]
    assert "probe_missing_concept" in strategies, "Weak candidate should have triggered probe_missing_concept"

    # 3. Specialist with Gap Assertions
    specialist = results["specialist_with_gap"]
    assert specialist["turns_completed"] >= 5
    strategies_spec = [t["strategy"] for t in specialist["turns"]]
    assert "probe_missing_concept" in strategies_spec, "Specialist should trigger gap probing on system design"

    # 4. Resume-Heavy Candidate Assertions
    resume = results["resume_heavy_candidate"]
    assert resume["turns_completed"] >= 5
    assert any(t["strategy"] == "probe_missing_concept" for t in resume["turns"])

    # 5. LLM Outage Fallback Assertions
    outage = results["llm_outage_scenario"]
    assert outage["turns_completed"] >= 5
    # Every question must be fallback
    assert all(t["is_fallback"] is True for t in outage["turns"])
    # All stages must be covered
    stages_covered = set(t["stage"] for t in outage["turns"])
    assert "ice_breaker" in stages_covered
    assert "fundamentals" in stages_covered
    assert "role_technical" in stages_covered
    assert "deep_dive" in stages_covered
    assert "scenario_managerial" in stages_covered


def test_api_adaptive_policy_step_endpoint():
    """Verify /api/ai/adaptive-policy-step endpoint produces deterministic policy decisions."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    payload = {
        "candidate_id": "cand-api-test",
        "current_stage": "fundamentals",
        "current_competency": "backend",
        "difficulty": 2,
        "score_history": [85],
        "demonstrated_concepts": ["REST"],
        "missing_concepts": [],
        "previous_questions": ["What is REST?"],
        "stage_question_counts": {"fundamentals": 1}
    }
    resp = client.post("/api/ai/adaptive-policy-step", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.text}"
    data = resp.json()
    assert data["next_difficulty"] == 3
    assert data["next_stage"] == "role_technical"
    assert data["strategy"] == "progress_stage"
    assert data["recommended_question_type"] in ["implementation", "debugging", "trade_off", "conceptual", "scenario", "design"]


def test_generate_question_with_adaptive_fields():
    """Verify /api/ai/generate-question accepts questionType and adaptiveReason and returns them."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    payload = {
        "candidate": {"name": "Alex", "skills": ["Python"]},
        "role": {"title": "Backend Engineer"},
        "stage": "deep_dive",
        "competency": "database",
        "difficulty": 4,
        "questionType": "trade_off",
        "adaptiveReason": "Testing trade-off reasoning under concurrency."
    }
    resp = client.post("/api/ai/generate-question", json=payload)
    assert resp.status_code == 200, f"Expected 200, got {resp.text}"
    q = resp.json()
    assert q["questionType"] == "trade_off"
    assert q["adaptiveReason"] == "Testing trade-off reasoning under concurrency."
    assert q["questionExplanation"] is not None
    assert q["questionExplanation"]["target_competency"] == "database"
    assert q["questionExplanation"]["question_type"] == "trade_off"
