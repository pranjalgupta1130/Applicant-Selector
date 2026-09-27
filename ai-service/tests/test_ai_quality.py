import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from core.schemas import CandidateProfile, TargetRole, QuestionObject, RubricCriteria
from generator.pipeline import QuestionGeneratorPipeline, is_meta_question
from generator.fallback_bank import FallbackQuestionBank, FALLBACK_QUESTIONS, STAGE_ORDER
from evaluator.answer_evaluator import MockAnswerEvaluator, AnswerEvaluationAdapter
from adaptive.orchestrator import InterviewOrchestrator
from adaptive.state import InterviewState
from adaptive.scorecard_engine import ScorecardEngine


# ---------------------------------------------------------
# Test 1: Every stage has >= 4 fallback questions
# ---------------------------------------------------------
def test_1_fallback_questions_count_per_stage():
    required_keys = [
        "ice_breaker",
        "applicant_validation",
        "core_technical_electronics_radar",
        "core_technical_aerodynamics",
        "core_technical_cyber_computing",
        "deep_dive",
        "application_scenario",
        "system_engineering",
        "techno_managerial"
    ]
    for key in required_keys:
        assert key in FALLBACK_QUESTIONS, f"Missing fallback key: {key}"
        questions = FALLBACK_QUESTIONS[key]
        assert len(questions) >= 4, f"Stage key '{key}' has fewer than 4 fallback questions (got {len(questions)})"


# ---------------------------------------------------------
# Test 2: No fallback question is meta-interview phrasing
# ---------------------------------------------------------
def test_2_no_meta_interview_phrasing():
    for key, q_list in FALLBACK_QUESTIONS.items():
        for q in q_list:
            text = q["text"]
            assert not is_meta_question(text), f"Fallback question '{q['id']}' in key '{key}' has meta-interview phrasing: '{text}'"


# ---------------------------------------------------------
# Test 3: Ice breaker is candidate-directed
# ---------------------------------------------------------
def test_3_ice_breaker_candidate_directed():
    for q in FALLBACK_QUESTIONS["ice_breaker"]:
        text = q["text"].lower()
        assert any(word in text for word in ["you", "your", "could you", "tell us"]), f"Icebreaker '{q['id']}' is not candidate-directed: {q['text']}"
        assert not is_meta_question(q["text"])


# ---------------------------------------------------------
# Test 4: Same fallback question is never returned twice in a session
# ---------------------------------------------------------
def test_4_no_duplicate_fallback_questions_in_session():
    used_ids = set()
    used_questions = []

    for stage in STAGE_ORDER:
        q_obj = FallbackQuestionBank.get_fallback_question(
            stage=stage,
            domain="electronics_radar",
            used_ids=used_ids,
            used_questions=used_questions
        )
        assert q_obj.id not in used_ids, f"Duplicate fallback ID returned: {q_obj.id}"
        used_ids.add(q_obj.id)
        used_questions.append(q_obj.text)

    assert len(used_ids) == len(STAGE_ORDER)


# ---------------------------------------------------------
# Test 5: Interview progresses beyond ice_breaker
# ---------------------------------------------------------
def test_5_interview_progresses_beyond_ice_breaker():
    orchestrator = InterviewOrchestrator()
    candidate = CandidateProfile(
        skills=["Aerodynamics", "CFD", "Flight Dynamics"],
        experience_years=4.0
    )
    role = TargetRole(
        id="scientist_b_aero",
        title="Scientist 'B' - Aerodynamics",
        domain="aerodynamics"
    )

    start_res = orchestrator.start_interview(candidate=candidate, role=role)
    assert start_res.openingQuestion.stage == "ice_breaker"
    current_q = start_res.openingQuestion
    state = start_res.interviewState

    stages_seen = [current_q.stage]

    for turn_num in range(1, 7):
        turn_res = orchestrator.process_turn(
            current_question=current_q,
            candidate_answer="I applied computational fluid dynamics and aerodynamic lift analysis to project requirements.",
            interview_state=state,
            candidate=candidate,
            role=role
        )
        current_q = turn_res.nextQuestion
        if current_q is None or turn_res.termination.shouldTerminate:
            break
        stages_seen.append(current_q.stage)
        state = turn_res.updatedState

    assert "ice_breaker" in stages_seen
    assert len(set(stages_seen)) >= 4, f"Interview failed to progress across stages. Stages seen: {stages_seen}"
    assert stages_seen[0] == "ice_breaker"
    assert stages_seen[1] != "ice_breaker", f"Turn 2 remained in ice_breaker! Stages: {stages_seen}"


# ---------------------------------------------------------
# Test 6: Aerodynamics role gets aerodynamics questions
# ---------------------------------------------------------
def test_6_aerodynamics_role_gets_aerodynamics_questions():
    q_obj = FallbackQuestionBank.get_fallback_question(
        stage="core_technical",
        domain="aerodynamics"
    )
    text = q_obj.text.lower()
    aero_keywords = ["lift", "stall", "reynolds", "aerodynamic", "drag", "wing", "aircraft", "computational"]
    assert any(k in text for k in aero_keywords), f"Aerodynamics core technical question did not contain aero concepts: '{q_obj.text}'"


