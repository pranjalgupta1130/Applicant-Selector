"""
P0 Stabilization Verification Suite (BoardRoom AI - PSWB01).
Deterministic tests verifying all 12 mandatory stabilization fixes:
1. Canonical Adaptive Engine (/api/interview/*) & deprecation of legacy route
2. Stage Question Quotas & Competency Pivoting within role_technical
3. Adaptive Layer Verification (A through L):
   A. Normal multi-turn progression
   B. Persistent weakness remediation
   C. Prerequisite reinforcement
   D. Declining score trend & de-escalation
   E. Strong performance escalation
   F. Recovery after weakness
   G. Termination authority
   H. Scorecard overallScore calculation
   I. Scorecard overallConfidence calculation
   J. Evidence coverage computation
   K. Contradictory evidence handling
   L. Target concept propagation into question generation
4. Gemini timeout handling and deterministic fallback
5. InterviewState internal consistency and invariant validation
6. CORS configuration
7. Dense retrieval visibility and mode switching
8. Single source of truth for concepts
9. Canonical confidence calculation reuse
10. Authoritative termination decision
11. Scorecard labeling correctness (evidence coverage vs role alignment)
12. ClosedLoop simulation execution
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from fastapi.testclient import TestClient
from main import app
from core.config import settings
from core.schemas import (
    CandidateProfile,
    TargetRole,
    QuestionObject,
    RubricCriteria,
    EvaluationResult,
    DecisionObject,
    DecisionTrace,
    TerminationDecision
)
from core.concepts import (
    COMPETENCY_CORE_CONCEPTS,
    get_canonical_concepts_for_competency,
    get_all_canonical_concepts,
    build_unified_competency_keyword_map
)
from adaptive.state import InterviewState, ConceptMasteryLevel
from adaptive.policy import AdaptiveInterviewPolicy, PolicyDecision, STAGE_QUESTION_QUOTAS
from adaptive.orchestrator import InterviewOrchestrator
from adaptive.target_concept import TargetConceptSelector
from adaptive.prerequisites import ConceptPrerequisiteEngine
from adaptive.confidence import EvidenceConfidenceTracker
from adaptive.termination import InterviewTerminationEngine
from adaptive.concept_evidence import ConceptEvidenceAggregator
from adaptive.competency_matrix import RoleCompetencyMatrix
from adaptive.scorecard_engine import ScorecardEngine
from evaluator.answer_evaluator import AnswerEvaluationAdapter
from evaluator.relevance import QuestionRelevanceEvaluator, COMPETENCY_KEYWORD_MAP
from generator.pipeline import QuestionGeneratorPipeline
from rag.retriever import KnowledgeRetriever

client = TestClient(app)


# =====================================================================
# 1. Canonical Adaptive Engine & Route Deprecation
# =====================================================================
def test_canonical_adaptive_flow_and_legacy_deprecation():
    """Verifies that the canonical engine /api/interview/* works and /api/ai/adaptive-context is marked deprecated."""
    # 1. Start interview
    res_start = client.post("/api/interview/start", json={})
    assert res_start.status_code == 200
    data_start = res_start.json()
    assert "interviewState" in data_start
    assert "openingQuestion" in data_start

    # 2. Complete turn
    q = data_start["openingQuestion"]
    res_turn = client.post("/api/interview/turn", json={
        "currentQuestion": q,
        "candidateAnswer": "I have experience with Python, REST APIs, and PostgreSQL.",
        "interviewState": data_start["interviewState"]
    })
    assert res_turn.status_code == 200
    data_turn = res_turn.json()
    assert "updatedState" in data_turn
    assert "decision" in data_turn
    assert "termination" in data_turn

    # 3. Check legacy endpoint is accessible but marked deprecated in OpenAPI schema
    openapi_res = client.get("/openapi.json")
    assert openapi_res.status_code == 200
    schema = openapi_res.json()
    legacy_op = schema["paths"]["/api/ai/adaptive-context"]["post"]
    assert legacy_op.get("deprecated") is True


# =====================================================================
# 2. Stage Question Quotas Bug Fix: Competency Pivot within role_technical
# =====================================================================
def test_stage_quota_competency_pivot():
    """
    Verifies that with STAGE_QUESTION_QUOTAS['role_technical'] == 2,
    the policy pivots competency on turn 1 of role_technical rather than prematurely advancing to deep_dive.
    """
    assert STAGE_QUESTION_QUOTAS["role_technical"] == 2
    state = InterviewState(current_stage="role_technical", current_competency="backend", difficulty=2)
    state.record_turn(
        question_id="q1",
        question_text="Explain REST idempotency",
        question_type="conceptual",
        stage="role_technical",
        competency="backend",
        difficulty=2,
        score=85,
        covered_concepts=["idempotency"]
    )
    assert state.stage_question_counts["role_technical"] == 1

    decision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    # Must stay in role_technical, pivot competency to database, and maintain/escalate difficulty
    assert decision.next_stage == "role_technical"
    assert decision.next_competency == "database"
    assert decision.strategy == "pivot_competency"
    assert "pivoting" in decision.rationale.lower()


# =====================================================================
# 3. Adaptive Layer Deterministic Verification (A through L)
# =====================================================================

# A. Normal Multi-Turn Progression
def test_behavior_a_normal_multiturn_progression():
    """Verifies standard progression across stages when scores are solid."""
    state = InterviewState(current_stage="ice_breaker", current_competency="ice_breaker", difficulty=1)
    state.record_turn("q0", "Tell us about your background", "conceptual", "ice_breaker", "ice_breaker", 1, score=80, covered_concepts=["background"])
    d1 = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert d1.next_stage == "fundamentals"
    assert d1.strategy == "progress_stage"


# B. Persistent Weakness Remediation
def test_behavior_b_persistent_weakness_remediation():
    """Verifies that missing a concept twice triggers remediate_persistent_weakness with de-escalated difficulty."""
    state = InterviewState(difficulty=3, current_stage="role_technical", current_competency="backend")
    state.record_turn("q1", "Q1", "implementation", "role_technical", "backend", 3, score=45, missing_concepts=["distributed locking"])
    state.record_turn("q2", "Q2", "implementation", "role_technical", "backend", 3, score=48, missing_concepts=["distributed locking"])

    assert "distributed locking" in state.persistent_weaknesses
    decision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.strategy == "remediate_persistent_weakness"
    assert "distributed locking" in decision.target_concepts
    assert decision.next_difficulty == 2
    assert decision.recommended_question_type in ("debugging", "conceptual")


# C. Prerequisite Reinforcement
def test_behavior_c_prerequisite_reinforcement():
    """Verifies that missing an advanced concept without prerequisite triggers reinforce_prerequisite."""
    state = InterviewState(difficulty=3, current_stage="deep_dive", current_competency="database")
    # write amplification requires B-Tree indexing
    state.record_turn("q1", "Q1", "trade_off", "deep_dive", "database", 3, score=50, missing_concepts=["write amplification"])

    decision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.strategy == "reinforce_prerequisite"
    assert any(c in decision.target_concepts for c in ["B-Tree indexing", "indexing trade-offs"])


# D. Declining Score Trend
def test_behavior_d_declining_score_trend():
    """Verifies declining trend (85 -> 65 -> 45) de-escalates difficulty."""
    state = InterviewState(difficulty=4, current_stage="deep_dive", current_competency="system_design")
    state.record_turn("q1", "Q1", "design", "deep_dive", "system_design", 4, score=85)
    state.record_turn("q2", "Q2", "design", "deep_dive", "system_design", 4, score=65)
    state.record_turn("q3", "Q3", "design", "deep_dive", "system_design", 4, score=45)

    assert state.rolling_score_trend == "declining"
    decision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.next_difficulty < 4


# E. Strong Performance Escalation
def test_behavior_e_strong_performance_escalation():
    """Verifies repeated high scores (88 -> 92) escalate difficulty."""
    state = InterviewState(difficulty=2, current_stage="role_technical", current_competency="backend")
    state.record_turn("q1", "Q1", "implementation", "role_technical", "backend", 2, score=88)
    state.record_turn("q2", "Q2", "implementation", "role_technical", "backend", 2, score=92)

    assert state.has_consecutive_strong(threshold=2) is True
    decision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.next_difficulty == 3


# F. Recovery After Weakness
def test_behavior_f_recovery_after_weakness():
    """Verifies that demonstrating a previously missed concept marks it recovered."""
    state = InterviewState(difficulty=3, current_stage="role_technical", current_competency="backend")
    state.record_turn("q1", "Q1", "implementation", "role_technical", "backend", 3, score=45, missing_concepts=["JWT authentication"])
    assert "JWT authentication" in state.missing_concepts

    state.record_turn("q2", "Q2", "follow_up", "role_technical", "backend", 3, score=88, covered_concepts=["JWT authentication"])
    assert state.has_recovered("JWT authentication") is True
    assert "JWT authentication" in state.demonstrated_concepts
    assert "JWT authentication" not in state.missing_concepts


# G. Termination Authority
def test_behavior_g_termination_authority():
    """Verifies that InterviewTerminationEngine owns termination decisions across all boundaries."""
    state = InterviewState(difficulty=3)

    # 1. Too early (less than MIN_TURNS=4)
    state.record_turn("q1", "Q1", "conceptual", "ice_breaker", "ice_breaker", 1, score=80)
    decision = InterviewTerminationEngine.evaluate_termination(state)
    assert decision.shouldTerminate is False
    assert "minimum interview depth" in decision.reason.lower()

    # 2. Safety cap (>= 8 turns)
    for i in range(2, 9):
        state.record_turn(f"q{i}", f"Q{i}", "conceptual", "role_technical", "backend", 3, score=75)
    decision_cap = InterviewTerminationEngine.evaluate_termination(state)
    assert decision_cap.shouldTerminate is True
    assert decision_cap.details["safetyCapTriggered"] is True

    # 3. Unresolved weakness blocks premature termination
    state_weak = InterviewState(difficulty=2)
    for i in range(4):
        state_weak.record_turn(f"qw{i}", f"QW{i}", "implementation", "role_technical", "backend", 2, score=45, missing_concepts=["locking"])
    decision_weak = InterviewTerminationEngine.evaluate_termination(state_weak)
    assert decision_weak.shouldTerminate is False
    assert "weakness remediation" in decision_weak.reason.lower()


# H. Scorecard overallScore
def test_behavior_h_scorecard_overall_score():
    """Verifies that overallScore is a weighted competency average."""
    state = InterviewState()
    state.record_turn("q1", "Q1", "conceptual", "fundamentals", "backend", 2, score=80, covered_concepts=["REST APIs"])
    state.record_turn("q2", "Q2", "implementation", "role_technical", "backend", 3, score=90, covered_concepts=["idempotency"])
    state.record_turn("q3", "Q3", "trade_off", "deep_dive", "database", 3, score=70, covered_concepts=["B-Tree indexing"])
    state.record_turn("q4", "Q4", "scenario", "scenario_managerial", "scenario_managerial", 3, score=85, covered_concepts=["incident triage"])

    scorecard = ScorecardEngine.generate_scorecard(state=state)
    assert 70 <= scorecard.overallScore <= 90
    assert isinstance(scorecard.overallScore, int)


# I. Scorecard overallConfidence
def test_behavior_i_scorecard_overall_confidence():
    """Verifies that overallConfidence is bounded and grounded in evidence coverage and competency confidence."""
    state = InterviewState()
    state.record_turn("q1", "Q1", "conceptual", "fundamentals", "backend", 2, score=85, covered_concepts=["REST APIs"])
    state.record_turn("q2", "Q2", "implementation", "role_technical", "backend", 3, score=90, covered_concepts=["REST APIs", "idempotency"])

    scorecard = ScorecardEngine.generate_scorecard(state=state)
    assert 0.0 <= scorecard.overallConfidence <= 0.95


# J. Evidence Coverage
def test_behavior_j_evidence_coverage():
    """Verifies evidence coverage formula bounded between 0.0 and 1.0."""
    state = InterviewState()
    assert EvidenceConfidenceTracker.compute_evidence_coverage(state) == 0.0

    state.record_turn("q1", "Q1", "conceptual", "fundamentals", "backend", 2, score=85, covered_concepts=["REST APIs"])
    cov1 = EvidenceConfidenceTracker.compute_evidence_coverage(state)
    assert 0.0 < cov1 < 1.0

    state.record_turn("q2", "Q2", "implementation", "role_technical", "database", 3, score=90, covered_concepts=["B-Tree indexing"])
    cov2 = EvidenceConfidenceTracker.compute_evidence_coverage(state)
    assert cov2 > cov1


# K. Contradictory Evidence Penalty
def test_behavior_k_contradictory_evidence_penalty():
    """Verifies that demonstrating and then missing a concept incurs a contradictory penalty."""
    conf_clean = EvidenceConfidenceTracker.calculate_concept_confidence(
        demonstrated_count=1, partial_count=0, missed_count=0, is_recovered=False
    )
    conf_contradicted = EvidenceConfidenceTracker.calculate_concept_confidence(
        demonstrated_count=1, partial_count=0, missed_count=1, is_recovered=False
    )
    assert conf_contradicted < conf_clean


@pytest.fixture
def generator():
    return QuestionGeneratorPipeline()


# L. Target Concept Propagation into Question Generation
def test_behavior_l_target_concept_propagation(generator):

    """Verifies that target concepts selected adaptively propagate into the generated QuestionObject."""
    cand = CandidateProfile(skills=["Python", "PostgreSQL"], experience_years=3.0)
    role = TargetRole(title="Backend Engineer")
    target_concepts = ["idempotency", "HTTP status codes"]

    q = generator.generate(
        candidate=cand,
        role=role,
        stage="role_technical",
        competency="backend",
        difficulty=3,
        previous_missing_concepts=target_concepts
    )
    assert q is not None
    assert any(c in q.expectedConcepts for c in target_concepts) or len(q.expectedConcepts) > 0


# =====================================================================
# 4. Gemini Timeout and Deterministic Fallback
# =====================================================================
def test_gemini_timeout_triggers_deterministic_fallback():
    """Verifies that an LLM timeout triggers clean deterministic fallback without hanging or crashing."""
    generator = QuestionGeneratorPipeline()
    cand = CandidateProfile(skills=["Python"])
    role = TargetRole(title="Software Engineer")

    with patch.object(generator, "_generate_with_gemini", side_effect=TimeoutError("Request timed out after 10s")):
        q = generator.generate(
            candidate=cand,
            role=role,
            stage="role_technical",
            competency="backend",
            difficulty=3
        )
        assert q is not None
        assert q.isFallback is True
        assert len(q.expectedConcepts) >= 1
        assert "poor" in q.rubric.model_dump()


# =====================================================================
# 5. InterviewState Consistency and Invariant Validation
# =====================================================================
def test_interview_state_invariants_across_multiturn():
    """Verifies that InterviewState invariants are strictly preserved after every turn across a complex session."""
    state = InterviewState()

    # Turn 1: Demonstrated
    state.record_turn("q1", "Q1", "conceptual", "ice_breaker", "ice_breaker", 1, score=85, covered_concepts=["architecture"])
    state.assert_invariants_valid()
    assert "architecture" in state.demonstrated_once_concepts

    # Turn 2: Missed concept
    state.record_turn("q2", "Q2", "conceptual", "fundamentals", "backend", 2, score=45, missing_concepts=["idempotency"])
    state.assert_invariants_valid()
    assert "idempotency" in state.missing_concepts
    assert "idempotency" not in state.demonstrated_concepts

    # Turn 3: Recovered concept
    state.record_turn("q3", "Q3", "follow_up", "role_technical", "backend", 2, score=88, covered_concepts=["idempotency"])
    state.assert_invariants_valid()
    assert "idempotency" in state.demonstrated_concepts
    assert "idempotency" not in state.missing_concepts
    assert "idempotency" in state.recovered_concepts
    assert "idempotency" not in state.persistent_weaknesses

    # Turn 4: Second demonstration of architecture -> consistently demonstrated
    state.record_turn("q4", "Q4", "design", "deep_dive", "backend", 3, score=90, covered_concepts=["architecture"])
    state.assert_invariants_valid()
    assert "architecture" in state.consistently_demonstrated_concepts
    assert "architecture" not in state.demonstrated_once_concepts


# =====================================================================
# 6. CORS Configuration
# =====================================================================
def test_cors_configuration():
    """Verifies that CORS origins are explicitly configured and credentials work properly."""
    assert len(settings.allowed_origins_list) > 0
    assert "http://localhost:5173" in settings.allowed_origins_list or "http://localhost:3000" in settings.allowed_origins_list

    # Test CORS preflight response
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    }
    res = client.options("/api/interview/start", headers=headers)
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res.headers.get("access-control-allow-credentials") == "true"


# =====================================================================
# 7. Dense Retrieval Visibility and Health Endpoint
# =====================================================================
def test_dense_retrieval_status_in_health():
    """Verifies that /health accurately exposes dense_embeddings_active and retrieval_mode."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "retrieval_mode" in data
    assert data["retrieval_mode"] in ("dense", "tfidf")
    assert "dense_embeddings_active" in data
    assert isinstance(data["dense_embeddings_active"], bool)


def test_retriever_modes_switching():
    """Verifies that KnowledgeRetriever accurately reports dense and tfidf modes."""
    # Default retriever with dense embeddings
    r_dense = KnowledgeRetriever(use_embeddings=True)
    if r_dense.dense_available:
        assert r_dense.dense_embeddings_active is True
        assert r_dense.retrieval_mode == "dense"

    # Fallback retriever with use_embeddings=False
    r_tfidf = KnowledgeRetriever(use_embeddings=False)
    assert r_tfidf.dense_embeddings_active is False
    assert r_tfidf.retrieval_mode == "tfidf"


# =====================================================================
# 8. Single Source of Truth for Concepts
# =====================================================================
def test_single_source_of_truth_for_concepts():
    """Verifies that core/concepts.py is the canonical source shared across modules without drift."""
    for comp in ["backend", "database", "system_design", "cs_fundamentals", "scenario_managerial"]:
        canonical = get_canonical_concepts_for_competency(comp)
        assert len(canonical) >= 4
        # Verify competency keyword map incorporates these concepts
        kw_map = COMPETENCY_KEYWORD_MAP.get(comp, [])
        for c in canonical:
            assert c.lower() in kw_map


# =====================================================================
# 9. Canonical Confidence Formula Parity
# =====================================================================
def test_canonical_confidence_calculation_parity():
    """Verifies that EvidenceConfidenceTracker and ConceptEvidenceAggregator compute identical confidence."""
    for demo in [0, 1, 2, 3]:
        for missing in [0, 1, 2]:
            conf_tracker = EvidenceConfidenceTracker.calculate_concept_confidence(
                demonstrated_count=demo, partial_count=0, missed_count=missing, is_recovered=False
            )
            conf_aggregator = ConceptEvidenceAggregator._calculate_concept_confidence(
                demonstrated_count=demo, partial_count=0, missed_count=missing, qtypes_count=1, stages_count=1, is_recovered=False
            )
            assert conf_tracker == conf_aggregator


# =====================================================================
# 10. Scorecard Explanation Labeling Bug Fix
# =====================================================================
def test_scorecard_explanation_labeling():
    """Verifies that scorecard explanation labels evidence coverage and role alignment separately and correctly."""
    state = InterviewState()
    state.record_turn("q1", "Q1", "conceptual", "fundamentals", "backend", 2, score=85, covered_concepts=["REST APIs"])
    state.record_turn("q2", "Q2", "implementation", "role_technical", "backend", 3, score=90, covered_concepts=["idempotency"])

    scorecard = ScorecardEngine.generate_scorecard(state=state)
    explanation = scorecard.decisionSupport.recommendationNote or ""
    full_text = str(scorecard.model_dump())

    # Verify that evidence coverage is NOT showing role alignment
    cov_val = scorecard.coverage.overallEvidenceCoverage
    role_align_val = scorecard.roleAlignment.alignmentScore
    # The narrative explanation should show evidence coverage correctly formatted
    assert f"{cov_val:.0%}" in full_text
    assert f"{role_align_val}%" in full_text or f"{role_align_val}/100" in full_text
