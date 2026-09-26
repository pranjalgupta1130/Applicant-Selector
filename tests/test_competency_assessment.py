"""
Phase D — Evidence-Based Competency Assessment & Final Selector Scorecard Test Suite.
Verifies all 25 non-negotiable requirements:
 1. Concept evidence aggregation
 2. Repeated demonstration increases evidence
 3. Repeated misses identify gaps
 4. Contradictory evidence detection
 5. Evidence provenance
 6. Competency coverage
 7. Low coverage vs low score distinction
 8. High score with low confidence
 9. Competency scoring formula
10. Weighted overall score
11. Role competency matching
12. Insufficient evidence detection
13. Strength extraction
14. Gap extraction
15. Technical evidence summary
16. Managerial evidence summary
17. Evidence timeline
18. Deterministic repeated scorecard generation
19. Empty / minimal interview handling
20. Malformed state handling
21. Specialist candidate scenario
22. Strong candidate scenario
23. Weak candidate scenario
24. Recovery candidate scenario
25. Frozen QuestionObject regression
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from fastapi.testclient import TestClient
from main import app
from core.schemas import (
    CandidateProfile,
    TargetRole,
    QuestionObject,
    RubricCriteria,
    FinalScorecard,
    CompetencyEvidence,
    ScorecardResponse
)
from adaptive.state import InterviewState, ConceptMasteryLevel
from adaptive.concept_evidence import ConceptEvidenceAggregator
from adaptive.competency_matrix import RoleCompetencyMatrix
from adaptive.competency_evaluator import CompetencyEvaluator
from adaptive.scorecard_engine import ScorecardEngine
from adaptive.simulator import (
    run_strong_candidate_simulation,
    run_weak_candidate_simulation,
    run_recovery_candidate_simulation,
    run_specialist_candidate_simulation,
    run_insufficient_evidence_simulation
)

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


def create_sample_state() -> InterviewState:
    """Creates a sample multi-turn state covering backend and database."""
    state = InterviewState(difficulty=3, current_stage="role_technical", current_competency="backend")
    state.record_turn(
        question_id="q1",
        question_text="Explain REST APIs and idempotency.",
        question_type="conceptual",
        stage="fundamentals",
        competency="backend",
        difficulty=2,
        score=88,
        covered_concepts=["REST APIs", "idempotency"],
        missing_concepts=[]
    )
    state.record_turn(
        question_id="q2",
        question_text="How do JWTs work with refresh token rotation?",
        question_type="implementation",
        stage="role_technical",
        competency="backend",
        difficulty=3,
        score=92,
        covered_concepts=["JWT authentication", "refresh token rotation"],
        missing_concepts=[]
    )
    state.record_turn(
        question_id="q3",
        question_text="Compare B-Tree indexing and hash indexing in PostgreSQL.",
        question_type="trade_off",
        stage="deep_dive",
        competency="database",
        difficulty=3,
        score=84,
        covered_concepts=["B-Tree indexing"],
        missing_concepts=["write amplification"]
    )
    return state


# =====================================================================
# 1. Concept Evidence Aggregation
# =====================================================================
def test_concept_evidence_aggregation():
    state = create_sample_state()
    ev_map = ConceptEvidenceAggregator.aggregate_from_state(state)

    assert "REST APIs" in ev_map
    assert "JWT authentication" in ev_map
    assert "write amplification" in ev_map

    rest_ev = ev_map["REST APIs"]
    assert rest_ev.testedCount == 1
    assert rest_ev.demonstratedCount == 1
    assert rest_ev.highestScore == 88
    assert rest_ev.competency == "backend"
    assert "conceptual" in rest_ev.questionTypes


# =====================================================================
# 2. Repeated Demonstration Increases Evidence
# =====================================================================
def test_repeated_demonstration_increases_evidence():
    state = InterviewState()
    # Turn 1
    state.record_turn("q1", "Q1", "conceptual", "fundamentals", "backend", 2, score=85, covered_concepts=["REST APIs"])
    ev_map_1 = ConceptEvidenceAggregator.aggregate_from_state(state)
    conf_1 = ev_map_1["REST APIs"].confidence
    assert conf_1 <= 0.60

    # Turn 2
    state.record_turn("q2", "Q2", "implementation", "role_technical", "backend", 3, score=90, covered_concepts=["REST APIs"])
    # Turn 3
    state.record_turn("q3", "Q3", "trade_off", "deep_dive", "backend", 4, score=92, covered_concepts=["REST APIs"])
    ev_map_3 = ConceptEvidenceAggregator.aggregate_from_state(state)
    conf_3 = ev_map_3["REST APIs"].confidence

    assert conf_3 > conf_1
    assert conf_3 >= 0.85
    assert ev_map_3["REST APIs"].demonstratedCount == 3
    assert ev_map_3["REST APIs"].masteryLevel == ConceptMasteryLevel.CONSISTENTLY_DEMONSTRATED.value


# =====================================================================
# 3. Repeated Misses Identify Gaps
# =====================================================================
def test_repeated_misses_identify_gaps():
    state = InterviewState()
    state.record_turn("q1", "Q1", "conceptual", "role_technical", "backend", 3, score=42, missing_concepts=["concurrency race conditions"])
    state.record_turn("q2", "Q2", "debugging", "role_technical", "backend", 2, score=45, missing_concepts=["concurrency race conditions"])

    ev_map = ConceptEvidenceAggregator.aggregate_from_state(state)
    gap_ev = ev_map["concurrency race conditions"]
    assert gap_ev.missedCount == 2
    assert gap_ev.demonstratedCount == 0
    assert gap_ev.confidence <= 0.20
    assert gap_ev.masteryLevel == ConceptMasteryLevel.REPEATEDLY_MISSING.value

    gaps = ScorecardEngine._extract_gaps(state, ev_map)
    assert any(g.area == "concurrency race conditions" and g.severity == "high" for g in gaps)


# =====================================================================
# 4. Contradictory Evidence Detection
# =====================================================================
def test_contradictory_evidence_detection():
    state = InterviewState()
    # Turn 1: Demonstrated
    state.record_turn("q1", "Q1", "conceptual", "fundamentals", "backend", 2, score=85, covered_concepts=["statelessness"])
    # Turn 2: Missed
    state.record_turn("q2", "Q2", "implementation", "role_technical", "backend", 3, score=45, missing_concepts=["statelessness"])

    ev_map = ConceptEvidenceAggregator.aggregate_from_state(state)
    stateless_ev = ev_map["statelessness"]
    assert stateless_ev.demonstratedCount == 1
    assert stateless_ev.missedCount == 1

    comp_ev = CompetencyEvaluator.evaluate_competency("backend", state, "backend_engineer", ev_map)
    assert "statelessness" in comp_ev.contradictoryEvidence
    assert comp_ev.confidence <= 0.65


# =====================================================================
# 5. Evidence Provenance
# =====================================================================
def test_evidence_provenance():
    state = create_sample_state()
    ev_map = ConceptEvidenceAggregator.aggregate_from_state(state)
    jwt_ev = ev_map["JWT authentication"]

    assert len(jwt_ev.provenance) == 1
    prov = jwt_ev.provenance[0]
    assert prov.turnId == 2
    assert prov.questionId == "q2"
    assert prov.score == 92
    assert prov.questionType == "implementation"
    assert prov.isDemonstrated is True


# =====================================================================
# 6. Competency Coverage
# =====================================================================
def test_competency_coverage():
    state = create_sample_state()
    ev_map = ConceptEvidenceAggregator.aggregate_from_state(state)
    comp_ev = CompetencyEvaluator.evaluate_competency("backend", state, "backend_engineer", ev_map)

    expected_pool = RoleCompetencyMatrix.get_expected_concepts("backend")
    assert comp_ev.coverage > 0.0
    assert comp_ev.coverage <= 1.0
    # Expected concepts pool should be greater than 0
    assert len(expected_pool) > 0


# =====================================================================
# 7. Low Coverage vs Low Score Distinction
# =====================================================================
def test_low_coverage_vs_low_score_distinction():
    # Case A: Candidate with high score but low coverage (only 1 turn tested)
    state_a = InterviewState()
    state_a.record_turn("q1", "Q1", "conceptual", "fundamentals", "backend", 3, score=95, covered_concepts=["REST APIs"])
    ev_a = ConceptEvidenceAggregator.aggregate_from_state(state_a)
    comp_a = CompetencyEvaluator.evaluate_competency("backend", state_a, "backend_engineer", ev_a)
    assert comp_a.score >= 90
    assert comp_a.coverage <= 0.30

    # Case B: Candidate with broad coverage but low score (tested 4 concepts, failed all)
    state_b = InterviewState()
    state_b.record_turn(
        "q1", "Q1", "conceptual", "role_technical", "backend", 2,
        score=40,
        missing_concepts=["REST APIs", "statelessness", "HTTP status codes", "idempotency"]
    )
    ev_b = ConceptEvidenceAggregator.aggregate_from_state(state_b)
    comp_b = CompetencyEvaluator.evaluate_competency("backend", state_b, "backend_engineer", ev_b)
    assert comp_b.score <= 45
    assert comp_b.coverage >= 0.40


# =====================================================================
# 8. High Score with Low Confidence
# =====================================================================
def test_high_score_with_low_confidence():
    state = InterviewState()
    state.record_turn("q1", "Q1", "conceptual", "role_technical", "backend", 3, score=92, covered_concepts=["REST APIs"])

    ev_map = ConceptEvidenceAggregator.aggregate_from_state(state)
    comp_ev = CompetencyEvaluator.evaluate_competency("backend", state, "backend_engineer", ev_map)

    # High score observed
    assert comp_ev.score >= 85
    # But confidence must remain low/moderate because of insufficient evidence depth
    assert comp_ev.confidence <= 0.45
    assert comp_ev.status == "insufficient_evidence"


# =====================================================================
# 9. Competency Scoring Formula
# =====================================================================
def test_competency_scoring_formula():
    state = InterviewState()
    state.record_turn("q1", "Q1", "conceptual", "role_technical", "backend", 3, score=80, covered_concepts=["REST APIs"])
    state.record_turn("q2", "Q2", "implementation", "role_technical", "backend", 3, score=90, covered_concepts=["idempotency"])

    ev_map = ConceptEvidenceAggregator.aggregate_from_state(state)
    comp_ev = CompetencyEvaluator.evaluate_competency("backend", state, "backend_engineer", ev_map)

    # Average turn score is 85; 100% concepts demonstrated -> score should be around 90
    assert 85 <= comp_ev.score <= 95
    assert comp_ev.status == "demonstrated"


# =====================================================================
# 10. Weighted Overall Score
# =====================================================================
def test_weighted_overall_score():
    state = create_sample_state()
    custom_weights = {"backend": 0.60, "database": 0.40}

    scorecard = ScorecardEngine.generate_scorecard(
        state=state,
        custom_weights=custom_weights
    )

    assert 0 <= scorecard.overallScore <= 100
    assert 0.0 <= scorecard.overallConfidence <= 1.0


# =====================================================================
# 11. Role Competency Matching
# =====================================================================
def test_role_competency_matching():
    backend_comps = RoleCompetencyMatrix.get_role_competencies("backend_engineer")
    assert "backend" in backend_comps
    assert "database" in backend_comps
    assert "system_design" in backend_comps

    weights = RoleCompetencyMatrix.get_normalized_weights("backend_engineer")
    assert abs(sum(weights.values()) - 1.0) < 0.001


# =====================================================================
# 12. Insufficient Evidence Detection
# =====================================================================
def test_insufficient_evidence_detection():
    state = InterviewState()
    # Only test backend
    state.record_turn("q1", "Q1", "conceptual", "fundamentals", "backend", 2, score=85, covered_concepts=["REST APIs"])

    ev_map = ConceptEvidenceAggregator.aggregate_from_state(state)
    # Database was never tested
    db_ev = CompetencyEvaluator.evaluate_competency("database", state, "backend_engineer", ev_map)
    assert db_ev.status == "untested"
    assert db_ev.confidence == 0.0
    assert db_ev.evidenceCount == 0


# =====================================================================
# 13. Strength Extraction
# =====================================================================
def test_strength_extraction():
    state = create_sample_state()
    scorecard = ScorecardEngine.generate_scorecard(state)

    assert len(scorecard.strengths) >= 1
    s = scorecard.strengths[0]
    assert s.area != ""
    assert s.competency in ["backend", "database", "system_design", "cs_fundamentals"]
    assert len(s.supportingTurns) >= 1
    assert s.confidence >= 0.50


# =====================================================================
# 14. Gap Extraction
# =====================================================================
def test_gap_extraction():
    state = create_sample_state()
    scorecard = ScorecardEngine.generate_scorecard(state)

    assert len(scorecard.gaps) >= 1
    g = scorecard.gaps[0]
    assert g.area == "write amplification"
    assert len(g.supportingTurns) >= 1
    assert g.severity in ["moderate", "high"]


# =====================================================================
# 15. Technical Evidence Summary
# =====================================================================
def test_technical_evidence_summary():
    state = create_sample_state()
    scorecard = ScorecardEngine.generate_scorecard(state)
    tech_summary = scorecard.decisionSupport.technicalEvidence

    assert "technical turn" in tech_summary.lower() or "score" in tech_summary.lower()
    assert len(tech_summary) > 20


# =====================================================================
# 16. Managerial Evidence Summary
# =====================================================================
def test_managerial_evidence_summary():
    # Technical-only session
    state_tech = create_sample_state()
    scorecard_tech = ScorecardEngine.generate_scorecard(state_tech)
    assert "insufficient managerial evidence" in scorecard_tech.decisionSupport.managerialEvidence.lower()

    # Session with managerial turn
    state_man = create_sample_state()
    state_man.record_turn(
        "qm", "Scenario Q", "scenario", "scenario_managerial", "scenario_managerial",
        3, score=85, covered_concepts=["incident triage"]
    )
    scorecard_man = ScorecardEngine.generate_scorecard(state_man)
    assert "scenario/managerial" in scorecard_man.decisionSupport.managerialEvidence.lower()


# =====================================================================
# 17. Evidence Timeline
# =====================================================================
def test_evidence_timeline():
    state = create_sample_state()
    scorecard = ScorecardEngine.generate_scorecard(state)

    assert len(scorecard.evidenceTimeline) == 3
    t1 = scorecard.evidenceTimeline[0]
    assert t1.turn == 1
    assert t1.competency == "backend"
    assert t1.score == 88
    assert "REST APIs" in t1.coveredConcepts


# =====================================================================
# 18. Deterministic Repeated Scorecard Generation
# =====================================================================
def test_deterministic_repeated_scorecard_generation():
    state = create_sample_state()
    cand = CandidateProfile(name="Jordan", skills=["Python", "FastAPI"])
    role = TargetRole()

    sc_1 = ScorecardEngine.generate_scorecard(state, cand, role)
    sc_2 = ScorecardEngine.generate_scorecard(state, cand, role)

    assert sc_1.overallScore == sc_2.overallScore
    assert sc_1.overallConfidence == sc_2.overallConfidence
    assert [c.score for c in sc_1.competencies] == [c.score for c in sc_2.competencies]
    assert [s.area for s in sc_1.strengths] == [s.area for s in sc_2.strengths]
    assert [g.area for g in sc_1.gaps] == [g.area for g in sc_2.gaps]


# =====================================================================
# 19. Empty / Minimal Interview Handling
# =====================================================================
def test_empty_minimal_interview_handling():
    empty_state = InterviewState()
    scorecard = ScorecardEngine.generate_scorecard(empty_state)

    assert scorecard.overallScore == 0
    assert scorecard.overallConfidence == 0.0
    assert len(scorecard.evidenceTimeline) == 0
    assert all(c.status == "untested" for c in scorecard.competencies)


# =====================================================================
# 20. Malformed State Handling via API
# =====================================================================
def test_malformed_state_handling_via_api():
    payload = {
        "interviewState": {},  # empty state dict
        "candidate": {"name": "Test Candidate"},
        "role": {"title": "Backend Engineer"}
    }
    res = client.post("/api/interview/scorecard", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "scorecard" in data
    assert "overallScore" in data["scorecard"]


# =====================================================================
# 21. Specialist Candidate Scenario
# =====================================================================
def test_specialist_candidate_scorecard_scenario():
    sim_res = run_specialist_candidate_simulation()
    state = InterviewState(**sim_res["final_state"])
    scorecard = ScorecardEngine.generate_scorecard(state)

    comp_dict = {c.competency: c for c in scorecard.competencies}
    # Backend and Database should be strong
    assert comp_dict["backend"].score >= 80
    assert comp_dict["database"].score >= 80

    # System design should reflect lower score / gap
    assert comp_dict["system_design"].score < 80
    assert any("horizontal scaling" in g.area or "load balancing" in g.area or "system_design" in g.competency for g in scorecard.gaps)


# =====================================================================
# 22. Strong Candidate Scenario
# =====================================================================
def test_strong_candidate_scorecard_scenario():
    sim_res = run_strong_candidate_simulation()
    state = InterviewState(**sim_res["final_state"])
    scorecard = ScorecardEngine.generate_scorecard(state)

    assert scorecard.overallScore >= 80
    assert scorecard.overallConfidence >= 0.70
    assert len(scorecard.strengths) >= 2


# =====================================================================
# 23. Weak Candidate Scenario
# =====================================================================
def test_weak_candidate_scorecard_scenario():
    sim_res = run_weak_candidate_simulation()
    state = InterviewState(**sim_res["final_state"])
    scorecard = ScorecardEngine.generate_scorecard(state)

    assert scorecard.overallScore <= 60
    assert len(scorecard.gaps) >= 1
    assert any(g.severity in ["moderate", "high"] for g in scorecard.gaps)


# =====================================================================
# 24. Recovery Candidate Scenario
# =====================================================================
def test_recovery_candidate_scorecard_scenario():
    sim_res = run_recovery_candidate_simulation()
    state = InterviewState(**sim_res["final_state"])
    scorecard = ScorecardEngine.generate_scorecard(state)

    assert "JWT authentication" in state.recovered_concepts
    # Recovered concept should not be an active high-severity gap
    assert not any(g.area == "JWT authentication" and g.severity == "high" for g in scorecard.gaps)
    # Trajectory timeline should contain "recovered" status
    assert any(t.evidenceStatus == "recovered" for t in scorecard.evidenceTimeline)


# =====================================================================
# 25. Frozen QuestionObject Regression
# =====================================================================
def test_frozen_question_object_regression():
    # Verify starting question conforms to frozen contract
    res_start = client.post("/api/interview/start", json={})
    assert res_start.status_code == 200
    q = res_start.json()["openingQuestion"]

    for field in FROZEN_CONTRACT_FIELDS:
        assert field in q, f"Missing frozen field '{field}' in openingQuestion"
    assert q["rubric"]["poor"] != ""
    assert q["rubric"]["acceptable"] != ""
    assert q["rubric"]["excellent"] != ""
