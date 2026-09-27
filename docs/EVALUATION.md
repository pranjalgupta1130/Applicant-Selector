# Answer Evaluation Subsystem (Member 4)

Answer scoring, concept coverage, guardrails and the golden test set for
**BoardRoom AI / PSWB01**. Consumes what the RAG subsystem (Member 3) produces:
a `QuestionObject` with `expectedConcepts` and a `rubric` goes in, an
`EvaluationResult` comes out.

## Boundaries

| Owner | Responsibility |
|---|---|
| Member 3 (RAG) | Retrieval, question generation, `expectedConcepts`, `rubric`, **question** relevance |
| **Member 4 (this subsystem)** | **Answer scoring, concept coverage, guardrails, golden tests, demo reliability** |
| Member 2 (Backend) | Calls `/api/ai/evaluate-answer`, or passes `evaluation` into `/api/interview/turn` |
| Member 1 (Frontend) | Renders `score`, `subScores`, `conceptDetail`, `scoreBreakdown` |

This subsystem does **not** generate questions and does **not** decide the next
one. It emits an advisory `strategyHint`; `adaptive/policy.py` owns the decision.

## Where it plugs in

`evaluator/answer_evaluator.py` already defined the seam — `BaseAnswerEvaluator`,
with `MockAnswerEvaluator` as a placeholder so the adaptive pipeline could be
built before this subsystem existed. `RealAnswerEvaluator` implements the same
interface, so it drops in with no changes to the orchestrator:

```python
from evaluator.answer_evaluator import AnswerEvaluationAdapter
from evaluator.real_evaluator import RealAnswerEvaluator

adapter = AnswerEvaluationAdapter(fallback_evaluator=RealAnswerEvaluator())
```

**The mock is still the default.** `get_default_evaluator()` and a bare
`AnswerEvaluationAdapter()` both return it unless `EVAL_USE_REAL=1` is set, so
switching the closed loop over is a deliberate `.env` change rather than a
silent flip under someone else's work mid-hackathon. Two tests assert that.

### Why not keep the mock

The mock matches concepts by substring, so a correct paraphrase reads as a miss,
and its score is a coverage ladder with no guardrails. Deterministic mode, same
golden cases, real engine vs mock:

| case | real | mock | what the mock gets wrong |
|---|---|---|---|
| g10_parrot | **38** | 56 | scores a restatement of the question like a real answer |
| g07_too_short | **23** | 44 | "Index is faster." passes as partial understanding |
| g08_empty | **0** | 25 | an empty answer earns 25 |
| g05_vague | **49** | 56 | ranks a vague answer level with a confident wrong one |
| g03_irrelevant | **11** | 30 | off-topic answer is not capped |

Reproduce with `python tools/calibrate.py --compare-mock`.

---

## The rule this subsystem enforces

> **The LLM never owns the final score.** (Master Plan RULE 4)

The LLM returns sub-scores for what only a language model can judge — technical
correctness, reasoning, clarity. Relevance, concept coverage, completeness and
**the total** are computed by a fixed weighted formula over numbers we can put
on a slide.

Enforced *structurally*: `LLMSubScores` has no `total` and no `score` field, so a
model that emits one cannot influence the aggregate.
`test_llm_cannot_set_the_total` locks that in.

Consequence: no key, a timeout, or malformed JSON all degrade to a fully
deterministic path in the same response shape, with
`evaluationMode="deterministic"`. **An API outage cannot break the demo.**

### Formula

```
score (0-100)
  = 30%  relevance            <- deterministic: similarity x novelty + concept touch
  + 30%  technicalCorrectness <- LLM sub-score; coverage proxy offline
  + 20%  completeness         <- deterministic: concept coverage ratio
  + 10%  reasoning            <- LLM sub-score; derived offline
  + 10%  clarity              <- LLM sub-score; structure heuristic offline
```

Weights live in `evaluator/scoring.py::WEIGHTS` and are exposed by
`/api/ai/evaluation-health`. They are engineering defaults, **not** values the
problem statement specified — say so if asked.

### Guardrails, applied after the weighted sum

| flag | trigger | effect |
|---|---|---|
| `refusal` | short answer containing "I don't know", "skip", … | capped at 25 |
| `off_topic` | relevance ≤ 35, with a concept list present | capped at 30 |
| `insufficient_length` | fewer than 8 substantive tokens | capped at 35 |
| `factually_incorrect` | LLM sets `factuallyIncorrect` | × 0.55 |
| `no_concept_coverage` | zero coverage and relevance < 60 | capped at 25 |
| `no_concept_ground_truth` | no `expectedConcepts` (ice-breakers) | informational; disables the off-topic cap |

**Novelty clawback.** Relevance is scaled by how much of the answer is *not*
lifted from the question. Without it, "I would design a secure token-based system
and handle revocation properly" scores 92 on similarity alone while saying
nothing. With it: 52 → total 38 (`g10_parrot`).

---

## API

### `POST /api/ai/evaluate-answer`

Accepts either a full `QuestionObject` (preferred — pass it straight through
from `/api/ai/generate-question`) or loose fields:

```json
{
  "questionId": "q_auth_01",
  "questionText": "How would you handle JWT revocation on logout?",
  "answerText": "Because JWTs are stateless I keep a denylist in Redis...",
  "expectedConcepts": ["revocation strategy", "denylist"],
  "rubric": {"poor": "...", "acceptable": "...", "excellent": "..."},
  "stage": "role_technical",
  "competency": "backend",
  "difficulty": 3
}
```

