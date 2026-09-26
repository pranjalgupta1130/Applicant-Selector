"""
Closed-Loop Adaptive Interview Engine Test Suite (Phase C — BoardRoom AI).
Comprehensive verification of all 20 required behaviors:
 1. Successful answer -> state update
 2. Weak answer -> missing concept propagation
 3. Persistent weakness -> remediation
 4. Prerequisite gap -> prerequisite question
 5. Strong streak -> difficulty increase
 6. Declining trend -> difficulty calibration
 7. Recovered concept -> mastery update
 8. Question deduplication
 9. Target concept reaches RAG
10. Decision trace correctness
11. Deterministic fallback
12. Malformed evaluator output handling
13. Malformed question generation handling
14. Termination logic
15. Evidence confidence
16. Complete multi-turn strong simulation
17. Complete multi-turn weak simulation
18. Strong -> Weak -> Recovery simulation
19. Specialist simulation
20. Frozen QuestionObject contract
"""

import sys
from pathlib import Path
from unittest.mock import patch
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
    EvaluationResult,
    TurnResponse,
    InterviewStartResponse
)
from adaptive.state import InterviewState, ConceptMasteryLevel
from adaptive.orchestrator import InterviewOrchestrator
from adaptive.target_concept import TargetConceptSelector
from adaptive.confidence import EvidenceConfidenceTracker
from adaptive.termination import InterviewTerminationEngine
from adaptive.simulator import (
    ClosedLoopInterviewSimulator,
    run_strong_candidate_simulation,
    run_weak_candidate_simulation,
    run_recovery_candidate_simulation,
    run_specialist_candidate_simulation
)
from evaluator.answer_evaluator import MockAnswerEvaluator, AnswerEvaluationAdapter

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


def create_sample_question(
    q_id="q_sample_01",
    stage="role_technical",
    competency="backend",
    difficulty=3,
    expected_concepts=None
) -> QuestionObject:
    """Helper creating a valid QuestionObject strictly satisfying frozen contract."""
    return QuestionObject(
        id=q_id,
        text="Explain how JWT authentication works and how refresh tokens mitigate session hijack?",
        stage=stage,
        competency=competency,
        difficulty=difficulty,
        expectedConcepts=expected_concepts or ["JWT authentication", "refresh token rotation"],
        rubric=RubricCriteria(
            poor="Lacks understanding of JWT signing and claims.",
            acceptable="Explains headers, payload, and signature with basic expiration.",
            excellent="Explains cryptographic signatures, rotation strategies, and replay attack prevention."
        ),
        relevanceScore=88,
        sources=["chunk_auth_01"],
        isFallback=False,
        questionType="conceptual"
    )


# =====================================================================
# 1. Successful Answer -> State Update
# =====================================================================
def test_successful_answer_state_update():
    orchestrator = InterviewOrchestrator()
    question = create_sample_question()
    answer = "JWT uses signed tokens with headers, payload, and HMAC/RSA signature. Refresh token rotation prevents session hijack."

    turn_res: TurnResponse = orchestrator.process_turn(
        current_question=question,
        candidate_answer=answer,
        evaluation=EvaluationResult(
            score=88,
            coveredConcepts=["JWT authentication", "refresh token rotation"],
            missingConcepts=[],
            reasoning="Strong demonstration of authentication concepts."
        )
    )

    state = turn_res.updatedState
    assert state["score_history"] == [88]
    assert "JWT authentication" in state["demonstrated_concepts"]
    assert "refresh token rotation" in state["demonstrated_concepts"]
    assert state["mastery_levels"]["JWT authentication"] == ConceptMasteryLevel.DEMONSTRATED_ONCE.value
    assert state["consecutive_strong_count"] == 1
    assert state["consecutive_weak_count"] == 0


# =====================================================================
# 2. Weak Answer -> Missing Concept Propagation
# =====================================================================
def test_weak_answer_missing_concept_propagation():
    orchestrator = InterviewOrchestrator()
    question = create_sample_question()
    answer = "I'm not completely sure about tokens."

    turn_res: TurnResponse = orchestrator.process_turn(
        current_question=question,
        candidate_answer=answer,
        evaluation=EvaluationResult(
            score=42,
            coveredConcepts=[],
            missingConcepts=["JWT authentication", "refresh token rotation"],
            reasoning="Candidate omitted core authentication mechanisms."
        )
    )

    state = turn_res.updatedState
    assert state["score_history"] == [42]
    assert "JWT authentication" in state["missing_concepts"]
    assert "refresh token rotation" in state["missing_concepts"]
    assert state["concept_missing_counts"]["JWT authentication"] == 1
    assert turn_res.decision.strategy in ("probe_missing_concept", "reinforce_fundamentals")
    assert any(c in turn_res.decision.targetConcepts for c in ["JWT authentication", "refresh token rotation"])


