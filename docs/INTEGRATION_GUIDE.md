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

---

## 🔄 6. Phase C — Closed-Loop Adaptive Interview Engine

### Architecture

```
Candidate Answer
      ↓
Member 4 Answer Evaluation
      ↓
Evaluation Result (score, coveredConcepts, missingConcepts)
      ↓
InterviewState Update (streaks, trends, mastery levels, recovery)
      ↓
Concept Prerequisite Engine
      ↓
Adaptive Policy v2 (difficulty calibration, stage progression)
      ↓
Target-Concept Selection (priority: persistent weakness -> prereqs -> gaps)
      ↓
RAG Retrieval (grounding knowledge chunks)
      ↓
Question Generation Pipeline (Gemini with Quality Gates & Fallback)
      ↓
Next Question & Decision Trace
      ↓
Candidate Answer (Next Turn)
      ↺
```

### Module Ownership & Architectural Boundaries

| Component | Owner | Responsibilities |
|---|---|---|
| **RAG & Retrieval** | Member 3 | Dense semantic search (all-MiniLM-L6-v2), TF-IDF fallback, chunk filtering, grounding |
| **Question Generation** | Member 3 | Gemini question generation, Quality Gates (relevance >= 70, rubrics, dedup), deterministic fallback |
| **Answer Evaluation** | Member 4 | Candidate answer scoring (0-100), covered concepts, missing concepts, reasoning, confidence |
| **Adaptive Engine** | Adaptive Engine | InterviewState, mastery tracking, streak/trend tracking, Prerequisite DAG, Adaptive Policy v2, Orchestrator |

> **Architectural Invariant**: The RAG and question generation modules **never** score candidate answers. The orchestration layer strictly consumes evaluation results produced by Member 4 (or the mock adapter during testing).

---

### Endpoint: `POST /api/interview/start`

Initializes a clean `InterviewState` and generates the opening ice-breaker question.

#### Request Example
```json
{
  "candidate": {
    "name": "Jordan Lee",
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "experience_years": 3.0
  },
  "role": {
    "id": "backend_engineer",
    "title": "Backend / Full-Stack Software Engineer"
  }
}
```

#### Response Example
```json
{
  "interviewState": {
    "candidate_id": "cand_default",
    "role_id": "backend_engineer",
    "current_stage": "ice_breaker",
    "current_competency": "ice_breaker",
    "difficulty": 1,
    "score_history": [],
    "demonstrated_concepts": [],
    "missing_concepts": []
  },
  "openingQuestion": {
    "id": "q_ice_01",
    "text": "Could you provide an overview of your software engineering background and the technical architecture of a recent backend project you led or built?",
    "stage": "ice_breaker",
    "competency": "ice_breaker",
    "difficulty": 1,
    "expectedConcepts": [
      "software architecture overview",
      "recent technical project",
      "core engineering strengths"
    ],
    "rubric": {
      "poor": "Cannot explain project architecture or role clearly.",
      "acceptable": "Describes tech stack, basic responsibilities, and components.",
      "excellent": "Articulates architectural trade-offs, scaling considerations, and project impact."
    },
    "relevanceScore": 88,
    "sources": ["chunk_ice_01"],
    "isFallback": false,
    "questionType": "conceptual"
  }
}
```

---

### Endpoint: `POST /api/interview/turn`

Processes a completed interview turn in a closed loop.

#### Request Example
```json
{
  "currentQuestion": {
    "id": "q_auth_01",
    "text": "How do you implement JWT authentication with refresh token rotation to mitigate token theft?",
    "stage": "role_technical",
    "competency": "backend",
    "difficulty": 3,
    "expectedConcepts": ["JWT authentication", "refresh token rotation"],
    "rubric": {
      "poor": "Cannot describe token structures or replay mitigation.",
      "acceptable": "Mentions access vs refresh tokens and basic storage.",
      "excellent": "Details cryptographic signatures, rotation strategies, and reuse detection."
    },
    "relevanceScore": 89,
    "sources": ["chunk_auth_01"],
    "isFallback": false
  },
  "candidateAnswer": "We use short-lived JWT access tokens and long-lived refresh tokens stored in HttpOnly cookies. On refresh, the server issues a new pair and revokes the old refresh token.",
  "interviewState": {
    "current_stage": "role_technical",
    "current_competency": "backend",
    "difficulty": 3,
    "score_history": [80],
    "demonstrated_concepts": ["REST APIs"],
    "missing_concepts": []
  },
  "evaluation": {
    "score": 88,
    "coveredConcepts": ["JWT authentication", "refresh token rotation"],
    "missingConcepts": [],
    "reasoning": "Candidate correctly explained short-lived tokens and rotation mechanism.",
    "confidence": 0.90
  }
}
```

