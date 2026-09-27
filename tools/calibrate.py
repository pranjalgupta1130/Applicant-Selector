"""
Calibration runner for the answer-evaluation subsystem.

Produces the table to put on the Q&A slide. Run it BEFORE the presentation: when
a judge asks "where does that score come from" or "what is your accuracy", this
output is the answer.

    python tools/calibrate.py                  # deterministic, offline
    python tools/calibrate.py --llm            # LLM path (needs GEMINI_API_KEY)
    python tools/calibrate.py --llm --runs 3   # also measures run-to-run spread
    python tools/calibrate.py --compare-mock   # real engine vs the mock evaluator
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))

from core.schemas import QuestionObject, RubricCriteria  # noqa: E402
from evaluator.answer_evaluator import MockAnswerEvaluator  # noqa: E402
from evaluator.matching import embedding_backend_available  # noqa: E402
from evaluator.real_evaluator import RealAnswerEvaluator  # noqa: E402

CASES = json.loads((ROOT / "data" / "golden_answers.json").read_text())["cases"]

RUBRIC = RubricCriteria(
    poor="Does not address the expected concepts.",
    acceptable="Addresses the main concepts without depth.",
    excellent="Addresses all concepts with specifics and trade-offs.",
)


def question_of(case: dict) -> QuestionObject:
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true", help="use the LLM path")
    ap.add_argument("--runs", type=int, default=1, help="repeat for consistency")
    ap.add_argument("--compare-mock", action="store_true",
                    help="also score with MockAnswerEvaluator for comparison")
    args = ap.parse_args()

    evaluator = RealAnswerEvaluator(use_llm=args.llm)
    mock = MockAnswerEvaluator()
    mode = "LLM-assisted" if args.llm else "Deterministic (offline)"

    print()
    print("=" * 100)
    print(f"  ANSWER EVALUATION CALIBRATION  |  mode: {mode}  |  runs: {args.runs}")
    print("  embedding backend: "
          f"{'sentence-transformers' if embedding_backend_available() else 'lexical fallback'}")
    print("=" * 100)
    header = f"{'case':<26}{'score':>8}{'band':>11}{'ok':>5}"
    if args.compare_mock:
        header += f"{'mock':>7}"
    print(header + "  flags")
    print("-" * 100)

    failures, spreads = [], []

    for case in CASES:
        q = question_of(case)
        totals, last = [], None
        for _ in range(max(1, args.runs)):
            last = evaluator.evaluate(q, case["answerText"])
            totals.append(last.score)

        band = (case["expectBand"] if args.llm
                else case.get("expectBandDeterministic", case["expectBand"]))
        mean = round(statistics.mean(totals))
        ok = band[0] <= mean <= band[1]
        if not ok:
            failures.append((case["id"], mean, band))
        spread = max(totals) - min(totals)
        if args.runs > 1:
            spreads.append((case["id"], spread))

        shown = f"{mean}" + (f" +/-{spread}" if args.runs > 1 else "")
        row = f"{case['id']:<26}{shown:>8}{f'{band[0]}-{band[1]}':>11}{'OK' if ok else 'OUT':>5}"
        if args.compare_mock:
            row += f"{mock.evaluate(q, case['answerText']).score:>7}"
        print(row + "  " + ",".join(last.flags[:2]))

    print("-" * 100)
    print(f"  in band: {len(CASES) - len(failures)}/{len(CASES)}")
    for cid, got, band in failures:
        print(f"    OUT  {cid}: {got} (expected {band[0]}-{band[1]})")

    if spreads:
        worst = max(spreads, key=lambda x: x[1])
        print(f"  consistency: worst spread {worst[1]} points on {worst[0]}")
        print("    (above ~8 means the LLM is too unstable to quote an exact number --")
        print("     lower the temperature or report the range instead)")

    print()
    print("  SAY THESE OUT LOUD IN Q&A:")
    for case in CASES:
        if case.get("deterministicNote"):
            print(f"    - {case['id']}: {case['deterministicNote'][:160]}")
    print("    - Bands, not exact numbers: no labelled ground-truth dataset exists for")
    print("      interview scoring, so we assert ranges a human would agree with.")
    print("    - The LLM never sets the total. Sub-scores in, fixed weights out.")
    print()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