# =====================================================================
# 3. Persistent Weakness -> Remediation
# =====================================================================
def test_persistent_weakness_remediation():
    orchestrator = InterviewOrchestrator()
    question = create_sample_question()

    # Pre-populate state with an existing weakness in "concurrency race conditions"
    state = InterviewState(
        difficulty=3,
        current_stage="role_technical",
        current_competency="backend"
    )
    # Turn 1: Misses concept
    state.record_turn(
        question_id="q1",
        question_text="Q1",
        question_type="conceptual",
        stage="role_technical",
        competency="backend",
        difficulty=3,
        score=45,
        missing_concepts=["concurrency race conditions"]
    )
    # Turn 2: Misses concept again -> persistent weakness
    state.record_turn(
        question_id="q2",
        question_text="Q2",
        question_type="implementation",
        stage="role_technical",
        competency="backend",
        difficulty=3,
        score=48,
        missing_concepts=["concurrency race conditions"]
    )

    assert state.is_persistent_weakness("concurrency race conditions") is True

    turn_res: TurnResponse = orchestrator.process_turn(
        current_question=question,
        candidate_answer="Still confused about concurrency.",
        interview_state=state,
        evaluation=EvaluationResult(
            score=45,
            coveredConcepts=[],
            missingConcepts=["concurrency race conditions"]
        )
    )

    assert turn_res.decision.strategy == "remediate_persistent_weakness"
    assert turn_res.decision.targetConcepts == ["concurrency race conditions"]
    assert turn_res.decision.nextDifficulty < 3
    assert "persistent weakness" in turn_res.decision.reason.lower()


# =====================================================================
# 4. Prerequisite Gap -> Prerequisite Question
# =====================================================================
def test_prerequisite_gap_prerequisite_question():
    orchestrator = InterviewOrchestrator()
    adv_question = create_sample_question(
        expected_concepts=["write amplification"]
    )

    state = InterviewState(
        difficulty=3,
        current_stage="role_technical",
        current_competency="database"
    )

    # Candidate misses advanced concept "write amplification" without mastering "B-Tree indexing"
    turn_res: TurnResponse = orchestrator.process_turn(
        current_question=adv_question,
        candidate_answer="I don't know write amplification.",
        interview_state=state,
        evaluation=EvaluationResult(
            score=40,
            coveredConcepts=[],
            missingConcepts=["write amplification"]
        )
    )

    assert turn_res.decision.strategy == "reinforce_prerequisite"
    assert "B-Tree indexing" in turn_res.decision.targetConcepts or "indexing trade-offs" in turn_res.decision.targetConcepts
    assert turn_res.decision.nextDifficulty <= 2
    assert "prerequisite" in turn_res.decision.reason.lower()


# =====================================================================
# 5. Strong Streak -> Difficulty Increase
# =====================================================================
def test_strong_streak_difficulty_increase():
    orchestrator = InterviewOrchestrator()
    question = create_sample_question(difficulty=2)

    state = InterviewState(
        difficulty=2,
        current_stage="role_technical",
        current_competency="backend"
    )
    # Turn 1: score 88
    state.record_turn("q1", "Q1 text", "conceptual", "role_technical", "backend", 2, score=88, covered_concepts=["REST"])

    # Turn 2: score 92 (consecutive strong count becomes 2)
    turn_res: TurnResponse = orchestrator.process_turn(
        current_question=question,
        candidate_answer="Excellent answer on authentication and session security.",
        interview_state=state,
        evaluation=EvaluationResult(
            score=92,
            coveredConcepts=["JWT authentication", "refresh token rotation"]
        )
    )

    assert turn_res.decision.nextDifficulty == 3
    assert "strong" in turn_res.decision.reason.lower() or "escalat" in turn_res.decision.reason.lower()


