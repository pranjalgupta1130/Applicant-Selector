"""
Comprehensive Unit Test Suite for Final Scorecard & Evaluation Quality (Task Fix).
Validates:
1. Aerodynamics role receives strictly Aerodynamics competencies (zero Radar/DSP).
2. Radar role receives Radar/DSP competencies.
3. Cyber role receives Cyber competencies.
4. Ice breaker stage technical correctness is None (N/A).
5. Core technical stage receives technical correctness evaluation.
6. Untested competency score is None (not 0).
7. Overall score calculation excludes untested competencies.
8. Every evaluated score is supported by interview evidence.
"""

import pytest
from core.schemas import CandidateProfile, TargetRole, QuestionObject
from adaptive.competency_matrix import RoleCompetencyMatrix
from adaptive.state import InterviewState
from adaptive.competency_evaluator import CompetencyEvaluator
from adaptive.scorecard_engine import ScorecardEngine
from evaluator.scoring import score_answer


def test_aerodynamics_role_competency_mapping():
    comps = RoleCompetencyMatrix.get_role_competencies("Scientist B — Aerodynamics")
    assert "aerodynamics_fundamentals" in comps
    assert "fluid_mechanics_cfd" in comps
    assert "aerodynamic_analysis" in comps
    assert "system_engineering" in comps
    assert "techno_managerial" in comps
    # Guarantee ZERO Radar / DSP / ECE competencies
    assert "radar_rf_systems" not in comps
    assert "digital_signal_processing" not in comps
    assert "embedded_realtime_systems" not in comps
    assert "avionics_communication" not in comps


def test_radar_role_competency_mapping():
    comps = RoleCompetencyMatrix.get_role_competencies("Scientist C — Radar Signal Processing")
    assert "radar_rf_systems" in comps
    assert "digital_signal_processing" in comps
    assert "embedded_realtime_systems" in comps
    assert "system_engineering" in comps
    assert "techno_managerial" in comps
    assert "aerodynamics_fundamentals" not in comps


def test_cyber_role_competency_mapping():
    comps = RoleCompetencyMatrix.get_role_competencies("Scientist B — Cybersecurity")
    assert "cybersecurity_fundamentals" in comps
    assert "network_security" in comps
    assert "system_resilience" in comps
    assert "system_engineering" in comps
    assert "techno_managerial" in comps
    assert "radar_rf_systems" not in comps


def test_ice_breaker_technical_correctness_is_none():
    q = QuestionObject(
        id="ib_1",
        text="Could you walk us through your academic background and engineering interest?",
        stage="ice_breaker",
        competency="aerodynamics_fundamentals",
        difficulty=1,
        expectedConcepts=["academic background", "engineering focus"],
        rubric={"poor": "p", "acceptable": "a", "excellent": "e"},
        relevanceScore=90
    )
    result = score_answer(q, "I have a Ph.D. in Aerospace Engineering focusing on fluid mechanics.")
    assert result["subScores"]["technicalCorrectness"] is None
    assert "relevance" in result["subScores"]
    assert "background_alignment" in result["subScores"]


def test_core_technical_receives_technical_correctness():
    q = QuestionObject(
        id="core_1",
        text="What are the primary factors that influence aerodynamic lift on an aircraft wing?",
        stage="core_technical",
        competency="aerodynamics_fundamentals",
        difficulty=3,
        expectedConcepts=["angle of attack", "airfoil shape", "air density", "airspeed"],
        rubric={"poor": "p", "acceptable": "a", "excellent": "e"},
        relevanceScore=90
    )
    result = score_answer(q, "Lift depends on angle of attack, airfoil camber, dynamic pressure, air density, and wing area.")
    assert result["subScores"]["technicalCorrectness"] is not None
    assert isinstance(result["subScores"]["technicalCorrectness"], int)


def test_untested_competency_score_is_none_not_zero():
    state = InterviewState(session_id="test_sess_01", current_stage="core_technical")
    state.record_turn(
        question_id="q1",
        question_text="Sample aero question",
        question_type="conceptual",
        stage="core_technical",
        competency="aerodynamics_fundamentals",
        difficulty=3,
        score=85,
        covered_concepts=["angle of attack"],
        missing_concepts=[]
    )
    
    comp_ev = CompetencyEvaluator.evaluate_competency(
        competency="techno_managerial",
        state=state,
        role_id="drdo_scientist_aerospace"
    )
    
    assert comp_ev.status == "untested"
    assert comp_ev.score is None


def test_overall_score_excludes_untested_competencies():
    state = InterviewState(session_id="test_sess_02", current_stage="core_technical")
    state.record_turn(
        question_id="q1",
        question_text="Aerodynamic lift principles",
        question_type="conceptual",
        stage="core_technical",
        competency="aerodynamics_fundamentals",
        difficulty=3,
        score=90,
        covered_concepts=["angle of attack", "airfoil shape"],
        missing_concepts=[]
    )
    
    role = TargetRole(id="drdo_scientist_aerospace", title="Scientist B — Aerodynamics")
    scorecard = ScorecardEngine.generate_scorecard(state=state, role=role)
    
    # Overall score should average only evaluated competency (approx 90), not diluted by 0s from untested competencies
    assert scorecard.overallScore >= 80
    
    # Check that untested competencies remain status=untested and score=None
    untested_comps = [c for c in scorecard.competencies if c.status == "untested"]
    assert len(untested_comps) > 0
    for uc in untested_comps:
        assert uc.score is None


def test_evaluated_scores_have_supporting_evidence():
    state = InterviewState(session_id="test_sess_03", current_stage="core_technical")
    state.record_turn(
        question_id="q1",
        question_text="Describe CFD discretization",
        question_type="conceptual",
        stage="core_technical",
        competency="fluid_mechanics_cfd",
        difficulty=3,
        score=75,
        covered_concepts=["finite-volume discretization"],
        missing_concepts=[]
    )
    
    role = TargetRole(id="drdo_scientist_aerospace", title="Scientist B — Aerodynamics")
    scorecard = ScorecardEngine.generate_scorecard(state=state, role=role)
    
    evaluated_comps = [c for c in scorecard.competencies if c.status != "untested"]
    assert len(evaluated_comps) > 0
    for ec in evaluated_comps:
        assert ec.score is not None
        assert ec.reasoning != ""
        assert len(ec.strongEvidence) > 0 or len(ec.weakEvidence) > 0 or len(ec.testedConcepts) > 0
