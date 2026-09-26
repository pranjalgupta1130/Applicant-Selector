# BoardRoom AI — RAG & Question Generation Subsystem (Member 3)

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-orange.svg)](https://docs.pydantic.dev/)
[![Sentence-Transformers](https://img.shields.io/badge/Embeddings-all--MiniLM--L6--v2-purple.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![Tests](https://img.shields.io/badge/tests-25%20passed%2C%201%20skipped-brightgreen.svg)](tests/)

Production-quality Hackathon MVP for the **RAG + Question Generation Subsystem** of BoardRoom AI, built strictly according to the **PSWB01 Selector–Applicant Hackathon Master Plan**.

---

## 🎯 Architecture Overview

```
Candidate Profile + Target Role + Stage + Competency + Difficulty + Missing Concepts
                               │
                               ▼
            ┌──────────────────────────────────────────────┐
            │             KnowledgeRetriever               │
            │  - Metadata Pre-Filtering & Auto-Relaxation  │
            │  - Dense Semantic Embeddings (MiniLM-L6-v2)  │
            │  - In-Process Cosine Similarity Dot-Product   │
            │  - Sublinear TF-IDF Lexical Fallback         │
            └──────────────────────┬───────────────────────┘
                                   │ Top-K Grounded Context + Rubrics
                                   ▼
            ┌──────────────────────────────────────────────┐
            │          QuestionGeneratorPipeline           │
            │  - Grounded Context Synthesis                │
            │  - Gemini 2.5 Flash Structured JSON          │
            │  - Deduplication & Adaptive Probing          │
            │  - Curated Deterministic Question Fallback   │
            └──────────────────────┬───────────────────────┘
                                   │ Structured Question
                                   ▼
            ┌──────────────────────────────────────────────┐
            │          QuestionRelevanceEvaluator          │
            │  - 5-Factor Auditable Formula (0-100)        │
            │  - Explainable Score Rationale Breakdown     │
            │  - Quality Guardrail Validation              │
            └──────────────────────┬───────────────────────┘
                                   │
                                   ▼
         Validated QuestionObject with Grounding Sources & Rubrics
```

---

## 📂 Repository Structure

```
.
├── ai-service/
│   ├── adaptive/
│   │   └── strategy.py          # Adaptive interview progression & gap probing
│   ├── api/
│   │   └── routes.py            # FastAPI REST endpoints (Section 9 contracts)
│   ├── core/
│   │   ├── config.py            # Environment & model settings
│   │   └── schemas.py           # Shared Pydantic data contracts (Section 11.2)
│   ├── evaluator/
│   │   └── relevance.py         # 5-factor explainable question relevance engine
│   ├── generator/
│   │   └── pipeline.py          # End-to-end question generator + fallback
│   ├── rag/
│   │   └── retriever.py         # Metadata-filtered vector retrieval engine
│   └── main.py                  # Service entry point with CORS & Health check
├── data/
│   └── knowledge_base/
│       └── seed_knowledge.json  # 26 curated chunks across 5 competencies & stages
├── tests/
│   └── test_rag_pipeline.py     # Golden test suite (13 passing test cases)
├── .env.example                 # Environment configuration template
├── requirements.txt             # Pinned dependencies
└── README.md                    # Subsystem documentation & API reference
```

---

## 🚀 Quickstart & Setup

### 1. Configure Environment
```bash
cp .env.example .env
```
*(Optional for online generation: add your `GEMINI_API_KEY` in `.env`. If omitted or offline, the subsystem operates deterministically via the curated knowledge bank.)*

### 2. Run Test Suite
Verify all 13 golden test cases covering retrieval, generation, relevance, fallbacks, and API contracts:
```bash
pytest tests/test_rag_pipeline.py -v
```

### 3. Start the FastAPI AI Service
```bash
python ai-service/main.py
```
Or via uvicorn directly:
```bash
uvicorn ai-service.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation will be live at: **`http://localhost:8000/docs`**

---

## 🤝 Integration Contract for Backend & Evaluation Team

### Subsystem Boundaries
* **Member 3 (RAG/LLM - This Module)**: Responsible for knowledge retrieval, structured question generation, expected concepts, rubrics, and question relevance scoring.
* **Member 4 (Evaluation Team)**: Responsible for evaluating candidate answers, concept coverage matching, and final candidate scoring. **The RAG module explicitly does NOT evaluate answers.**
* **Member 2 (Backend Team)**: Calls `/api/ai/generate-question` to populate questions and `/api/ai/adaptive-context` to guide session progression.

---

### Core Endpoint: `POST /api/ai/generate-question`

#### 1. Request JSON Schema
```json
{
  "candidate": {
    "id": "cand_001",
    "name": "Jordan Lee",
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "experience_years": 3.0,
    "education": "B.Tech in Computer Engineering"
  },
  "role": {
    "id": "backend_engineer",
    "title": "Backend / Full-Stack Software Engineer",
    "required_skills": ["Python", "SQL", "REST APIs", "System Design"]
  },
  "stage": "role_technical",
  "competency": "backend",
  "difficulty": 3,
  "previousQuestions": [
    "Explain the difference between POST and PUT in REST APIs."
  ],
  "previousMissingConcepts": [
    "refresh token rotation",
    "token revocation"
  ]
}
```
*Note: `previousQuestions` and `previousMissingConcepts` are optional lists used for deduplication and adaptive follow-up.*

#### 2. Frozen Response JSON Contract (10 Fields)
Every response is guaranteed to return these 10 fields:
```json
{
  "id": "q_7a9f1b2c",
  "text": "Following up on our earlier discussion regarding refresh token rotation: How would you design a secure token-based authentication system using JWTs, and how do you handle token revocation when a user logs out?",
  "stage": "role_technical",
  "competency": "backend",
  "difficulty": 3,
  "expectedConcepts": [
    "JWT structure",
    "short-lived access tokens",
    "refresh token rotation",
    "httpOnly cookies",
    "revocation strategy"
  ],
  "rubric": {
    "poor": "Suggests storing sensitive secrets in JWT payload or believes JWTs cannot be revoked.",
    "acceptable": "Explains JWT structure, short expiration with refresh tokens, and mentions a blacklist.",
    "excellent": "Addresses XSS/CSRF mitigations, refresh token rotation with reuse detection, and distributed revocation via Redis TTL."
  },
  "relevanceScore": 89,
  "sources": [
    "chunk_tech_auth_01",
    "OWASP-API-Security-Top10"
  ],
  "isFallback": false
}
```

#### 3. Error Responses
* **HTTP 422 Unprocessable Entity**: Returned when required parameters are missing or out-of-range (e.g., `difficulty` outside 1–5). Returns standard FastAPI validation details.
* **HTTP 500 Internal Server Error**: Fatal internal server error (safely avoided via internal try/catch fallback).

#### 4. Fallback Behaviour
* If `GEMINI_API_KEY` is not present, the LLM service times out, or the LLM returns invalid/malformed JSON, the service **does not crash or return HTTP 500**.
* Instead, it returns HTTP 200 with `isFallback: true`, serving a curated, stage-calibrated question directly from the 39-chunk knowledge base with full rubrics and expected concepts attached.

---

### Adaptive Handoff Endpoint: `POST /api/ai/adaptive-context`
Provides Member 2 and Member 4 with strategy recommendations without performing candidate evaluation.

**Request:**
```json
{
  "previousQuestions": ["Explain SQL index vs table scan"],
  "coveredConcepts": ["SQL index", "table scan"],
  "missingConcepts": ["B-Tree update overhead", "write amplification"],
  "currentDifficulty": 3,
  "lastScore": 55,
  "currentCompetency": "database",
  "currentStage": "role_technical"
}
```

**Response:**
```json
{
  "next_stage": "role_technical",
  "next_competency": "database",
  "next_difficulty": 3,
  "strategy": "probe_missing_concept",
  "missing_concepts_to_probe": ["B-Tree update overhead", "write amplification"],
  "rationale": "Candidate missed critical concepts (B-Tree update overhead, write amplification); probing to evaluate baseline understanding."
}
```

---

### Local Run Commands

```bash
# 1. Run full test suite (34 passing tests across unit, golden, and integration)
pytest tests/ -v

# 2. Start the AI service on port 8000
python ai-service/main.py
```
*Live Swagger documentation will be available at:* **`http://localhost:8000/docs`**