# =====================================================================
# 6. Declining Trend -> Difficulty Calibration
# =====================================================================
def test_declining_trend_difficulty_calibration():
    orchestrator = InterviewOrchestrator()
    question = create_sample_question(difficulty=4)

    state = InterviewState(
        difficulty=4,
        current_stage="deep_dive",
        current_competency="system_design"
    )
    # Turn 1: 85
    state.record_turn("q1", "Q1", "design", "deep_dive", "system_design", 4, score=85, covered_concepts=["caching"])
    # Turn 2: 60
    state.record_turn("q2", "Q2", "design", "deep_dive", "system_design", 4, score=60, covered_concepts=["sharding"])

    # Turn 3: 45 -> trend drops to declining
    turn_res: TurnResponse = orchestrator.process_turn(
        current_question=question,
        candidate_answer="Struggling with high availability.",
        interview_state=state,
        evaluation=EvaluationResult(
            score=45,
            coveredConcepts=[],
            missingConcepts=["high availability"]
        )
    )

    assert turn_res.trace.trend == "declining"
    assert turn_res.decision.nextDifficulty < 4
    assert "declining" in turn_res.decision.reason.lower() or "reduc" in turn_res.decision.reason.lower() or "calibrat" in turn_res.decision.reason.lower()


# =====================================================================
# 7. Recovered Concept -> Mastery Update
# =====================================================================
def test_recovered_concept_mastery_update():
    orchestrator = InterviewOrchestrator()
    question = create_sample_question()

    state = InterviewState(
        difficulty=3,
        current_stage="role_technical",
        current_competency="backend"
    )
    # Candidate previously missed "JWT authentication"
    state.record_turn("q1", "Q1", "conceptual", "role_technical", "backend", 3, score=45, missing_concepts=["JWT authentication"])
    assert "JWT authentication" in state.missing_concepts

    # Now demonstrates it with score 86
    turn_res: TurnResponse = orchestrator.process_turn(
        current_question=question,
        candidate_answer="Comprehensive breakdown of JWT signing, claims, expiration, and refresh tokens.",
        interview_state=state,
        evaluation=EvaluationResult(
            score=86,
            coveredConcepts=["JWT authentication"],
            missingConcepts=[]
        )
    )

    updated_state = turn_res.updatedState
    assert "JWT authentication" in updated_state["recovered_concepts"]
    assert "JWT authentication" not in updated_state["missing_concepts"]
    assert "JWT authentication" in updated_state["demonstrated_concepts"]


# =====================================================================
# 8. Question Deduplication
# =====================================================================
def test_question_deduplication():
    orchestrator = InterviewOrchestrator()
    question1 = create_sample_question(q_id="q1")

    state = InterviewState(difficulty=2, current_stage="fundamentals", current_competency="backend")

    turn1 = orchestrator.process_turn(
        current_question=question1,
        candidate_answer="Standard answer.",
        interview_state=state,
        evaluation=EvaluationResult(score=80, coveredConcepts=["HTTP status codes"])
    )

    q2 = turn1.nextQuestion
    assert q2 is not None
    assert q2.text != question1.text
    assert q2.id != question1.id


# =====================================================================
# 9. Target Concept Reaches RAG
# =====================================================================
def test_target_concept_reaches_rag():
    orchestrator = InterviewOrchestrator()
    question = create_sample_question(expected_concepts=["database transactions"])

    state = InterviewState(difficulty=3, current_stage="role_technical", current_competency="database")

    # Force a missing concept that should be targeted next
    turn_res = orchestrator.process_turn(
        current_question=question,
        candidate_answer="I don't know ACID.",
        interview_state=state,
        evaluation=EvaluationResult(score=40, coveredConcepts=[], missingConcepts=["database transactions"])
    )

    # Next question must be generated focusing on database / transactions
    assert turn_res.nextQuestion is not None
    assert turn_res.decision.targetConcepts == ["database transactions"]
    assert "database transactions" in turn_res.nextQuestion.adaptiveReason or "database" in turn_res.nextQuestion.competency


