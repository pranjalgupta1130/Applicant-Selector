# BoardRoom AI — Backend & Data Service

A Node.js & Express backend for BoardRoom AI providing autonomous interview session management, question persistence, candidate answer evaluations, adaptive turn progression, and stage-weighted final report generation backed by an atomic local JSON storage layer.

---

## 🚀 Quick Setup & Execution

### Requirements
- **Node.js**: v18.0.0 or higher (v24.x tested)
- **npm**: v9.x or higher

### Installation
```bash
cd backend
npm install
```

### Environment Configuration
Copy `.env.example` to `.env` (already configured by default):
```env
PORT=5000
NODE_ENV=development
AI_SERVICE_URL=http://localhost:8000
AI_SERVICE_TIMEOUT_MS=5000
```
*Note: The Python AI service at `http://localhost:8000` is optional. If unavailable, the Node.js backend uses built-in deterministic fallback evaluation and adaptive question generation without breaking.*

### Seed Local Database
```bash
npm run seed
```
Seeds initial roles and target competencies under `backend/data/`.

### Start Backend Server
```bash
npm start
```
Runs Express server on `http://localhost:5000`.

---

## 📡 Key REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health and liveness check (`?checkAi=true` verifies AI service) |
| `GET` | `/api/roles` | List available roles & competencies |
| `GET` | `/api/roles/:id` | Fetch role by ID |
| `POST` | `/api/candidates` | Create candidate profile |
| `POST` | `/api/candidates/:id/resume` | Attach resume URL reference |
| `POST` | `/api/interviews` | Create interview session |
| `GET` | `/api/interviews/:id` | Get interview state |
| `POST` | `/api/interviews/:id/start` | Start interview session |
| `POST` | `/api/interviews/:id/questions` | Persist question attached to interview |
| `GET` | `/api/interviews/:id/questions` | Retrieve all interview questions |
| `POST` | `/api/interviews/:id/answers` | Submit candidate answer (triggers evaluation & adaptive next question) |
| `GET` | `/api/interviews/:id/report` | Generate / fetch stage-weighted final evaluation report |

---

## 🔄 Vertical Slice Demo Flow

1. **Role Selection**: `GET /api/roles`
2. **Candidate Creation**: `POST /api/candidates`
3. **Session Start**: `POST /api/interviews` → `POST /api/interviews/:id/start`
4. **First Question**: `POST /api/interviews/:id/questions`
5. **Adaptive Turns (Repeat 5x)**: `POST /api/interviews/:id/answers`
   - Evaluates answer (1-10 dimensions).
   - Computes adaptive strategy (`escalate`, `maintain`, `simplify`).
   - Generates & persists next question across stages (`ice_breaker` → `fundamentals` → `technical` → `deep_dive` → `scenario`).
6. **Final Report**: `GET /api/interviews/:id/report` (returns stage-weighted overall score, competency scores, strengths, gaps, and neutral recommendations).

---

## 💾 Storage Architecture
All persistent data is stored under `backend/data/` using atomic temporary file writes with mutex serialization (`backend/src/storage/jsonStore.js`). Process restarts preserve all interview data.
