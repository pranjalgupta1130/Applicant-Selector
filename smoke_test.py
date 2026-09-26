"""
BoardRoom AI — Integration Smoke Test
Simple, zero-dependency script for Member 2 (Backend) and Member 4 (Evaluation)
to verify the RAG service is live, responsive, and producing valid QuestionObjects.

Usage:
  python smoke_test.py
"""

import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"

def run_smoke_test():
    print("=" * 60)
    print("BoardRoom AI — Subsystem Integration Smoke Test")
    print(f"Target: {BASE_URL}")
    print("=" * 60)

    # 1. Health Check
    print("\n[1/3] Testing GET /health ...")
    try:
        req = urllib.request.Request(f"{BASE_URL}/health", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            health = json.loads(response.read().decode("utf-8"))
            print(f"  -> HTTP {response.status}: {health.get('service')} (Chunks: {health.get('chunks_indexed')})")
            assert response.status == 200
            assert health.get("status") == "healthy"
    except Exception as e:
        print(f"  [FAIL] Could not connect to {BASE_URL}/health. Is the service running?")
        print(f"  Error: {e}")
        print("\nStart the service with: python ai-service/main.py")
        sys.exit(1)

    # 2. Question Generation Contract Test
    print("\n[2/3] Testing POST /api/ai/generate-question ...")
    gen_payload = {
        "candidate": {
            "name": "Jordan Lee",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience_years": 3.0
        },
        "role": {
            "id": "backend_engineer",
            "title": "Backend / Full-Stack Software Engineer"
        },
        "stage": "role_technical",
        "competency": "backend",
        "difficulty": 3,
        "previousQuestions": [],
        "previousMissingConcepts": ["refresh token rotation"]
    }
    
    try:
        data_bytes = json.dumps(gen_payload).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/api/ai/generate-question",
            data=data_bytes,
            headers={"Content-Type": "application/json", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            question = json.loads(response.read().decode("utf-8"))
            print(f"  -> HTTP {response.status} OK")
            
            # Verify frozen 10 fields
            expected_fields = [
                "id", "text", "stage", "competency", "difficulty",
                "expectedConcepts", "rubric", "relevanceScore", "sources", "isFallback"
            ]
            for f in expected_fields:
                assert f in question, f"Missing frozen field: {f}"
            
            print(f"  -> ID: {question['id']}")
            print(f"  -> Question: \"{question['text'][:75]}...\"")
            print(f"  -> Stage: {question['stage']} | Competency: {question['competency']} | Difficulty: {question['difficulty']}/5")
            print(f"  -> Expected Concepts ({len(question['expectedConcepts'])}): {question['expectedConcepts'][:3]}")
            print(f"  -> Relevance Score: {question['relevanceScore']}/100")
            print(f"  -> Sources: {question['sources']}")
            print(f"  -> Fallback Mode: {question['isFallback']}")
    except Exception as e:
        print(f"  [FAIL] Question generation failed: {e}")
        sys.exit(1)

    # 3. [DEPRECATED] Adaptive Handoff Context Test
    print("\n[3/4] Testing POST /api/ai/adaptive-context [DEPRECATED legacy endpoint] ...")
    adapt_payload = {
        "previousQuestions": [question["text"]],
        "coveredConcepts": ["JWT", "HTTP"],
        "missingConcepts": ["token revocation"],
        "currentDifficulty": 3,
        "lastScore": 58,
        "currentCompetency": "backend",
        "currentStage": "role_technical"
    }

    try:
        data_bytes = json.dumps(adapt_payload).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/api/ai/adaptive-context",
            data=data_bytes,
            headers={"Content-Type": "application/json", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            rec = json.loads(response.read().decode("utf-8"))
            print(f"  -> HTTP {response.status} OK")
            print(f"  -> Recommended Strategy: {rec['strategy']}")
            assert "strategy" in rec
    except Exception as e:
        print(f"  [FAIL] Adaptive context failed: {e}")
        sys.exit(1)

    # 4. Canonical Closed-Loop Interview Flow Test
    print("\n[4/4] Testing Canonical Engine (POST /api/interview/start & /api/interview/turn) ...")
    try:
        start_payload = {
            "candidate": {"name": "Jordan Lee", "skills": ["Python", "FastAPI"], "experience_years": 3.0},
            "role": {"id": "backend_engineer", "title": "Backend Software Engineer"}
        }
        req_start = urllib.request.Request(
            f"{BASE_URL}/api/interview/start",
            data=json.dumps(start_payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req_start, timeout=10) as response:
            start_data = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
            assert "openingQuestion" in start_data
            assert "interviewState" in start_data
            print("  -> POST /api/interview/start: OK")

        turn_payload = {
            "currentQuestion": start_data["openingQuestion"],
            "candidateAnswer": "I have experience with Python, FastAPI, and PostgreSQL building microservices.",
            "interviewState": start_data["interviewState"]
        }
        req_turn = urllib.request.Request(
            f"{BASE_URL}/api/interview/turn",
            data=json.dumps(turn_payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req_turn, timeout=10) as response:
            turn_data = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
            assert "updatedState" in turn_data
            assert "decision" in turn_data
            assert "termination" in turn_data
            print(f"  -> POST /api/interview/turn: OK (Decision: {turn_data['decision']['strategy']})")
    except Exception as e:
        print(f"  [FAIL] Canonical interview flow failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("SUCCESS: All integration endpoints are verified and ready for team connection!")
    print("=" * 60)

if __name__ == "__main__":
    run_smoke_test()

