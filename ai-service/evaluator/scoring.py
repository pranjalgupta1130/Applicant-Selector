"""
Deterministic answer scoring engine (Member 4 -- Evaluation & QA).

THE RULE THIS FILE ENFORCES (Master Plan RULE 4):
    The LLM never owns the final score.

The LLM supplies sub-scores only for what a language model can judge --
technical correctness, reasoning, clarity. Relevance, concept coverage,
completeness and the TOTAL are computed here by a fixed weighted formula over
numbers we can display and defend. `LLMSubScores` has no `total` field, so a
model that emits one cannot influence the aggregate.

If the LLM is unavailable (no key, timeout, malformed JSON) the engine degrades
to a fully deterministic path and says so. The interview never dead-ends.

Consumed by evaluator/real_evaluator.py, which adapts the result into the
shared core.schemas.EvaluationResult contract.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.config import settings
from core.schemas import QuestionObject

from .matching import (
    COVERAGE_THRESHOLD,
    ConceptMatch,
    coverage_ratio,
    match_concepts,
    semantic_similarity,
    tokenize,
)

logger = logging.getLogger(__name__)

# --- Master Plan Section 7.2 weights. Engineering defaults, configurable. ----
WEIGHTS: Dict[str, float] = {
    "relevance": 0.30,
    "technicalCorrectness": 0.30,
    "completeness": 0.20,
    "reasoning": 0.10,
    "clarity": 0.10,
}

MIN_SUBSTANTIVE_TOKENS = 8      # below this, nothing has been demonstrated
OFF_TOPIC_RELEVANCE = 35        # at or below, the answer is off-topic
NOVELTY_FLOOR = 0.45            # below this share of novel tokens, it's a restatement
INCORRECTNESS_PENALTY = 0.55    # applied when the LLM flags confident factual error

REFUSAL_PHRASES = (
    "i don't know", "i do not know", "no idea", "not sure", "unsure",
    "skip", "pass on this",
)


class LLMSubScores(BaseModel):
    """
    What the LLM is permitted to return: sub-scores and prose only.
    Deliberately has NO `total` field -- aggregation belongs to this module.
    """

    technicalCorrectness: int = Field(ge=0, le=100)
    reasoning: int = Field(ge=0, le=100)
    clarity: int = Field(ge=0, le=100)
    factuallyIncorrect: bool = False
    incorrectClaims: List[str] = Field(default_factory=list)
    feedback: str = ""
    confidence: float = Field(default=0.6, ge=0.0, le=1.0)


# ============================================================================
# Deterministic sub-scores
# ============================================================================

def answer_novelty(question: str, answer: str) -> float:
    """
    Share of the answer NOT lifted from the question. [0, 1]

    Guards the parrot case: "I would design a secure token-based system and
    handle revocation properly" is maximally similar to the question and says
    nothing. Similarity alone scores it ~92; novelty pulls it back.
    """
    q, a = set(tokenize(question)), tokenize(answer)
    if not a:
        return 0.0
    return len([t for t in a if t not in q]) / len(a)


def score_relevance(question: str, answer: str, matches: List[ConceptMatch]) -> int:
    """Is the answer about the question at all? 0-100, deterministic."""
    if not (answer or "").strip():
        return 0
    direct = semantic_similarity(question, answer)

    if matches:
        blended = 0.6 * direct + 0.4 * max((m.score for m in matches), default=0.0)
    else:
        # Ice-breakers carry no concept list, so there is no ground truth to
        # check against. Give a substantive attempt the benefit of the doubt
        # rather than failing it on surface wording; flagged downstream.
        blended = direct
        if len(tokenize(answer)) >= 25:
            blended = max(blended, 0.45)

    score = 100 * min(1.0, blended * 1.15)

    nov = answer_novelty(question, answer)
    if nov < NOVELTY_FLOOR:
        score *= 0.4 + 0.6 * (nov / NOVELTY_FLOOR)

    return int(round(max(0.0, min(100.0, score))))


def score_completeness(matches: List[ConceptMatch], answer: str) -> int:
    """How much of what was asked for is present. Concept coverage first."""
    if matches:
        return int(round(100 * coverage_ratio(matches)))
    n = len(tokenize(answer))
    if n < MIN_SUBSTANTIVE_TOKENS:
        return 15
    return min(70, int(round(35 + n * 0.6)))


def score_clarity_deterministic(answer: str) -> int:
    """Structure proxy, used only when the LLM is unavailable."""
    toks = tokenize(answer)
    n = len(toks)
    if n == 0:
        return 0
    if n < MIN_SUBSTANTIVE_TOKENS:
        return 25
    sentences = max(1, len(re.findall(r"[.!?]+", answer)))
    avg = n / sentences
    if avg > 45:
        return 45          # rambling, unpunctuated
    if avg < 4:
        return 50          # fragmentary
    base = 70
    if 60 <= n <= 220:
        base += 10
    if len(set(toks)) / n < 0.45:
        base -= 15         # heavy repetition / padding
    return max(0, min(100, base))


# ============================================================================
# LLM sub-scores (optional)
# ============================================================================

EVALUATOR_SYSTEM_PROMPT = """You grade ONE interview answer against ONE question.