#### Response Example
```json
{
  "updatedState": {
    "current_stage": "role_technical",
    "current_competency": "backend",
    "difficulty": 3,
    "score_history": [80, 88],
    "rolling_score_trend": "improving",
    "consecutive_strong_count": 2,
    "consecutive_weak_count": 0,
    "demonstrated_concepts": ["REST APIs", "JWT authentication", "refresh token rotation"],
    "missing_concepts": [],
    "consistently_demonstrated_concepts": [],
    "demonstrated_once_concepts": ["REST APIs", "JWT authentication", "refresh token rotation"]
  },
  "evaluation": {
    "score": 88,
    "coveredConcepts": ["JWT authentication", "refresh token rotation"],
    "missingConcepts": [],
    "reasoning": "Candidate correctly explained short-lived tokens and rotation mechanism.",
    "confidence": 0.90
  },
  "decision": {
    "strategy": "escalate_difficulty",
    "nextDifficulty": 4,
    "nextCompetency": "database",
    "targetConcepts": ["B-Tree indexing"],
    "questionType": "trade_off",
    "reason": "Candidate achieved sustained strong performance (2 consecutive scores >= 80, latest: 88/100, trend: improving). Escalating difficulty to 4/5 (trade_off) in deep_dive."
  },
  "nextQuestion": {
    "id": "q_db_02",
    "text": "When designing a composite index in PostgreSQL on columns (user_id, created_at, status), how does column order impact query planning and range scan performance?",
    "stage": "deep_dive",
    "competency": "database",
    "difficulty": 4,
    "expectedConcepts": ["B-Tree indexing", "composite indexing", "indexing trade-offs"],
    "rubric": {
      "poor": "Believes column order in composite indexes does not matter.",
      "acceptable": "Explains left-to-right prefix matching rule.",
      "excellent": "Explains index skip scans, equality before range predicate ordering, and index-only scans."
    },
    "relevanceScore": 92,
    "sources": ["chunk_db_index_01"],
    "isFallback": false,
    "questionType": "trade_off"
  },
  "termination": {
    "shouldTerminate": false,
    "reason": "Minimum interview depth not yet achieved (2/4 turns completed).",
    "evidenceCoverage": 0.52,
    "details": {
      "totalTurns": 2,
      "stagesVisited": 2,
      "unresolvedWeaknesses": []
    }
  },
  "trace": {
    "previousScore": 88,
    "trend": "improving",
    "missingConcepts": [],
    "persistentWeaknesses": [],
    "prerequisiteIssues": [],
    "strategy": "escalate_difficulty",
    "nextDifficulty": 4,
    "nextCompetency": "database",
    "questionType": "trade_off",
    "targetConcepts": ["B-Tree indexing"],
    "reason": "Candidate achieved sustained strong performance (2 consecutive scores >= 80, latest: 88/100, trend: improving). Escalating difficulty to 4/5 (trade_off) in deep_dive."
  }
}
```

---

### Example Decision Traces

#### Trace 1: Persistent Weakness Remediation
```json
{
  "previousScore": 45,
  "trend": "declining",
  "missingConcepts": ["concurrency race conditions"],
  "persistentWeaknesses": ["concurrency race conditions"],
  "prerequisiteIssues": [],
  "strategy": "remediate_persistent_weakness",
  "nextDifficulty": 2,
  "nextCompetency": "backend",
  "questionType": "debugging",
  "targetConcepts": ["concurrency race conditions"],
  "reason": "Candidate repeatedly missed 'concurrency race conditions' across multiple turns (persistent weakness detected). De-escalating difficulty to 2/5 using a debugging question to diagnose fundamental misconceptions."
}
```

