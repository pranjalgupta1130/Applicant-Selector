"""
Golden test suite for the answer-evaluation subsystem (Member 4).

Every test pins use_llm=False, so results are deterministic and the suite passes
offline, in CI, and with no API key. The LLM path is exercised separately by
tools/calibrate.py.

    pytest tests/test_answer_evaluation.py -v
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))

from core.schemas import EvaluationResult, QuestionObject, RubricCriteria  # noqa: E402
from evaluator.answer_evaluator import AnswerEvaluationAdapter, MockAnswerEvaluator  # noqa: E402
from evaluator.real_evaluator import RealAnswerEvaluator, get_default_evaluator  # noqa: E402
from evaluator.scoring import WEIGHTS, LLMSubScores, score_answer  # noqa: E402

GOLDEN = json.loads((ROOT / "data" / "golden_answers.json").read_text())["cases"]

RUBRIC = RubricCriteria(
    poor="Does not address the expected concepts.",
    acceptable="Addresses the main concepts without depth.",
    excellent="Addresses all concepts with specifics and trade-offs.",
)

EVALUATOR = RealAnswerEvaluator(use_llm=False)


def _question(case: dict) -> QuestionObject:
    return QuestionObject(
        id=case["questionId"],
        text=case["questionText"],
        stage=case["stage"],
        competency=case["competency"],
        difficulty=case["difficulty"],
        expectedConcepts=case["expectedConcepts"],
        rubric=RUBRIC,
        relevanceScore=85,
    )


def _run(case: dict) -> EvaluationResult:
    return EVALUATOR.evaluate(_question(case), case["answerText"])


def _by_id(cid: str) -> dict:
    return next(c for c in GOLDEN if c["id"] == cid)


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", GOLDEN, ids=[c["id"] for c in GOLDEN])
def test_returns_valid_evaluation_result(case):
    """Never raises; always a complete, in-range EvaluationResult."""
    res = _run(case)
    assert isinstance(res, EvaluationResult)
    assert 0 <= res.score <= 100
    assert 0.0 <= res.confidence <= 1.0
    assert res.reasoning.strip(), "reasoning must never be empty"
    assert res.subScores is not None
    for field, value in res.subScores.model_dump().items():
        assert 0 <= value <= 100, f"{field}={value} out of range"


def test_satisfies_the_base_evaluator_interface():
    """Drops into AnswerEvaluationAdapter wherever the mock was used."""
    from evaluator.answer_evaluator import BaseAnswerEvaluator

    assert isinstance(EVALUATOR, BaseAnswerEvaluator)
    adapter = AnswerEvaluationAdapter(fallback_evaluator=EVALUATOR)
    case = _by_id("g01_strong")
    res = adapter.process_evaluation(_question(case), case["answerText"])
    assert isinstance(res, EvaluationResult)
    assert res.score > 0


def test_default_evaluator_is_still_the_mock():
    """
    Switching the closed loop onto the real engine must be a deliberate .env
    change (EVAL_USE_REAL=1), never a silent default flip mid-hackathon.
    """
    assert isinstance(get_default_evaluator(), MockAnswerEvaluator)


def test_adapter_still_defaults_to_mock_when_nothing_passed():
    """Existing orchestrator behaviour is unchanged by this subsystem."""
    assert isinstance(AnswerEvaluationAdapter().fallback_evaluator, MockAnswerEvaluator)


# ---------------------------------------------------------------------------
# Calibration bands
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", GOLDEN, ids=[c["id"] for c in GOLDEN])
def test_score_in_expected_band(case):
    """
    The score lands where a human would put it.

    Where the offline path is honestly blunter than the LLM path, the case
    carries expectBandDeterministic; we assert the band for the mode we ran in
    rather than loosening the real target so the fallback passes.
    """
    res = _run(case)
    lo, hi = case.get("expectBandDeterministic", case["expectBand"])
    assert lo <= res.score <= hi, (
        f"{case['id']} scored {res.score}, expected {lo}-{hi}. "
        f"flags={res.flags} | {case['why']}"
    )


# ---------------------------------------------------------------------------
# Discrimination -- the property that actually matters
# ---------------------------------------------------------------------------

def test_answers_rank_correctly():
    """A scorer that cannot rank answers is useless, however calibrated."""
    s = {c["id"]: _run(c).score for c in GOLDEN}
    assert s["g01_strong"] > s["g02_partial"], s
    assert s["g02_partial"] > s["g05_vague"], s
    assert s["g05_vague"] > s["g03_irrelevant"], s
    assert s["g01_strong"] > s["g07_too_short"], s


def test_parrot_scores_below_a_real_partial_answer():
    """Restating the question must not beat genuine partial understanding."""
    s = {c["id"]: _run(c).score for c in GOLDEN}
    assert s["g10_parrot"] < s["g02_partial"], s


def test_verbose_answer_is_not_treated_as_wrong():
    """Bad structure costs clarity only; coverage is still credited."""
    res = _run(_by_id("g06_verbose"))
    assert len(res.coveredConcepts) >= 2, res.coveredConcepts
    assert "off_topic" not in res.flags


def test_beats_the_mock_on_paraphrase():
    """
    Why this evaluator exists: the mock matches substrings, so a correct answer
    that paraphrases the expected concept is scored as a miss.
    """
    question = QuestionObject(
        id="q_paraphrase",
        text="How do you keep a leaked access token from being useful for long?",
        stage="role_technical",
        competency="backend",
        difficulty=3,
        expectedConcepts=["short-lived access tokens"],
        rubric=RUBRIC,
        relevanceScore=90,
    )
    answer = (
        "I keep the access token lifetime very short, around fifteen minutes, so "
        "a stolen token expires almost immediately and the client silently "
        "requests a fresh one."
    )
    real = EVALUATOR.evaluate(question, answer)
    mock = MockAnswerEvaluator().evaluate(question, answer)
    assert real.coveredConcepts, "real evaluator should credit the paraphrase"
    assert real.score > mock.score, (real.score, mock.score)


# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "case", [c for c in GOLDEN if "expectFlagsPresent" in c],
    ids=[c["id"] for c in GOLDEN if "expectFlagsPresent" in c],
)
def test_expected_flags_present(case):
    res = _run(case)
    for flag in case["expectFlagsPresent"]:
        assert flag in res.flags, f"expected {flag}, got {res.flags}"


@pytest.mark.parametrize(
    "case", [c for c in GOLDEN if "expectFlagsAbsent" in c],
    ids=[c["id"] for c in GOLDEN if "expectFlagsAbsent" in c],
)
def test_expected_flags_absent(case):
    res = _run(case)
    for flag in case["expectFlagsAbsent"]:
        assert flag not in res.flags, f"unexpected {flag} in {res.flags}"


def test_missing_concepts_are_reported():
    case = _by_id("g02_partial")
    res = _run(case)
    for concept in case["expectMissingIncludes"]:
        assert concept in res.missingConcepts + res.partialConcepts, (
            f"{concept} should be missing/partial; missing={res.missingConcepts} "
            f"partial={res.partialConcepts}"
        )


def test_empty_answer_is_safe():
    res = _run(_by_id("g08_empty"))
    assert res.score <= 5
    assert res.subScores.relevance == 0


def test_refusal_is_capped():
    question = _question(_by_id("g02_partial"))
    res = EVALUATOR.evaluate(question, "I don't know, skip this one.")
    assert "refusal" in res.flags
    assert res.score <= 30, res.score


def test_ice_breaker_without_concepts_still_scores():
    res = _run(_by_id("g09_no_expected_concepts"))
    assert res.score > 0, "an ice-breaker must not score zero"
    assert "no_concept_ground_truth" in res.flags


# ---------------------------------------------------------------------------
# Explainability -- what a judge will interrogate
# ---------------------------------------------------------------------------

def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_breakdown_reconstructs_the_total():
    """If a judge sums the contributions on screen, they get our number."""
    res = _run(_by_id("g01_strong"))
    b = res.scoreBreakdown
    assert abs(sum(b["weightedContributions"].values()) - b["rawWeightedSum"]) < 0.5
    if not b["guardsApplied"]:
        assert abs(b["rawWeightedSum"] - b["finalTotal"]) < 1.0


def test_llm_cannot_set_the_total():
    """RULE 4 enforced structurally: the sub-score schema has no total field."""
    assert "total" not in LLMSubScores.model_fields
    assert "score" not in LLMSubScores.model_fields
    assert not hasattr(
        LLMSubScores(technicalCorrectness=99, reasoning=99, clarity=99), "total"
    )


def test_concept_evidence_comes_from_the_answer():
    """Every covered concept cites the candidate's own sentence."""
    case = _by_id("g01_strong")
    res = _run(case)
    answer_lower = case["answerText"].lower()
    cited = [d for d in res.conceptDetail if d.covered and d.evidence]
    assert cited, "covered concepts must carry evidence"
    for detail in cited:
        assert detail.evidence.lower().strip(" .") in answer_lower