# ---------------------------------------------------------
# Test 7: Radar/DSP role gets radar/DSP questions
# ---------------------------------------------------------
def test_7_radar_role_gets_radar_questions():
    q_obj = FallbackQuestionBank.get_fallback_question(
        stage="core_technical",
        domain="electronics_radar"
    )
    text = q_obj.text.lower()
    radar_keywords = ["matched filter", "sampling", "doppler", "radar", "fft", "signal", "noise"]
    assert any(k in text for k in radar_keywords), f"Radar core technical question did not contain radar concepts: '{q_obj.text}'"


# ---------------------------------------------------------
# Test 8: Cyber role gets cyber questions
# ---------------------------------------------------------
def test_8_cyber_role_gets_cyber_questions():
    q_obj = FallbackQuestionBank.get_fallback_question(
        stage="core_technical",
        domain="cyber_computing"
    )
    text = q_obj.text.lower()
    cyber_keywords = ["security", "network", "authentication", "traffic", "data", "backend", "authorization"]
    assert any(k in text for k in cyber_keywords), f"Cyber core technical question did not contain cyber concepts: '{q_obj.text}'"


# ---------------------------------------------------------
# Test 9: Every fallback has expectedConcepts
# ---------------------------------------------------------
def test_9_every_fallback_has_expected_concepts():
    for key, q_list in FALLBACK_QUESTIONS.items():
        for q in q_list:
            concepts = q.get("expectedConcepts", [])
            assert isinstance(concepts, list), f"Expected concepts for '{q['id']}' must be a list"
            assert len(concepts) >= 2, f"Fallback '{q['id']}' in key '{key}' has fewer than 2 expected concepts"


# ---------------------------------------------------------
# Test 10: Every fallback has a rubric
# ---------------------------------------------------------
def test_10_every_fallback_has_rubric():
    for stage in STAGE_ORDER:
        q_obj = FallbackQuestionBank.get_fallback_question(
            stage=stage,
            domain="electronics_radar"
        )
        assert q_obj.rubric is not None
        assert q_obj.rubric.poor
        assert q_obj.rubric.acceptable
        assert q_obj.rubric.excellent


# ---------------------------------------------------------
# Test 11: Correct answer to a fallback gets a high score
# ---------------------------------------------------------
def test_11_correct_answer_gets_high_score():
    evaluator = MockAnswerEvaluator()
    q = QuestionObject(
        id="radar_core_1",
        text="What is the purpose of matched filtering in a radar receiver, and how does it affect target detection?",
        stage="core_technical",
        competency="radar_rf_systems",
        difficulty=3,
        expectedConcepts=["matched filter", "snr maximization", "known waveform", "target detection"],
        rubric=RubricCriteria(
            poor="Vague response lacking details.",
            acceptable="Mentions SNR maximization.",
            excellent="Explains correlation with known waveform to maximize signal to noise ratio for target detection."
        ),
        relevanceScore=95,
        sources=["chunk_drdo_radar_01"],
        isFallback=True
    )

    correct_answer = "The purpose of matched filtering in a radar receiver is to maximize the signal-to-noise ratio (SNR) by correlating the received signal with a known transmitted waveform, which significantly improves target detection capability in noise."
    result = evaluator.evaluate(q, correct_answer)

    assert result.score >= 80
    assert result.technicalCorrectness in ("accurate", "high")


# ---------------------------------------------------------
# Test 12: Incorrect answer gets a low score
# ---------------------------------------------------------
def test_12_incorrect_answer_gets_low_score():
    evaluator = MockAnswerEvaluator()
    q = QuestionObject(
        id="radar_core_1",
        text="What is the purpose of matched filtering in a radar receiver, and how does it affect target detection?",
        stage="core_technical",
        competency="radar_rf_systems",
        difficulty=3,
        expectedConcepts=["matched filter", "snr maximization", "known waveform", "target detection"],
        rubric=RubricCriteria(
            poor="Vague response lacking details.",
            acceptable="Mentions SNR maximization.",
            excellent="Explains correlation with known waveform to maximize signal to noise ratio for target detection."
        ),
        relevanceScore=95,
        sources=["chunk_drdo_radar_01"],
        isFallback=True
    )

    false_answer = "This topic is about web database backups, CSS styling, and frontend web server performance."
    result = evaluator.evaluate(q, false_answer)

    assert result.score <= 35
    assert result.technicalCorrectness == "inaccurate"


# ---------------------------------------------------------
# Test 13: Buzzword-only answer does not receive a high score
# ---------------------------------------------------------
def test_13_buzzword_only_answer_gets_low_score():
    evaluator = MockAnswerEvaluator()
    q = QuestionObject(
        id="radar_core_1",
        text="What is the purpose of matched filtering in a radar receiver, and how does it affect target detection?",
        stage="core_technical",
        competency="radar_rf_systems",
        difficulty=3,
        expectedConcepts=["matched filter", "snr maximization", "known waveform", "target detection"],
        rubric=RubricCriteria(
            poor="Vague response lacking details.",
            acceptable="Mentions SNR maximization.",
            excellent="Explains correlation with known waveform to maximize signal to noise ratio for target detection."
        ),
        relevanceScore=95,
        sources=["chunk_drdo_radar_01"],
        isFallback=True
    )

    buzzword_answer = "Matched filter SNR radar detection waveform signal noise."
    result = evaluator.evaluate(q, buzzword_answer)

    assert result.score <= 35
    assert result.technicalCorrectness == "inaccurate"
