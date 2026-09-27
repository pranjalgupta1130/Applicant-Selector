"""
Real Gemini Live AI Verification Script (BoardRoom AI - Section 8 of Ralph Master Mission).
Verifies live Gemini API connectivity, structured question generation, answer evaluation,
and adaptive transitions.
If GEMINI_API_KEY is unavailable, reports clearly:
  LIVE GEMINI: NOT VERIFIED — API KEY MISSING
and verifies all deterministic offline fallback contracts.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add ai-service to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from core.config import settings
from core.schemas import CandidateProfile, TargetRole, EvaluationResult
from rag.retriever import KnowledgeRetriever
from generator.pipeline import QuestionGeneratorPipeline
from evaluator.answer_evaluator import GeminiAnswerEvaluator, MockAnswerEvaluator
from adaptive.orchestrator import InterviewOrchestrator

logging.basicConfig(level=logging.WARNING)


def run_verification():
    print("=" * 60)
    print("BOARDROOM AI — LIVE AI SUBSYSTEM VERIFICATION")
    print("=" * 60)

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        print("\n[!] LIVE GEMINI: NOT VERIFIED — API KEY MISSING")
        print("    (To test live Gemini API calls, set GEMINI_API_KEY in .env)")
        print("\n--> Verifying Offline Deterministic Subsystem Contracts:")
        
        # 1. Retrieval
        retriever = KnowledgeRetriever(use_embeddings=False)
        res = retriever.retrieve("database indexes", top_k=2)
        assert res.total_found > 0, "Fallback retrieval failed"
        print("    [1] Knowledge Retrieval Fallback:     PASS")

        # 2. Generator Fallback
        pipeline = QuestionGeneratorPipeline(retriever=retriever)
        candidate = CandidateProfile(skills=["Python", "SQL"], experience_years=2.0)
        role = TargetRole(title="Backend Software Engineer")
        q = pipeline.generate(
            candidate=candidate,
            role=role,
            stage="fundamentals",
            competency="backend",
            difficulty=2
        )
        assert q is not None and q.text, "Fallback question generation failed"
        assert q.relevanceScore >= 60, "Fallback question relevance score invalid"
        print("    [2] Deterministic Question Generator: PASS")

        # 3. Answer Evaluator Fallback
        evaluator = MockAnswerEvaluator()
        concepts_str = ", ".join(q.expectedConcepts[:2]) if q.expectedConcepts else "backend architecture"
        sample_answer = f"We implement {concepts_str} in our service pipeline to ensure structured request execution and robust error handling."
        eval_res = evaluator.evaluate(q, sample_answer)
        assert eval_res.score >= 50, f"Fallback answer evaluation failed with score {eval_res.score}"
        assert eval_res.isFallback is True
        print("    [3] Deterministic Answer Evaluator:   PASS")

        # 4. Adaptive Closed-Loop Turn
        orchestrator = InterviewOrchestrator(retriever=retriever)
        session = orchestrator.start_interview(candidate, role)
        turn_res = orchestrator.process_turn(
            current_question=session.openingQuestion,
            candidate_answer="We design endpoints to be idempotent and maintain stateless request handling.",
            interview_state=session.interviewState,
            candidate=candidate,
            role=role
        )
        assert turn_res.nextQuestion is not None
        assert turn_res.decision.strategy is not None
        print("    [4] Closed-Loop Adaptive Turn:        PASS")

        # 5. Scorecard Generation
        from adaptive.scorecard_engine import ScorecardEngine
        from adaptive.state import InterviewState
        state = InterviewState(**turn_res.updatedState)
        scorecard = ScorecardEngine.generate_scorecard(state=state, candidate=candidate, role=role)
        assert scorecard.overallScore >= 0
        assert scorecard.overallConfidence >= 0.0
        print("    [5] Selector Scorecard Generation:    PASS")

        print("\nOFFLINE DETERMINISTIC CONTRACTS: ALL PASS")
        print("=" * 60)
        return 0

    print(f"\n[+] GEMINI_API_KEY detected. Model: {settings.DEFAULT_LLM_MODEL}")
    print("--> Executing Live End-to-End Gemini Verification...")

    # Step 1: Live Connectivity & Client Test
    print("    [1] Testing Gemini API Connectivity...")
    try:
        from google import genai
        from google.genai import types
        timeout_ms = int(settings.LLM_TIMEOUT_SECONDS * 1000)
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_ms))
        ping_resp = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents="Say 'OK' if you are online."
        )
        assert ping_resp.text, "Empty response from Gemini ping"
        print("        Connectivity: PASS")
    except Exception as e:
        print(f"        Connectivity FAILED: {e}")
        return 1

    # Step 2: Live Question Generation with Grounding & Citation
    print("    [2] Testing Live Question Generation with RAG Grounding...")
    retriever = KnowledgeRetriever(use_embeddings=True)
    pipeline = QuestionGeneratorPipeline(retriever=retriever)
    candidate = CandidateProfile(skills=["Python", "PostgreSQL", "Docker"], experience_years=3.0)
    role = TargetRole(title="Senior Backend Engineer")
    try:
        question = pipeline.generate(
            candidate=candidate,
            role=role,
            stage="role_technical",
            competency="database",
            difficulty=3,
            question_type="trade_off",
            adaptive_reason="Probing database index internals"
        )
        assert question is not None, "Live generation returned None"
        print(f"        Generated Question: '{question.text[:70]}...'")
        print(f"        Relevance Score: {question.relevanceScore}/100")
        print(f"        Sources: {question.sources}")
        print(f"        Expected Concepts: {question.expectedConcepts}")
        assert question.relevanceScore >= 65, "Relevance score below quality threshold"
        print("        Generation & Relevance Gate: PASS")
    except Exception as e:
        print(f"        Generation FAILED: {e}")
        return 1

    # Step 3: Live Semantic Answer Evaluation
    print("    [3] Testing Live Semantic Answer Evaluation...")
    evaluator = GeminiAnswerEvaluator()
    sample_answer = (
        "We construct a B+Tree on the indexed columns so lookups don't do full table scans. "
        "Point queries traverse the tree in O(log N) disk reads, and leaf node pointers allow sequential range scans. "
        "The trade-off is write amplification because insertions trigger node splits and tree rebalancing."
    )
    try:
        eval_result = evaluator.evaluate(question, sample_answer)
        print(f"        Score: {eval_result.score}/100")
        print(f"        Covered Concepts: {eval_result.coveredConcepts}")
        print(f"        Technical Correctness: {eval_result.technicalCorrectness}")
        print(f"        Completeness: {eval_result.completeness}")
        print(f"        Relevance: {eval_result.relevance}")
        print(f"        Depth: {eval_result.depth}")
        print(f"        Reasoning: {eval_result.reasoning}")
        assert eval_result.score >= 70, f"Expected strong score for deep answer, got {eval_result.score}"
        print("        Live Evaluation: PASS")
    except Exception as e:
        print(f"        Evaluation FAILED: {e}")
        return 1

    # Step 4: Live Adaptive Next-Question Transition
    orchestrator = InterviewOrchestrator(retriever=retriever, generator=pipeline)
    session = orchestrator.start_interview(candidate, role)
    turn_res = orchestrator.process_turn(
        current_question=session.openingQuestion,
        candidate_answer=sample_answer,
        interview_state=session.interviewState,
        candidate=candidate,
        role=role
    )
    print(f"        Next Question: '{turn_res.nextQuestion.text[:70]}...'")
    print(f"        Adaptive Strategy: {turn_res.decision.strategy}")
    print(f"        Calibrated Difficulty: {turn_res.decision.nextDifficulty}/5")
    print(f"        Target Competency: {turn_res.decision.nextCompetency}")
    assert turn_res.nextQuestion is not None
    print("        Closed Loop: PASS")

    print("\nALL LIVE AI VERIFICATION CHECKS: PASS")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(run_verification())