# =====================================================================
# 10. Decision Trace Correctness
# =====================================================================
def test_decision_trace_correctness():
    orchestrator = InterviewOrchestrator()
    question = create_sample_question()

    turn_res = orchestrator.process_turn(
        current_question=question,
        candidate_answer="Technical response.",
        evaluation=EvaluationResult(
            score=54,
            coveredConcepts=["REST APIs"],
            missingConcepts=["JWT authentication"]
        )
    )

    trace = turn_res.trace
    assert trace.previousScore == 54
    assert trace.strategy is not None
    assert trace.nextDifficulty in [1, 2, 3, 4, 5]
    assert trace.questionType in ["conceptual", "implementation", "debugging", "trade_off", "scenario", "design", "follow_up"]
    assert len(trace.reason) > 20
    # Must NOT be generic boilerplate
    assert "based on the candidate's performance..." not in trace.reason.lower()
    # Must contain actual score or concept
    assert "54" in trace.reason or "jwt" in trace.reason.lower() or "rest" in trace.reason.lower()


# =====================================================================
# 11. Deterministic Fallback on Generation Outage
# =====================================================================
def test_deterministic_fallback():
    orchestrator = InterviewOrchestrator()
    question = create_sample_question()

    with patch.object(orchestrator.generator, "_generate_with_gemini", side_effect=RuntimeError("Simulated LLM 503 Outage")):
        turn_res = orchestrator.process_turn(
            current_question=question,
            candidate_answer="Valid answer.",
            evaluation=EvaluationResult(score=80, coveredConcepts=["JWT authentication"])
        )

        assert turn_res.nextQuestion is not None
        assert turn_res.nextQuestion.isFallback is True
        assert len(turn_res.nextQuestion.expectedConcepts) >= 1
        assert turn_res.nextQuestion.rubric.poor != ""


# =====================================================================
# 12. Malformed Evaluator Output Handling
# =====================================================================
def test_malformed_evaluator_output_handling():
    adapter = AnswerEvaluationAdapter()
    question = create_sample_question()

    # Case 1: string score and missing keys
    malformed_dict = {
        "score": "not_an_int",
        "missingConcepts": "invalid_string_not_list",
        "confidence": "2.5"  # out of bounds
    }
    result = adapter.process_evaluation(question, "answer", malformed_dict)
    assert 0 <= result.score <= 100
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.missingConcepts, list)

    # Case 2: negative score
    result2 = adapter.process_evaluation(question, "answer", {"score": -50})
    assert result2.score == 0


# =====================================================================
# 13. Malformed Question Generation Handling
# =====================================================================
def test_malformed_question_generation_handling():
    orchestrator = InterviewOrchestrator()
    question = create_sample_question()

    # Force generator.generate to raise
    with patch.object(orchestrator.generator, "generate", side_effect=Exception("Generator network timeout")):
        turn_res = orchestrator.process_turn(
            current_question=question,
            candidate_answer="Candidate answer.",
            evaluation=EvaluationResult(score=75, coveredConcepts=["JWT authentication"])
        )
        assert turn_res.nextQuestion is not None
        assert turn_res.nextQuestion.isFallback is True


# =====================================================================
# 14. Termination Logic
# =====================================================================
def test_termination_logic():
    # Case 1: Early turn (< 4 turns) should NOT terminate
    state_early = InterviewState(difficulty=2)
    state_early.record_turn("q1", "Q1", "conceptual", "ice_breaker", "ice_breaker", 1, score=85)
    term_early = InterviewTerminationEngine.evaluate_termination(state_early)
    assert term_early.shouldTerminate is False
    assert "minimum interview depth" in term_early.reason.lower()

    # Case 2: Safety cap reached (>= 8 turns) MUST terminate
    state_capped = InterviewState(difficulty=3)
    for i in range(8):
        state_capped.record_turn(f"q{i}", f"Q{i}", "conceptual", "role_technical", "backend", 3, score=80)
    term_capped = InterviewTerminationEngine.evaluate_termination(state_capped)
    assert term_capped.shouldTerminate is True
    assert "safety cap" in term_capped.reason.lower()


# =====================================================================
# 15. Evidence Confidence
# =====================================================================
def test_evidence_confidence():
    state = InterviewState(difficulty=2)
    # Turn 1: Demonstrated once in conceptual fundamentals
    state.record_turn("q1", "Q1", "conceptual", "fundamentals", "backend", 2, score=85, covered_concepts=["REST"])
    conf_1 = EvidenceConfidenceTracker.compute_concept_confidence(state)
    assert 0.40 <= conf_1["REST"] <= 0.60

    # Turn 2: Demonstrated again in implementation role_technical
    state.record_turn("q2", "Q2", "implementation", "role_technical", "backend", 3, score=90, covered_concepts=["REST"])
    conf_2 = EvidenceConfidenceTracker.compute_concept_confidence(state)
    assert conf_2["REST"] > conf_1["REST"]
    assert conf_2["REST"] >= 0.75

    coverage = EvidenceConfidenceTracker.compute_evidence_coverage(state)
    assert 0.0 <= coverage <= 1.0


