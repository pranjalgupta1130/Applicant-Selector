# BoardRoom AI — RAG Subsystem Integration Guide
**Target Audience**: Member 2 (Node/Express Backend) & Member 4 (Answer Evaluation)  
**Author**: Member 3 (RAG / LLM Engineer)  
**Status**: FROZEN & READY FOR CONSUMPTION  

---

## 🚀 1. Service Startup & Verification

### Startup Command
From the project root:
```bash
python ai-service/main.py
```
*(Alternative via uvicorn: `uvicorn ai-service.main:app --host 0.0.0.0 --port 8000 --reload`)*

The service starts locally on: **`http://localhost:8000`**  
Interactive OpenAPI / Swagger UI: **`http://localhost:8000/docs`**

### Pre-Integration Smoke Test
Before connecting your Node server or test scripts, run:
```bash
python smoke_test.py
```
This zero-dependency script verifies `/health`, `/api/ai/generate-question`, and `/api/ai/adaptive-context` in ~2 seconds.

---

## 📡 2. Endpoint 1: Generate Question (`Member 2 Handoff`)

* **URL**: `POST http://localhost:8000/api/ai/generate-question`
* **Headers**: `Content-Type: application/json`
* **Purpose**: Generates a grounded, stage-calibrated interview question with expected concepts and rubrics.

### Request JSON Example
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
    "revocation strategy"
  ]
}
```
* **Allowed `stage` values**: `"ice_breaker"`, `"fundamentals"`, `"role_technical"`, `"deep_dive"`, `"scenario_managerial"`
* **Allowed `competency` values**: `"backend"`, `"database"`, `"system_design"`, `"cs_fundamentals"`, `"scenario_managerial"`, `"ice_breaker"`
* **Allowed `difficulty`**: Integer `1` to `5`

### Response JSON (Frozen 10 Fields)
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

---

## 🧠 3. Endpoint 2: Adaptive Strategy Handoff (`Member 4 / Member 2 Handoff`)

* **URL**: `POST http://localhost:8000/api/ai/adaptive-context`
* **Purpose**: Determines next stage, competency pivot, and difficulty shift based on previous performance.
* **CRITICAL**: The RAG subsystem **DOES NOT score candidate answers**. Member 4 performs answer scoring and passes the resulting score & missing concepts here.

### Request JSON Example
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

### Response JSON Example
```json
{
  "next_stage": "role_technical",
  "next_competency": "database",
  "next_difficulty": 3,
  "strategy": "probe_missing_concept",
  "missing_concepts_to_probe": [
    "B-Tree update overhead",
    "write amplification"
  ],
  "rationale": "Candidate missed critical concepts (B-Tree update overhead, write amplification); probing to evaluate baseline understanding."
}
```

---

## 🛡️ 4. Fallback & Error Behaviors

### Fallback Guarantee (Zero Crashes)
* If `GEMINI_API_KEY` is not present, the LLM API is unreachable, or the LLM returns invalid JSON, the endpoint **does not crash or return HTTP 500**.
* It returns HTTP 200 with `isFallback: true`, serving a curated, stage-calibrated question directly from the 39-chunk knowledge base with full rubrics and expected concepts.

### Input Error Handling
* Passing an invalid difficulty (e.g. `difficulty: 99` or `-1`) or invalid types returns **HTTP 422 Unprocessable Entity** with standard FastAPI error details:
```json
{
  "detail": [
    {
      "loc": ["body", "difficulty"],
      "msg": "Input should be less than or equal to 5",
      "type": "less_than_equal"
    }
  ]
}
```

---

## 🌐 5. CORS & Network Integration
* CORS is pre-configured with `allow_origins=["*"]`, allowing direct browser testing from React (`http://localhost:5173`) and Node (`http://localhost:5000`).