def test_scoring_is_deterministic():
    case = _by_id("g01_strong")
    assert _run(case).model_dump() == _run(case).model_dump()


def test_deterministic_mode_is_declared_honestly():
    """A fallback score is never presented as a full evaluation."""
    res = _run(_by_id("g01_strong"))
    assert res.evaluationMode == "deterministic"
    assert "llm_unavailable_deterministic_scoring" in res.flags


def test_confident_wrong_limitation_is_documented():
    """
    Locks in the honest finding: the deterministic path cannot detect a fluent,
    confidently incorrect answer. If this ever starts passing, the limitation has
    been fixed and the docs must be updated.
    """
    case = _by_id("g04_confident_wrong")
    assert case.get("requiresLlm") is True
    assert case.get("deterministicNote")
    assert "factually_incorrect" not in _run(case).flags


def test_incorrectness_penalty_applies_when_the_llm_flags_it():
    """The LLM path must actually move the number, not just add a flag."""
    case = _by_id("g04_confident_wrong")
    question = _question(case)
    baseline = score_answer(question, case["answerText"], use_llm=False)

    import evaluator.scoring as scoring

    original = scoring.call_llm_evaluator
    scoring.call_llm_evaluator = lambda q, a: LLMSubScores(
        technicalCorrectness=10,
        reasoning=30,
        clarity=80,
        factuallyIncorrect=True,
        incorrectClaims=["claims an index is a cached copy of the table in RAM"],
        feedback="Fluent but wrong on every claim.",
        confidence=0.9,
    )
    try:
        flagged = score_answer(question, case["answerText"], use_llm=True)
    finally:
        scoring.call_llm_evaluator = original

    assert "factually_incorrect" in flagged["flags"]
    assert flagged["total"] < baseline["total"], (flagged["total"], baseline["total"])
    assert flagged["total"] <= case["expectBand"][1], flagged["total"]
    assert flagged["strategyHint"] == "correct_and_probe"


def test_malformed_llm_output_degrades_to_deterministic():
    """Garbage from the model must not crash or poison the score."""
    import evaluator.scoring as scoring

    case = _by_id("g01_strong")
    question = _question(case)
    original = scoring.call_llm_evaluator
    scoring.call_llm_evaluator = lambda q, a: None  # simulates unparseable output
    try:
        res = score_answer(question, case["answerText"], use_llm=True)
    finally:
        scoring.call_llm_evaluator = original

    assert res["mode"] == "deterministic"
    assert 0 <= res["total"] <= 100


# ---------------------------------------------------------------------------
# Adaptive hand-off
# ---------------------------------------------------------------------------

def test_strategy_hint_is_advisory_and_sane():
    assert _run(_by_id("g07_too_short")).strategyHint == "reask_simpler"
    assert _run(_by_id("g02_partial")).strategyHint in (
        "probe_missing_concept", "correct_and_probe", "continue",
    )