Return ONLY valid JSON with exactly these keys:
{
  "technicalCorrectness": <0-100>,
  "reasoning": <0-100>,
  "clarity": <0-100>,
  "factuallyIncorrect": <true|false>,
  "incorrectClaims": ["..."],
  "feedback": "<2 sentences max: what was right, what was missing>",
  "confidence": <0.0-1.0>
}

RULES
1. Do NOT return a total or overall score. It is computed elsewhere.
2. A fluent, confident, well-structured answer that is TECHNICALLY WRONG must
   get a LOW technicalCorrectness and factuallyIncorrect=true. Fluency is not
   correctness. This is the failure mode you exist to catch.
3. Judge only against the question, expected concepts and rubric supplied. Do
   not invent requirements the question did not ask for.
4. Do not infer anything about the candidate as a person -- not personality,
   health, background, nor any protected attribute. Grade the answer only.
5. Off-topic answers get a low technicalCorrectness and a feedback line saying so.
6. Lower your confidence when the question is ambiguous or you are unsure.
"""


def _clean_and_parse_json(raw: str) -> Optional[dict]:
    """Parse a model response, tolerating code fences and surrounding prose."""
    if not raw:
        return None
    text = re.sub(r"^\s*```(?:json)?|```\s*$", "", raw.strip(), flags=re.MULTILINE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    depth, start = 0, None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    start = None
    return None


def call_llm_evaluator(
    question: QuestionObject, answer: str
) -> Optional[LLMSubScores]:
    """
    Request sub-scores from Gemini. Returns None on ANY failure -- missing key,
    network error, timeout, malformed JSON, schema violation. Callers degrade.

    Uses the same client pattern and settings as generator/pipeline.py.
    """
    if not settings.GEMINI_API_KEY:
        return None

    try:
        from google import genai
        from google.genai import types

        timeout_ms = int(settings.LLM_TIMEOUT_SECONDS * 1000)
        http_options = types.HttpOptions(timeout=timeout_ms)
        client = genai.Client(
            api_key=settings.GEMINI_API_KEY, http_options=http_options
        )

        user_prompt = f"""Grade this answer.

QUESTION: {question.text}
STAGE: {question.stage} | COMPETENCY: {question.competency} | DIFFICULTY: {question.difficulty}/5
EXPECTED CONCEPTS: {json.dumps(question.expectedConcepts)}
RUBRIC:
  poor: {question.rubric.poor}
  acceptable: {question.rubric.acceptable}
  excellent: {question.rubric.excellent}

CANDIDATE ANSWER:
{answer}

