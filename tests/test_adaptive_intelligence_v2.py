"""
Test Suite for Phase B — Adaptive Intelligence v2 (BoardRoom AI).
Tests performance trend analysis, concept prerequisite graph enforcement,
mastery confidence evolution, persistent weakness remediation, and historical adaptive policy decisions.
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from adaptive.state import InterviewState, ConceptMasteryLevel
from adaptive.policy import AdaptiveInterviewPolicy, PolicyDecision
from adaptive.prerequisites import ConceptPrerequisiteEngine, CONCEPT_PREREQUISITE_GRAPH


# -------------------------------------------------------------
# 1. Performance Trend Tests
# -------------------------------------------------------------

def test_improving_candidate_trend_and_escalation():
    """
    Verifies that an improving candidate trend (e.g. 50 -> 72 -> 88)
    is detected by the rolling trend tracker and triggers difficulty escalation.
    """
    state = InterviewState(difficulty=2, current_stage="fundamentals", current_competency="backend")
    
    state.record_turn(
        question_id="q1",
        question_text="Q1 text",
        question_type="conceptual",
        stage="fundamentals",
        competency="backend",
        difficulty=2,
        score=50,
        covered_concepts=["REST basics"]
    )
    state.record_turn(
        question_id="q2",
        question_text="Q2 text",
        question_type="implementation",
        stage="fundamentals",
        competency="backend",
        difficulty=2,
        score=72,
        covered_concepts=["HTTP verbs"]
    )
    state.record_turn(
        question_id="q3",
        question_text="Q3 text",
        question_type="trade_off",
        stage="fundamentals",
        competency="backend",
        difficulty=2,
        score=88,
        covered_concepts=["Idempotency"]
    )

    assert state.rolling_score_trend == "improving"
    assert state.score_history == [50, 72, 88]

    decision: PolicyDecision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.next_difficulty == 3
    assert "improving" in decision.rationale.lower() or "sustained" in decision.rationale.lower() or "escalat" in decision.rationale.lower()


def test_declining_candidate_trend_and_deescalation():
    """
    Verifies that a declining candidate trend (e.g. 86 -> 64 -> 45)
    is detected and triggers difficulty de-escalation to prevent cognitive overload.
    """
    state = InterviewState(difficulty=4, current_stage="deep_dive", current_competency="system_design")
    
    state.record_turn(
        question_id="q1",
        question_text="Q1 text",
        question_type="design",
        stage="deep_dive",
        competency="system_design",
        difficulty=4,
        score=86,
        covered_concepts=["Load balancing"]
    )
    state.record_turn(
        question_id="q2",
        question_text="Q2 text",
        question_type="trade_off",
        stage="deep_dive",
        competency="system_design",
        difficulty=4,
        score=64,
        covered_concepts=["Consistent hashing"]
    )
    state.record_turn(
        question_id="q3",
        question_text="Q3 text",
        question_type="scenario",
        stage="deep_dive",
        competency="system_design",
        difficulty=4,
        score=45,
        missing_concepts=["CAP theorem"]
    )

    assert state.rolling_score_trend == "declining"
    decision: PolicyDecision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.next_difficulty <= 3
    assert decision.next_difficulty < 4


def test_repeated_strong_performance():
    """
    Verifies that consecutive scores >= 80 increment consecutive_strong_count
    and trigger difficulty escalation with streak acknowledgment.
    """
    state = InterviewState(difficulty=2, current_stage="role_technical", current_competency="backend")
    
    state.record_turn(
        question_id="q1",
        question_text="Q1 text",
        question_type="implementation",
        stage="role_technical",
        competency="backend",
        difficulty=2,
        score=88,
        covered_concepts=["JWT auth"]
    )
    assert state.consecutive_strong_count == 1
    assert state.has_consecutive_strong(threshold=2) is False

    state.record_turn(
        question_id="q2",
        question_text="Q2 text",
        question_type="debugging",
        stage="role_technical",
        competency="backend",
        difficulty=2,
        score=92,
        covered_concepts=["Token signature"]
    )
    assert state.consecutive_strong_count == 2
    assert state.has_consecutive_strong(threshold=2) is True

    decision: PolicyDecision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.next_difficulty == 3
    assert "consecutive strong" in decision.rationale.lower() or "sustained strong" in decision.rationale.lower()


def test_repeated_weak_performance():
    """
    Verifies that consecutive low scores (< 55) increment consecutive_weak_count
    and de-escalate difficulty down toward baseline 1.
    """
    state = InterviewState(difficulty=3, current_stage="fundamentals", current_competency="cs_fundamentals")
    
    state.record_turn(
        question_id="q1",
        question_text="Q1 text",
        question_type="conceptual",
        stage="fundamentals",
        competency="cs_fundamentals",
        difficulty=3,
        score=42,
        missing_concepts=["Process isolation"]
    )
    assert state.consecutive_weak_count == 1

    state.record_turn(
        question_id="q2",
        question_text="Q2 text",
        question_type="debugging",
        stage="fundamentals",
        competency="cs_fundamentals",
        difficulty=3,
        score=46,
        missing_concepts=["Virtual memory"]
    )
    assert state.consecutive_weak_count == 2
    assert state.has_consecutive_weak(threshold=2) is True

    decision: PolicyDecision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.next_difficulty == 2
    assert "weak" in decision.rationale.lower() or "reduc" in decision.rationale.lower()


# -------------------------------------------------------------
# 2. Concept Mastery Confidence & Recovery Tests
# -------------------------------------------------------------

def test_mastery_confidence_evolution():
    """
    Verifies that repeated evidence distinguishes:
    untested -> demonstrated_once -> consistently_demonstrated.
    """
    state = InterviewState()

    # Turn 1: First demonstration (score 85)
    state.record_turn(
        question_id="q1",
        question_text="Q1",
        question_type="conceptual",
        stage="fundamentals",
        competency="backend",
        difficulty=2,
        score=85,
        covered_concepts=["CAP theorem"]
    )
    assert state.mastery_levels.get("CAP theorem") == ConceptMasteryLevel.DEMONSTRATED_ONCE.value
    assert "CAP theorem" in state.demonstrated_once_concepts
    assert "CAP theorem" not in state.consistently_demonstrated_concepts

    # Turn 2: Second demonstration (score 90)
    state.record_turn(
        question_id="q2",
        question_text="Q2",
        question_type="trade_off",
        stage="deep_dive",
        competency="system_design",
        difficulty=3,
        score=90,
        covered_concepts=["CAP theorem"]
    )
    assert state.mastery_levels.get("CAP theorem") == ConceptMasteryLevel.CONSISTENTLY_DEMONSTRATED.value
    assert "CAP theorem" in state.consistently_demonstrated_concepts
    assert "CAP theorem" not in state.demonstrated_once_concepts


def test_persistent_weakness_detection_and_remediation():
    """
    Verifies that a concept missed across multiple turns becomes a persistent_weakness / repeatedly_missing,
    and the policy shifts to 'remediate_persistent_weakness' at lowered difficulty.
    """
    state = InterviewState(difficulty=3, current_stage="role_technical", current_competency="backend")
    
    # Turn 1: misses distributed locking
    state.record_turn(
        question_id="q1",
        question_text="Q1",
        question_type="implementation",
        stage="role_technical",
        competency="backend",
        difficulty=3,
        score=45,
        missing_concepts=["distributed locking"]
    )
    assert state.concept_missing_counts.get("distributed locking") == 1
    assert "distributed locking" not in state.persistent_weaknesses

    # Turn 2: misses distributed locking again
    state.record_turn(
        question_id="q2",
        question_text="Q2",
        question_type="follow_up",
        stage="role_technical",
        competency="backend",
        difficulty=3,
        score=40,
        missing_concepts=["distributed locking"]
    )
    assert state.concept_missing_counts.get("distributed locking") == 2
    assert state.is_persistent_weakness("distributed locking") is True
    assert "distributed locking" in state.persistent_weaknesses
    assert state.mastery_levels.get("distributed locking") == ConceptMasteryLevel.REPEATEDLY_MISSING.value

    # Policy decision must target persistent weakness with remedial debugging question
    decision: PolicyDecision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.strategy == "remediate_persistent_weakness"
    assert "distributed locking" in decision.target_concepts
    assert decision.recommended_question_type in ["debugging", "conceptual"]
    assert decision.next_difficulty == 2


def test_recovered_weakness():
    """
    Verifies that when a candidate misses a concept in Turn 1 and subsequently demonstrates it in Turn 2,
    the concept is marked as recovered and removed from persistent weaknesses.
    """
    state = InterviewState(difficulty=3, current_stage="role_technical", current_competency="backend")

    # Turn 1: Misses SQL transactions
    state.record_turn(
        question_id="q1",
        question_text="Q1",
        question_type="implementation",
        stage="role_technical",
        competency="backend",
        difficulty=3,
        score=45,
        missing_concepts=["SQL transactions"]
    )
    assert "SQL transactions" in state.missing_concepts

    # Turn 2: Follow-up question, candidate answers well (score 85)
    state.record_turn(
        question_id="q2",
        question_text="Q2",
        question_type="follow_up",
        stage="role_technical",
        competency="backend",
        difficulty=3,
        score=85,
        covered_concepts=["SQL transactions"]
    )
    assert state.has_recovered("SQL transactions") is True
    assert "SQL transactions" in state.recovered_concepts
    assert "SQL transactions" in state.demonstrated_concepts
    assert "SQL transactions" not in state.missing_concepts


# -------------------------------------------------------------
# 3. Concept Prerequisite Graph Tests
# -------------------------------------------------------------

def test_prerequisite_missing_prevents_jumping_to_advanced_concept():
    """
    Verifies that if candidate misses an advanced concept (e.g. 'write amplification'),
    the system checks prerequisites ('B-Tree indexing'), finds it unverified,
    and sets strategy to 'reinforce_prerequisite' targeting 'B-Tree indexing' or 'indexing trade-offs'.
    """
    state = InterviewState(difficulty=3, current_stage="deep_dive", current_competency="database")
    
    # Candidate misses write amplification without having demonstrated B-Tree indexing
    state.record_turn(
        question_id="q1",
        question_text="Q1",
        question_type="trade_off",
        stage="deep_dive",
        competency="database",
        difficulty=3,
        score=52,
        missing_concepts=["write amplification"]
    )

    decision: PolicyDecision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    assert decision.strategy == "reinforce_prerequisite"
    assert decision.recommended_question_type == "conceptual"
    assert any(c in decision.target_concepts for c in ["B-Tree indexing", "indexing trade-offs"])
    assert "prerequisite" in decision.rationale.lower()


def test_prerequisite_mastered_allows_advanced_concept():
    """
    Verifies that if candidate has already demonstrated the prerequisites
    ('B-Tree indexing' and 'indexing trade-offs'), the system allows probing
    the advanced concept ('write amplification') directly with 'probe_missing_concept'.
    """
    state = InterviewState(difficulty=3, current_stage="deep_dive", current_competency="database")
    
    # Candidate previously mastered prerequisites
    state.demonstrated_concepts.append("B-Tree indexing")
    state.demonstrated_concepts.append("indexing trade-offs")

    # Now candidate exhibits a gap on write amplification
    state.record_turn(
        question_id="q1",
        question_text="Q1",
        question_type="trade_off",
        stage="deep_dive",
        competency="database",
        difficulty=3,
        score=55,
        missing_concepts=["write amplification"]
    )

    decision: PolicyDecision = AdaptiveInterviewPolicy.evaluate_next_step(state)
    # Since prerequisites are mastered, policy can probe the missing concept directly
    assert decision.strategy == "probe_missing_concept"
    assert decision.recommended_question_type == "follow_up"
    assert "write amplification" in decision.target_concepts
