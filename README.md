# BoardRoom AI (PSWB01) — DRDO/RAC Applicant Selector & Board Room Simulation

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-orange.svg)](https://docs.pydantic.dev/)
[![Sentence-Transformers](https://img.shields.io/badge/Embeddings-all--MiniLM--L6--v2-purple.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![Tests](https://img.shields.io/badge/tests-194%20passed%2C%201%20skipped-brightgreen.svg)](tests/)

Production-quality Hackathon MVP for **PSWB01 — Web-Based Selector-Applicant Simulation Software**, internally named **BoardRoom AI**.

The system simulates an authentic **DRDO/RAC Board Room interview experience**, progressing from ice-breaking to deep technical questioning, scenario analysis, and techno-managerial evaluation, while providing explainable, evidence-based decision support for selection boards.

---

## 🎯 7-Stage Board Room Interview Architecture

The system operates a closed-loop adaptive interview pipeline tailored to scientific selection boards:

```
Applicant Profile (Claimed Expertise) & Advertised Post (Scientist 'B')
                              │
                              ▼
DRDO Multi-Domain Resolution & Strict Boundary Enforcement (ECE / Radar vs Cyber)
                              │
                              ▼
Stage 1: Ice-Breaking / Specialization Interaction
                              │
                              ▼
Stage 2: Expertise Validation (Probes claimed candidate resume skills)
                              │
                              ▼
Stage 3: Core Technical Questioning (Grounded in Radar, DSP, Embedded RTOS)
                              │
                              ▼
Candidate Answer ──► Semantic Evaluator (Paraphrase Credit + Anti-Keyword Stuffing)
                              │
                              ▼
Competency Matrix & Prerequisite DAG Update
                              │
                              ▼
Stage 4: Deep Dive (Follow-up on missing concepts or harder mathematical reasoning)
                              │
                              ▼
Stage 5: Application / Scenario (Real-world clutter, ISR latency, DMA arbitration)
                              │
                              ▼
Stage 6: System Engineering Design (RTCA DO-254 / DO-178C, MIL-STD-1553B)
                              │
                              ▼
Stage 7: Techno-Managerial (Design Reviews PDR/CDR, Thermal/Timing Risk Trade-offs)
                              │
                              ▼
Final Scorecard: Subject Knowledge + Role Suitability + Non-Autonomous Decision Support
```

---

## 📂 Repository Structure

```
.
├── ai-service/
│   ├── adaptive/
│   │   ├── competency_evaluator.py # Evidence confidence & coverage evaluator
│   │   ├── competency_matrix.py    # Role profiles (Scientist 'B' ECE, Radar, Embedded)
│   │   ├── concept_evidence.py     # Turn provenance & demonstration aggregator
│   │   ├── confidence.py           # Canonical confidence calculation
│   │   ├── orchestrator.py         # Central closed-loop interview orchestrator
│   │   ├── policy.py               # 7-stage Board Room deterministic adaptive policy
│   │   ├── prerequisites.py        # Scientific concept prerequisite DAG engine
│   │   ├── scorecard_engine.py     # Final selector scorecard & report generator
│   │   ├── simulator.py            # Golden archetype regression simulator
│   │   ├── state.py                # InterviewState model & invariant synchronization
│   │   └── target_concept.py       # Deterministic target concept selection
│   ├── api/
│   │   └── routes.py               # Canonical REST endpoints (/api/interview/*)
│   ├── core/
│   │   ├── concepts.py             # DRDO ECE, Radar, DSP, Embedded canonical concepts
│   │   ├── config.py               # Environment, timeout, and CORS settings
│   │   ├── drdo_domain.py          # DRDODomainProfile, AdvertisedPostProfile, ApplicantExpertiseProfile
│   │   └── schemas.py              # Pydantic data contracts (QuestionObject, EvaluationResult)
│   ├── evaluator/
│   │   ├── answer_evaluator.py     # GeminiAnswerEvaluator & MockAnswerEvaluator (Fallback)
│   │   └── relevance.py            # 5-factor explainable question relevance engine
│   ├── generator/
│   │   └── pipeline.py             # Grounded question generator with timeout & fallback
│   ├── rag/
│   │   └── retriever.py            # Dense embedding search, loud diagnostics & TF-IDF fallback
│   └── main.py                     # FastAPI entry point with CORS & Health check
├── data/
│   └── knowledge_base/
│       └── seed_knowledge.json     # 45 curated chunks, 71 distinct sample questions
├── scripts/
│   ├── preflight.py                # 12-point automated pre-demo AI preflight check
│   ├── verify_live_ai.py           # Live Gemini connectivity & offline contract test
│   └── expand_knowledge_base.py    # KB enrichment and expansion utility
├── tests/
│   ├── test_answer_evaluation_golden.py # 10 golden evaluation categories (paraphrases vs stuffing)
│   ├── test_semantic_retrieval_benchmark.py # Dense vs TF-IDF zero-keyword retrieval benchmark
│   ├── test_p0_stabilization.py    # P0 stabilization & deterministic adaptive tests
│   ├── test_closed_loop_interview.py # Closed-loop interview tests
│   ├── test_competency_assessment.py # Competency assessment & scorecard tests
│   └── ...                         # Comprehensive test suites (165 tests, 100% pass)
├── requirements.txt                # Pinned dependencies
└── README.md                       # Subsystem documentation & API reference
```

---

## 🚀 Preflight Verification & Demo Tools

### 1. Automated 12-Point Pre-Demo AI Preflight
Run before any live demo to guarantee all subsystems are operational:
```bash
python scripts/preflight.py
```
Checks: Python/dependencies, KB integrity (45 chunks), SentenceTransformer loading, dense RAG mode, retrieval benchmark, Gemini connectivity, question generation quality gates, answer evaluation (semantic paraphrase vs keyword stuffing), adaptive engine turn, scorecard engine, fallback subsystems, and full pytest suite.

### 2. Live Gemini Verification
Verifies end-to-end Gemini connectivity, grounded generation, structured JSON, answer evaluation, and adaptive transitions:
```bash
python scripts/verify_live_ai.py
```
*Note: If `GEMINI_API_KEY` is not set, it cleanly reports `LIVE GEMINI: NOT VERIFIED — API KEY MISSING` and automatically runs all 5 offline deterministic fallback contracts.*

### 3. Run Test Suite
```bash
python -m pytest
```
Result: **164 passed, 1 skipped, 0 failures** in ~60 seconds.

---

## 🤝 Canonical Integration Contracts

### 1. `POST /api/interview/start`
Initializes a clean, invariant-verified `InterviewState` and generates the opening ice-breaker question.

### 2. `POST /api/interview/turn`
Processes one complete closed-loop turn:
Candidate Answer → Answer Evaluation → State Update → Policy Decision → Target Concept → Next Question / Termination.

Response includes:
- `evaluation`: Structured `EvaluationResult` with `score`, `coveredConcepts`, `missingConcepts`, `technicalCorrectness`, `completeness`, `relevance`, `depth`, `isFallback`, and `reasoning`.
- `decision`: Adaptive decision with `strategy`, `nextDifficulty`, `nextCompetency`, `targetConcepts`, `reason`.
- `nextQuestion`: Calibrated, grounded `QuestionObject`.
- `updatedState`: Synchronized, serialized `InterviewState`.
- `termination`: Structured termination assessment.
- `trace`: Explainable decision trace.

### 3. `POST /api/interview/scorecard`
Synthesizes the final Selector Scorecard from accumulated candidate evidence:
- Competency-level scores & confidence
- Role alignment score & requirement coverage
- Technical vs managerial evidence separation
- Decision support summary for human selectors

### 4. `GET /health`
Returns service health, loaded chunks, and explicit retrieval visibility:
```json
{
  "status": "healthy",
  "service": "BoardRoom AI - RAG & Question Generation Subsystem",
  "chunks_indexed": 45,
  "retrieval_mode": "dense",
  "retrieval_mode_display": "DENSE",
  "dense_embeddings_active": true,
  "embedding_model": "all-MiniLM-L6-v2",
  "llm_configured": true,
  "llm_model": "gemini-2.5-flash"
}
```

### [DEPRECATED] `POST /api/ai/adaptive-context`
Preserved strictly for backwards compatibility with legacy tests. Marked as deprecated in OpenAPI schema. All new integrations MUST use `/api/interview/*`.