#### Trace 2: Prerequisite Reinforcement
```json
{
  "previousScore": 40,
  "trend": "declining",
  "missingConcepts": ["write amplification"],
  "persistentWeaknesses": [],
  "prerequisiteIssues": ["B-Tree indexing"],
  "strategy": "reinforce_prerequisite",
  "nextDifficulty": 2,
  "nextCompetency": "database",
  "questionType": "conceptual",
  "targetConcepts": ["B-Tree indexing"],
  "reason": "Candidate attempted advanced topic with unverified foundations. Targeting prerequisite 'B-Tree indexing' at difficulty 2/5 (conceptual) to reinforce core building blocks."
}
```

#### Trace 3: Recovery Confirmation
```json
{
  "previousScore": 86,
  "trend": "improving",
  "missingConcepts": [],
  "persistentWeaknesses": [],
  "prerequisiteIssues": [],
  "strategy": "progress_after_recovery",
  "nextDifficulty": 3,
  "nextCompetency": "database",
  "questionType": "implementation",
  "targetConcepts": ["B-Tree indexing"],
  "reason": "Candidate successfully demonstrated recovery of 'JWT authentication' (score: 86/100). Resuming stage progression to 'role_technical' at difficulty 3/5."
}
```

---

## 📊 7. Phase D — Evidence-Based Competency Assessment & Final Selector Scorecard

### Architecture

```
Completed Interview Trajectory (turns, scores, covered/missing concepts)
        ↓
Concept-Level Evidence Aggregator (counts, bounds, question types, mastery, provenance)
        ↓
Role-Aware Competency Matrix (configurable weights, expected concepts pool)
        ↓
Competency Evidence Evaluator (score, confidence, coverage, uncertainty, contradictory detection)
        ↓
Role Alignment & Strengths/Gaps Extraction
        ↓
Technical vs Managerial Evidence Separation
        ↓
Final Selector Scorecard Engine
        ↓
Frontend-Ready Dashboard Data & Evidence Timeline (Human Decision Support)
```

### Key Principles & Mathematical Formulae

#### 1. Separation of Score, Coverage, and Confidence
* **Competency Score** ($0 - 100$): Measures the quality of demonstrated candidate answers where observed.
  $$\text{Competency Score} = \text{round}\left(0.65 \times \text{Avg Turn Score} + 0.35 \times (\text{Demo Ratio} \times 100)\right)$$
* **Evidence Coverage** ($0.0 - 1.0$): Measures breadth across expected role concepts.
  $$\text{Evidence Coverage} = \frac{\text{Tested Expected Concepts}}{\text{Total Expected Concepts in Role Benchmark}}$$
* **Evidence Confidence** ($0.0 - 0.95$): Measures evidence depth, multi-type consistency, and cross-stage repeatability. Bounded between $0.0$ and $0.95$ (never claiming statistical certainty).
* **Uncertainty & Thin Evidence**: When a competency has only 1 turn or low coverage ($< 25\%$), its status is flagged as `"insufficient_evidence"` (confidence $\le 0.45$) rather than penalizing the score to zero. Untested competencies are marked `"untested"` ($0.0$ confidence).

#### 2. Weighted Overall Score
$$\text{Overall Score} = \sum (\text{Competency Weight} \times \text{Competency Score})$$
Default weights (Backend Engineer):
* Backend: $35\%$
* Database: $25\%$
* System Design: $25\%$
* CS Fundamentals: $15\%$
*(Note: Weights are configurable engineering parameters and can be overridden via API)*.

#### 3. Human Decision-Support Boundary (Strictly Non-Autonomous)
The system **never** produces autonomous hiring labels (`"Hire"`, `"Reject"`, `"Selected"`). It generates objective evidence summaries, identified strengths, verified gaps, and unverified areas to empower human selectors and interviewers.

---

### Endpoint: `POST /api/interview/scorecard`

#### Request Example
```json
{
  "interviewState": { ... },
  "candidate": {
    "name": "Jordan Lee",
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "experience_years": 3.0
  },
  "role": {
    "id": "backend_engineer",
    "title": "Backend / Full-Stack Software Engineer"
  },
  "competencyWeights": {
    "backend": 0.40,
    "database": 0.25,
    "system_design": 0.25,
    "cs_fundamentals": 0.10
  }
}
```