Respond with valid JSON according to the schema."""

        response = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents=[EVALUATOR_SYSTEM_PROMPT, user_prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,  # lower than generation: grading must be stable
                response_mime_type="application/json",
                http_options=http_options,
            ),
        )
        data = _clean_and_parse_json((response.text or "").strip())
    except Exception as exc:  # noqa: BLE001 -- any failure degrades, never raises
        logger.info("LLM evaluator unavailable, using deterministic path: %s", exc)
        return None

    if not data:
        logger.info("LLM evaluator returned unparseable output; deterministic path.")
        return None

    data.pop("total", None)        # belt and braces
    data.pop("score", None)
    try:
        return LLMSubScores(**data)
    except Exception as exc:  # noqa: BLE001
        logger.info("LLM evaluator output failed schema validation: %s", exc)
        return None


# ============================================================================
# Guards and aggregation
# ============================================================================

def _apply_guards(
    subs: Dict[str, Optional[int]],
    answer: str,
    llm: Optional[LLMSubScores],
    has_concepts: bool,
    stage: str = "core_technical"
) -> tuple[float, List[str]]:
    """
    Deterministic guardrails applied AFTER the stage-weighted sum.
    """
    valid_pairs = [(k, v) for k, v in subs.items() if v is not None]
    if valid_pairs:
        total = sum(v for _, v in valid_pairs) / len(valid_pairs)
    else:
        total = 50.0

    flags: List[str] = []

    if not has_concepts:
        flags.append("no_concept_ground_truth")

    lowered = (answer or "").lower().strip()
    if lowered and len(lowered) < 40 and any(p in lowered for p in REFUSAL_PHRASES):
        total = min(total, 25.0)
        flags.append("refusal")

    rel_val = subs.get("relevance") or subs.get("background_alignment") or 50
    if has_concepts and rel_val <= OFF_TOPIC_RELEVANCE:
        total = min(total, 30.0)
        flags.append("off_topic")

    if len(tokenize(answer)) < MIN_SUBSTANTIVE_TOKENS:
        total = min(total, 35.0)
        flags.append("insufficient_length")

    if llm is not None and llm.factuallyIncorrect and stage not in ("ice_breaker", "techno_managerial"):
        total *= INCORRECTNESS_PENALTY
        flags.append("factually_incorrect")

    comp_val = subs.get("completeness") or subs.get("experience_evidence") or 0
    if has_concepts and comp_val == 0 and rel_val < 60:
        total = min(total, 25.0)
        flags.append("no_concept_coverage")

    return max(0.0, min(100.0, total)), flags


def _strategy_hint(
    matches: List[ConceptMatch], total: float, flags: List[str]
) -> str:
    """
    Hint for the adaptive layer. Advisory only: adaptive/policy.py owns the
    actual decision -- this module does not choose the next question.
    """
    if "off_topic" in flags or "insufficient_length" in flags or "refusal" in flags:
        return "reask_simpler"
    if "factually_incorrect" in flags:
        return "correct_and_probe"
    if any(not m.covered for m in matches) and total < 75:
        return "probe_missing_concept"
    if total >= 80:
        return "increase_difficulty"
    return "continue"


def _deterministic_reasoning(
    matches: List[ConceptMatch], subs: Dict[str, Optional[int]], flags: List[str]
) -> str:
    covered = [m.concept for m in matches if m.covered]
    missing = [m.concept for m in matches if not m.covered and not m.partial]
    parts: List[str] = []
    if "refusal" in flags:
        parts.append("Candidate declined to answer substantively.")
    elif "off_topic" in flags:
        parts.append("The answer does not address the question asked.")
    elif "insufficient_length" in flags:
        parts.append("The answer is too brief to demonstrate understanding.")
    elif covered:
        parts.append("Demonstrated: " + ", ".join(covered[:4]) + ".")
    else:
        parts.append("None of the expected concepts were clearly addressed.")
    if missing:
        parts.append("Not addressed: " + ", ".join(missing[:4]) + ".")

    rel_score = subs.get("relevance") or subs.get("background_alignment") or 50
    parts.append(
        f"Relevance {rel_score}/100."
    )
    return " ".join(parts)


# ============================================================================
# Public entry point
# ============================================================================

def score_answer(
    question: QuestionObject, answer: str, use_llm: bool = True
) -> Dict[str, Any]:
    """
    Score one answer. Never raises; always returns a complete result dict.
    """
    text = (answer or "").strip()
    matches = match_concepts(text, question.expectedConcepts or [])

    relevance = score_relevance(question.text, text, matches)
    completeness = score_completeness(matches, text)

    llm = call_llm_evaluator(question, text) if (use_llm and text) else None

    if llm is not None:
        technical, reasoning_s, clarity = (
            llm.technicalCorrectness, llm.reasoning, llm.clarity
        )
        mode, confidence = "llm_assisted", llm.confidence
        reasoning = llm.feedback or ""
    else:
        technical = int(round(0.75 * completeness + 0.25 * relevance))
        reasoning_s = int(round(0.5 * (relevance + completeness) * 0.85))
        clarity = score_clarity_deterministic(text)
        mode, confidence, reasoning = "deterministic", 0.45, ""

    stg = (question.stage or "core_technical").lower().strip()

    if stg == "ice_breaker":
        subs = {
            "relevance": relevance,
            "background_alignment": relevance,
            "communication": clarity,
            "completeness": completeness,
            "technicalCorrectness": None
        }
    elif stg in ("applicant_validation", "expertise_validation"):
        subs = {
            "relevance": relevance,
            "experience_evidence": completeness,
            "specificity": clarity,
            "completeness": completeness,
            "technicalCorrectness": technical if question.expectedConcepts else None
        }
    elif stg == "deep_dive":
        subs = {
            "technicalCorrectness": technical,
            "reasoning": reasoning_s,
            "assumptions": completeness,
            "trade_offs": relevance,
            "depth": clarity
        }
    elif stg in ("application_scenario", "scenario"):
        subs = {
            "technicalCorrectness": technical,
            "problem_solving": reasoning_s,
            "reasoning": reasoning_s,
            "trade_offs": relevance,
            "practical_applicability": completeness
        }
    elif stg in ("system_engineering", "system_engineering_design"):
        subs = {
            "architecture": reasoning_s,
            "system_reasoning": technical,
            "interfaces": completeness,
            "trade_offs": relevance,
            "reliability": clarity,
            "technicalCorrectness": technical
        }
    elif stg in ("techno_managerial", "scenario_managerial"):
        subs = {
            "prioritization": reasoning_s,
            "leadership": relevance,
            "communication": clarity,
            "decision_making": completeness,
            "risk_management": technical,
            "technicalCorrectness": None
        }
    else: # core_technical
        subs = {
            "technicalCorrectness": technical,
            "completeness": completeness,
            "reasoning": reasoning_s,
            "depth": clarity,
            "relevance": relevance
        }

    total, flags = _apply_guards(subs, text, llm, has_concepts=bool(matches), stage=stg)

    if mode == "deterministic":
        flags.append("llm_unavailable_deterministic_scoring")
        reasoning = _deterministic_reasoning(matches, subs, flags)
    if llm is not None and llm.incorrectClaims:
        reasoning = (
            reasoning + " Incorrect claims: " + "; ".join(llm.incorrectClaims[:2])
        ).strip()

    return {
        "questionId": question.id,
        "subScores": subs,
        "total": int(round(total)),
        "coveredConcepts": [m.concept for m in matches if m.covered],
        "partialConcepts": [m.concept for m in matches if m.partial],
        "missingConcepts": [
            m.concept for m in matches if not m.covered and not m.partial
        ],
        "conceptDetail": [m.as_dict() for m in matches],
        "reasoning": reasoning or "No feedback generated.",
        "strategyHint": _strategy_hint(matches, total, flags),
        "confidence": round(float(confidence), 2),
        "scoreBreakdown": {
            "guardsApplied": flags,
            "finalTotal": round(total, 2),
            "coverageThreshold": COVERAGE_THRESHOLD,
            "scoringMode": mode,
        },
        "flags": flags,
        "mode": mode,
    }