Returns `EvaluationResult`. The first five fields are the frozen core the
orchestrator and scorecard engine already consume; everything below is additive
and default-safe, so the mock and any external producer stay valid.

```json
{
  "score": 80,
  "coveredConcepts": ["revocation strategy", "denylist"],
  "missingConcepts": [],
  "reasoning": "Explains stateless revocation via a Redis denylist with TTL.",
  "confidence": 0.72,

  "subScores": {"relevance": 88, "technicalCorrectness": 78,
                "completeness": 72, "reasoning": 80, "clarity": 86},
  "partialConcepts": [],
  "conceptDetail": [
    {"concept": "denylist", "score": 0.91, "covered": true, "partial": false,
     "evidence": "I keep a denylist of token IDs in Redis with a TTL."}
  ],
  "scoreBreakdown": {
    "weights": {"relevance": 0.3, "...": 0},
    "weightedContributions": {"relevance": 26.4, "...": 0},
    "rawWeightedSum": 80.2,
    "guardsApplied": [],
    "finalTotal": 80.2,
    "coverageThreshold": 0.55,
    "scoringMode": "llm_assisted"
  },
  "flags": [],
  "evaluationMode": "llm_assisted",
  "strategyHint": "increase_difficulty"
}
```

`conceptDetail[].evidence` is the sentence **from the candidate's own answer**
that best matched the concept. That is the audit trail the master plan asks for,
and the strongest thing to point at on screen.

**Status codes:** always `200` for a valid body — empty answer included. `422`
only for a malformed request. Never `500`.

`strategyHint`: `probe_missing_concept`, `correct_and_probe`, `reask_simpler`,
`increase_difficulty`, `continue`. Advisory — the policy engine still decides.

### `POST /api/ai/evaluate-answers`

Batch form, `{"items": [...]}`, same contract per item, order preserved.

### `GET /api/ai/evaluation-health`

Run before the demo. Reports the live scoring mode, whether a key is configured
(never the key), whether the closed loop is on the real evaluator, which
embedding backend loaded, the active weights and thresholds.

---

## Setup

Already covered by `requirements.txt`. No new dependencies.

```bash
pytest tests/ -v                              # full suite, no API key needed
pytest tests/test_answer_evaluation.py -v      # this subsystem only
python tools/calibrate.py                      # Q&A table, offline
python tools/calibrate.py --llm --runs 3       # with a key: also measures spread
python tools/calibrate.py --compare-mock       # real vs mock
```

| env var | effect |
|---|---|
| `GEMINI_API_KEY` | absent → deterministic mode; everything still works |
| `EVAL_FORCE_DETERMINISTIC=1` | **demo-safety switch** — pins the offline path |
| `EVAL_USE_REAL=1` | closed-loop pipeline uses `RealAnswerEvaluator` instead of the mock |

`sentence-transformers` is optional here as it is for retrieval. Without it the
matcher falls back to fuzzy token overlap: blunter (3/5 concepts on the strong
case where embeddings get 5/5) but never crashes and never needs the network.

---

## Golden test set

`data/golden_answers.json` — 10 cases covering Master Plan §15.1: strong,
partial, irrelevant, **confident-but-wrong**, vague, verbose, too-short, empty,
no-concept-list, parrot.

Each asserts a **band**, not an exact number, because no labelled ground-truth
dataset exists for interview scoring. Cases where the offline path is honestly
blunter carry a separate `expectBandDeterministic`; the suite asserts the band
for the mode it ran in and never loosens the real target to make the fallback
pass.

Beyond bands, the suite asserts **discrimination** — strong > partial > vague >
irrelevant, parrot < partial. A scorer that cannot rank answers is useless
however well-calibrated any single number looks.

Deterministic mode: **10/10 in band, 51 tests passing** (44 engine + 7 API).

---

## Known limitations — state these before a judge finds them

1. **The deterministic path cannot detect a confidently wrong answer.** It
   verifies concepts are *present*, not *true*. Case `g04_confident_wrong` —
   "an index is a cached copy of the table in RAM, so indexes always make things
   faster" — uses all the right vocabulary and is wrong on every claim, scoring
   ~54 offline. Only the LLM path sets `factuallyIncorrect`, applying the ×0.55
   penalty to drop it below 45. This is the documented failure mode of LLM-based
   interview graders: they score delivery and miss technical wrongness. Lead
   with it. `test_incorrectness_penalty_applies_when_the_llm_flags_it` proves the
   LLM path actually moves the number;
   `test_confident_wrong_limitation_is_documented` fails if anyone later claims
   the offline path handles it.

2. **No labelled ground truth.** Validated against 10 hand-written cases with
   human-agreed bands, not real hiring outcomes. We cannot quote an accuracy
   figure and do not.

3. **Weights are engineering defaults**, not PS-specified. Configurable, and
   exposed via the health endpoint.

4. **LLM sub-scores vary run to run.** Grading temperature is 0.1 (lower than
   generation's 0.2) and aggregation is deterministic, which bounds drift but
   does not remove it. Run `--llm --runs 3` and report the observed spread rather
   than implying the number is exact.

5. **Coverage threshold (0.55) is tuned, not derived.** Lower it and vague
   answers pass; raise it and strong answers are punished for paraphrasing.

## Responsible use

Decision support for a human panel, never an autonomous hiring decision. The
evaluator prompt forbids inferring anything about the candidate as a person —
personality, health, background, or any protected attribute; it grades the answer
only. Every score ships with its breakdown and the evidence sentence behind it.
Use synthetic candidate data in the demo.