#### Response Example (Truncated Sample)
```json
{
  "scorecard": {
    "candidate": {
      "name": "Jordan Lee",
      "skills": ["Python", "FastAPI", "PostgreSQL"]
    },
    "role": {
      "id": "backend_engineer",
      "title": "Backend / Full-Stack Software Engineer"
    },
    "overallScore": 86,
    "overallConfidence": 0.82,
    "competencies": [
      {
        "competency": "backend",
        "score": 90,
        "confidence": 0.88,
        "coverage": 0.62,
        "status": "demonstrated",
        "testedConcepts": ["REST APIs", "idempotency", "JWT authentication", "refresh token rotation"],
        "demonstratedConcepts": ["REST APIs", "idempotency", "JWT authentication", "refresh token rotation"],
        "partialConcepts": [],
        "missingConcepts": [],
        "evidenceCount": 2,
        "strongEvidence": [
          "Demonstrated 'REST APIs' across 1 turn(s)",
          "Demonstrated 'JWT authentication' across 1 turn(s)"
        ],
        "weakEvidence": [],
        "contradictoryEvidence": [],
        "reasoning": "Competency score is 90/100 (confidence: 0.88, coverage: 62%) derived from 2 evaluated turn(s) with average score 90/100."
      },
      {
        "competency": "database",
        "score": 84,
        "confidence": 0.72,
        "coverage": 0.38,
        "status": "demonstrated",
        "testedConcepts": ["B-Tree indexing", "composite indexing"],
        "demonstratedConcepts": ["B-Tree indexing", "composite indexing"],
        "evidenceCount": 1,
        "reasoning": "Competency score is 84/100 (confidence: 0.72, coverage: 38%) derived from 1 evaluated turn(s)."
      }
    ],
    "strengths": [
      {
        "area": "JWT authentication",
        "competency": "backend",
        "evidence": "Successfully demonstrated across 1 turn(s) (Turn(s) 2) with top score 92/100.",
        "confidence": 0.85,
        "supportingTurns": [2]
      }
    ],
    "gaps": [],
    "coverage": {
      "overallEvidenceCoverage": 0.78,
      "competencyCoverage": [
        {
          "competency": "backend",
          "coverage": 0.62,
          "score": 90,
          "confidence": 0.88,
          "status": "demonstrated"
        }
      ],
      "testedConceptsCount": 8,
      "demonstratedConceptsCount": 8,
      "missingConceptsCount": 0,
      "stagesVisitedCount": 4
    },
    "roleAlignment": {
      "roleId": "backend_engineer",
      "roleTitle": "Backend / Full-Stack Software Engineer",
      "alignmentScore": 85,
      "demonstratedRequirements": ["REST APIs", "SQL"],
      "partiallyDemonstratedRequirements": [],
      "insufficientlyTestedRequirements": ["Git"],
      "missingRequirements": [],
      "rationale": "Candidate satisfies 4/5 mandatory role requirements with verified evidence."
    },
    "decisionSupport": {
      "technicalEvidence": "Candidate completed 4 technical turn(s) with an average score of 88/100.",
      "managerialEvidence": "Insufficient managerial evidence — interview session focused on technical competencies.",
      "roleAlignmentEvidence": "Candidate role alignment score is 85/100.",
      "areasRequiringFurtherAssessment": ["Git (insufficiently tested)"],
      "recommendationNote": "Decision-support summary for human selector. BoardRoom AI does not make autonomous hiring decisions."
    },
    "evidenceTimeline": [
      {
        "turn": 1,
        "stage": "fundamentals",
        "competency": "backend",
        "difficulty": 2,
        "questionId": "q1",
        "questionText": "Explain REST APIs and idempotency.",
        "questionType": "conceptual",
        "score": 88,
        "coveredConcepts": ["REST APIs", "idempotency"],
        "missingConcepts": [],
        "evidenceStatus": "demonstrated",
        "summary": "Turn 1 (backend, diff 2/5, conceptual): score 88/100. Status: demonstrated."
      }
    ],
    "explanation": "Candidate Evaluation Summary for Jordan Lee..."
  }
}
```