# =====================================================================
# 16. Complete Multi-Turn Strong Simulation
# =====================================================================
def test_complete_multi_turn_strong_simulation():
    res = run_strong_candidate_simulation()
    assert res["turns_completed"] >= 4
    # Difficulty should escalate
    assert max(res["difficulty_trend"]) >= 3
    # Candidate achieved strong scores
    assert all(s >= 80 for s in res["score_history"])
    # No persistent weaknesses
    assert len(res["persistent_weaknesses"]) == 0


# =====================================================================
# 17. Complete Multi-Turn Weak Simulation
# =====================================================================
def test_complete_multi_turn_weak_simulation():
    res = run_weak_candidate_simulation()
    assert res["turns_completed"] >= 4
    # Difficulty calibrated down/held low
    assert res["final_difficulty"] <= 2
    # Missing concepts were recorded
    assert len(res["missing_concepts"]) > 0


# =====================================================================
# 18. Strong -> Weak -> Recovery Simulation
# =====================================================================
def test_strong_weak_recovery_simulation():
    res = run_recovery_candidate_simulation()
    assert res["turns_completed"] >= 5
    # Must have recovered concepts
    assert len(res["recovered_concepts"]) > 0
    # Final score history matches trajectory
    assert res["score_history"][-1] >= 80


# =====================================================================
# 19. Specialist Simulation
# =====================================================================
def test_specialist_simulation():
    res = run_specialist_candidate_simulation()
    assert res["turns_completed"] >= 4
    # Should demonstrate backend concepts
    assert "REST APIs" in res["demonstrated_concepts"] or "idempotency" in res["demonstrated_concepts"]
    # Should demonstrate database concepts
    assert "B-Tree indexing" in res["demonstrated_concepts"] or "database transactions" in res["demonstrated_concepts"]
    # Check that system design turns were probed
    sd_turns = [
        t for t in res["turns"]
        if "system_design" in t["question_asked"]["competency"] or
        any(c in t["decision"]["target_concepts"] for c in ["horizontal scaling", "load balancing", "distributed locking"])
    ]
    assert len(sd_turns) >= 1



# =====================================================================
# 20. Frozen QuestionObject Contract
# =====================================================================
def test_frozen_question_object_contract_in_api():
    # 1. Start interview endpoint
    res_start = client.post("/api/interview/start", json={})
    assert res_start.status_code == 200
    data_start = res_start.json()
    assert "interviewState" in data_start
    assert "openingQuestion" in data_start
    q_start = data_start["openingQuestion"]
    for field in FROZEN_CONTRACT_FIELDS:
        assert field in q_start, f"Missing frozen contract field '{field}' in opening question"

    # 2. Complete turn endpoint
    payload_turn = {
        "currentQuestion": q_start,
        "candidateAnswer": "I have 4 years of experience building Python and FastAPI REST services with PostgreSQL.",
        "interviewState": data_start["interviewState"],
        "evaluation": {
            "score": 85,
            "coveredConcepts": ["software architecture overview"],
            "missingConcepts": [],
            "reasoning": "Clear, grounded background presentation.",
            "confidence": 0.90
        }
    }

    res_turn = client.post("/api/interview/turn", json=payload_turn)
    assert res_turn.status_code == 200
    data_turn = res_turn.json()

    assert "updatedState" in data_turn
    assert "evaluation" in data_turn
    assert "decision" in data_turn
    assert "termination" in data_turn
    assert "trace" in data_turn

    if data_turn["nextQuestion"]:
        next_q = data_turn["nextQuestion"]
        for field in FROZEN_CONTRACT_FIELDS:
            assert field in next_q, f"Missing frozen contract field '{field}' in next question"
        # Rubric consistency: poor, acceptable, excellent
        assert "poor" in next_q["rubric"]
        assert "acceptable" in next_q["rubric"]
        assert "excellent" in next_q["rubric"]
