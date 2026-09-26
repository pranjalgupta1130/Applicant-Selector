# BoardRoom AI — RAG & Question Generation Subsystem (Member 3)

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-orange.svg)](https://docs.pydantic.dev/)
[![Sentence-Transformers](https://img.shields.io/badge/Embeddings-all--MiniLM--L6--v2-purple.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![Tests](https://img.shields.io/badge/tests-25%20passed%2C%201%20skipped-brightgreen.svg)](tests/)

Production-quality Hackathon MVP for the **RAG + Question Generation Subsystem** of BoardRoom AI, built strictly according to the **PSWB01 Selector–Applicant Hackathon Master Plan**.

---

## 🎯 Canonical Architecture Overview

The system strictly adheres to the single canonical closed-loop adaptive interview pipeline:

```
Candidate Answer
      │
      ▼
Answer Evaluation (Member 4 Contract / Ingestion)
      │
      ▼
InterviewState Update (History, Mastery Tiers, Streaks, Rolling Trends)
      │
      ▼
Adaptive Policy (Stage Progression, Quotas, Difficulty Calibration)
      │
      ▼
Concept Prerequisite DAG (Dependency Verification)
      │
      ▼
Deterministic Target Concept Selection (Weakness -> Prereqs -> Gaps -> Coverage)
      │
      ▼
KnowledgeRetriever (Dense MiniLM-L6-v2 Semantic Search / TF-IDF Fallback)
      │
      ▼
QuestionGeneratorPipeline (Gemini LLM with Enforced Timeout & Grounded Fallback)
      │
      ▼
Quality Gates (Relevance >= 70, Rubric Consistency, Deduplication)
      │
      ▼
Validated QuestionObject + Explainable Decision Trace
      │
      ▼
InterviewTerminationEngine (Authoritative Multi-Criteria Session Decision)
      │
      ▼
ScorecardEngine (Competency Matrix, Evidence Coverage, Decision Support Report)
```

---

## 📂 Repository Structure

```
.
├── ai-service/
│   ├── adaptive/
│   │   ├── competency_evaluator.py # Evidence confidence & coverage evaluator
│   │   ├── competency_matrix.py    # Role-aware weights & expected concept profiles
│   │   ├── concept_evidence.py     # Turn provenance & demonstration aggregator
│   │   ├── confidence.py           # Canonical single confidence calculation
│   │   ├── orchestrator.py         # Central closed-loop interview orchestrator
│   │   ├── policy.py               # Deterministic Adaptive Interview Policy
│   │   ├── prerequisites.py        # Concept prerequisite DAG engine
│   │   ├── scorecard_engine.py     # Final selector scorecard & report generator
│   │   ├── simulator.py            # Golden archetype regression simulator
│   │   ├── state.py                # InterviewState model & invariant synchronization
│   │   ├── strategy.py             # [DEPRECATED] Legacy stateless strategy
│   │   └── target_concept.py       # Deterministic target concept selection
│   ├── api/
│   │   └── routes.py               # Canonical REST endpoints (/api/interview/*)
│   ├── core/
│   │   ├── concepts.py             # Single canonical source of truth for concepts
│   │   ├── config.py               # Environment, timeout, and CORS settings
│   │   └── schemas.py              # Frozen Pydantic data contracts
│   ├── evaluator/
│   │   ├── answer_evaluator.py     # Member 4 contract adapter
│   │   └── relevance.py            # 5-factor explainable question relevance engine
│   ├── generator/
│   │   └── pipeline.py             # Grounded question generator with timeout & fallback
│   ├── rag/
│   │   └── retriever.py            # Dense embedding search & TF-IDF fallback
│   └── main.py                     # FastAPI entry point with CORS & Health check
├── data/
│   └── knowledge_base/
│       └── seed_knowledge.json     # 39 curated chunks across competencies & stages
├── tests/
│   ├── test_p0_stabilization.py    # P0 stabilization & deterministic adaptive tests
│   ├── test_closed_loop_interview.py # Closed-loop interview tests
│   ├── test_competency_assessment.py # Competency assessment & scorecard tests
│   └── ...                         # Comprehensive test suites (140 tests)
├── requirements.txt                # Pinned dependencies
└── README.md                       # Subsystem documentation & API reference
```

---

## 🚀 Quickstart & Setup

### 1. Configure Environment
```bash
cp .env.example .env
```
Key configuration settings:
- `GEMINI_API_KEY`: (Optional) API key for Gemini LLM generation. When absent or timed out, the system automatically uses the curated deterministic question bank.
- `LLM_TIMEOUT_SECONDS`: Request timeout in seconds (default: `10`). Enforced on both HTTP client and generation config.
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of allowed frontend origins (default: `http://localhost:3000,http://localhost:5173,http://localhost:5000`).

### 2. Run Test Suite
Verify the entire test suite with 100% passing tests:
```bash
python -m pytest
```

### 3. Start the FastAPI AI Service
```bash
python ai-service/main.py
```
Or via uvicorn directly:
```bash
uvicorn ai-service.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation is live at: **`http://localhost:8000/docs`**

---

## 🤝 Canonical Integration Contracts

### 1. `POST /api/interview/start`
Initializes a clean, invariant-verified `InterviewState` and generates the opening ice-breaker question.

### 2. `POST /api/interview/turn`
Processes one complete closed-loop turn:
Candidate Answer → Answer Evaluation → State Update → Policy Decision → Target Concept → Next Question / Termination.

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
  "chunks_indexed": 39,
  "retrieval_mode": "dense",
  "dense_embeddings_active": true,
  "llm_configured": true,
  "llm_model": "gemini-2.5-flash"
}
```

### [DEPRECATED] `POST /api/ai/adaptive-context`
Preserved strictly for backwards compatibility with legacy tests. Marked as deprecated in OpenAPI schema. All new integrations MUST use `/api/interview/*`.

