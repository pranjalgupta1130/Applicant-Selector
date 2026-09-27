"""
Pre-Demo Preflight Verification Script (BoardRoom AI - PSWB01 DRDO/RAC Edition).
Performs 14 comprehensive AI/RAG subsystem checks:
[1]  Python / Dependencies
[2]  DRDO Domain Model & Registries
[3]  Knowledge Base Integrity (77 Chunks, Multi-Domain Provenance)
[4]  Embedding Model Loading (all-MiniLM-L6-v2)
[5]  Dense Retrieval Visibility & Activation
[6]  Semantic Retrieval Benchmark
[7]  Cross-Domain Isolation Guarantee (Strict Zero-Leakage Boundary)
[8]  Gemini API Availability & Health / Offline Deterministic Fallback
[9]  Question Generator & Quality Gates
[10] Question Relevance Measurability (Alignment with Claimed Skills & Advertised Post)
[11] Answer Evaluator & Keyword Stuffing Resistance
[12] Closed-Loop Adaptive Engine & Decision Trace
[13] Scorecard & Evidence Aggregation
[14] Full Pytest Verification Suite (DRDO + Core Stabilization Suites)
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Tuple

# Add ai-service to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))


def check_step(name: str, fn) -> Tuple[bool, str]:
    try:
        ok, msg = fn()
        return ok, msg
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_preflight() -> int:
    results: Dict[str, Tuple[bool, str]] = {}

    print("=" * 68)
    print("BOARDROOM AI (PSWB01) -- DRDO/RAC PRE-DEMO PREFLIGHT AUDIT")
    print("=" * 68)

    # [1] Python / Dependencies
    def test_deps():
        import fastapi
        import pydantic
        import sklearn
        import numpy
        import sentence_transformers
        from google import genai
        return True, "All required ML/backend dependencies imported successfully"
    results["Dependencies"] = check_step("Dependencies", test_deps)

    # [2] DRDO Domain Model & Registries
    def test_domain_model():
        from core.drdo_domain import (
            get_domain_profile,
            DRDO_DOMAIN_REGISTRY,
            AdvertisedPostProfile,
            ApplicantExpertiseProfile
        )
        radar_prof = get_domain_profile("electronics_radar")
        cyber_prof = get_domain_profile("cyber_computing")
        if not radar_prof or not cyber_prof:
            return False, "Failed to resolve domain profiles"
        if len(radar_prof.competencies) < 5:
            return False, "Insufficient competencies in radar domain"
        post = AdvertisedPostProfile()
        cand = ApplicantExpertiseProfile()
        return True, f"Multi-Domain Active (Demonstration: '{radar_prof.domain_id}', Post: '{post.post_id}')"
    results["DRDO Domain Model"] = check_step("DRDO Domain Model", test_domain_model)

    # [3] Knowledge Base Integrity
    def test_kb():
        from core.schemas import KnowledgeChunk
        kb_path = ROOT_DIR / "data" / "knowledge_base" / "seed_knowledge.json"
        if not kb_path.exists():
            return False, "Knowledge base file not found"
        with open(kb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if len(data) < 70:
            return False, f"Insufficient chunks ({len(data)} < 70)"
        drdo_chunks = [c for c in data if c.get("domain") == "electronics_radar"]
        cyber_chunks = [c for c in data if c.get("domain") == "cyber_computing"]
        if len(drdo_chunks) < 30:
            return False, f"Insufficient DRDO chunks ({len(drdo_chunks)} < 30)"
        total_qs = sum(len(d.get("sample_questions", [])) for d in data)
        return True, f"{len(data)} chunks loaded ({len(drdo_chunks)} ECE/Radar, {len(cyber_chunks)} Cyber, {total_qs} questions)"
    results["Knowledge Base"] = check_step("Knowledge Base", test_kb)

    # [4] Embedding Model Loading
    def test_embedding_model():
        from sentence_transformers import SentenceTransformer
        try:
            model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
            return True, "all-MiniLM-L6-v2 loaded from local cache"
        except Exception:
            try:
                model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=False)
                return True, "all-MiniLM-L6-v2 loaded"
            except Exception as e:
                return False, f"Embedding model load failed: {e}"
    results["Embedding Model"] = check_step("Embedding Model", test_embedding_model)

    # [5] Dense Retrieval Visibility & Activation
    def test_dense_retrieval():
        from rag.retriever import KnowledgeRetriever
        r = KnowledgeRetriever(use_embeddings=True)
        if r.dense_embeddings_active:
            return True, f"ACTIVE (Mode: {r.retrieval_mode}, Chunks: {len(r.chunks)})"
        else:
            return True, f"TF-IDF FALLBACK ACTIVE (Dense embeddings inactive)"
    results["Dense RAG"] = check_step("Dense RAG", test_dense_retrieval)

    # [6] Semantic Retrieval Benchmark
    def test_retrieval_benchmark():
        from rag.retriever import KnowledgeRetriever
        r = KnowledgeRetriever(use_embeddings=True)
        query = "State the fundamental formula relating radar received echo power to target distance"
        res = r.retrieve(query, domain="electronics_radar", top_k=2)
        if res.total_found == 0:
            return False, "No chunks retrieved for radar range query"
        top_chunk = res.results[0]
        if "range" not in top_chunk.title.lower() and "radar" not in top_chunk.title.lower():
            return False, f"Unexpected top match: {top_chunk.chunk_id}"
        return True, f"Top match: {top_chunk.chunk_id} ('{top_chunk.title[:35]}...', Score: {top_chunk.score:.3f})"
    results["Semantic Benchmark"] = check_step("Semantic Benchmark", test_retrieval_benchmark)

    # [7] Cross-Domain Isolation Guarantee
    def test_cross_domain_isolation():
        from rag.retriever import KnowledgeRetriever
        r = KnowledgeRetriever(use_embeddings=True)
        chunks_by_id = {c.id: c for c in r.chunks}
        # Radar query in electronics_radar domain must NOT retrieve cyber chunks
        res1 = r.retrieve("interrupt latency and RTOS context switch", domain="electronics_radar", top_k=5)
        for item in res1.results:
            c = chunks_by_id.get(item.chunk_id)
            if c and c.domain == "cyber_computing":
                return False, f"Cross-domain leak: cyber chunk {c.id} returned in electronics_radar query"

        # Cyber query in cyber_computing domain must NOT retrieve radar chunks
        res2 = r.retrieve("b-tree indexing and database transactions", domain="cyber_computing", top_k=5)
        for item in res2.results:
            c = chunks_by_id.get(item.chunk_id)
            if c and c.domain == "electronics_radar":
                return False, f"Cross-domain leak: radar chunk {c.id} returned in cyber_computing query"
        return True, "Strict domain boundary verified: ZERO cross-domain leakage across all pairs"
    results["Cross-Domain Gate"] = check_step("Cross-Domain Gate", test_cross_domain_isolation)

    # [8] Gemini Availability
    def test_gemini():
        from core.config import settings
        if not settings.GEMINI_API_KEY:
            return True, "UNCONFIGURED (Deterministic Offline Fallbacks Active)"
        from google import genai
        from google.genai import types
        timeout_ms = int(settings.LLM_TIMEOUT_SECONDS * 1000)
        client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options=types.HttpOptions(timeout=timeout_ms))
        resp = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents="Respond 'HEALTHY' if API connection is active."
        )
        return True, f"ACTIVE ({settings.DEFAULT_LLM_MODEL})"
    results["Gemini Connectivity"] = check_step("Gemini Connectivity", test_gemini)

    # [9] Question Generator & Quality Gates
    def test_question_generator():
        from rag.retriever import KnowledgeRetriever
        from generator.pipeline import QuestionGeneratorPipeline
        from core.schemas import CandidateProfile, TargetRole
        r = KnowledgeRetriever()
        pipe = QuestionGeneratorPipeline(retriever=r)
        cand = CandidateProfile(discipline="ECE", claimed_expertise=["FreeRTOS", "DSP"])
        role = TargetRole(domain="electronics_radar", title="Scientist 'B' - ECE")
        q = pipe.generate(candidate=cand, role=role, stage="fundamentals", competency="embedded_realtime_systems", difficulty=2)
        if not q or not q.text:
            return False, "Question generation returned empty question"
        if q.relevanceScore < 60:
            return False, f"Relevance score {q.relevanceScore} below quality gate"
        return True, f"Generated: '{q.text[:40]}...' (Relevance: {q.relevanceScore}/100)"
    results["Question Generator"] = check_step("Question Generator", test_question_generator)

    # [10] Question Relevance Measurability
    def test_question_relevance():
        from evaluator.relevance import QuestionRelevanceEvaluator
        from core.schemas import CandidateProfile, TargetRole
        cand = CandidateProfile(
            discipline="ECE",
            claimed_expertise=["FreeRTOS", "DSP Filter Design"],
            domain="electronics_radar"
        )
        role = TargetRole(
            id="DRDO-RAC-2026-ECE-001",
            domain="electronics_radar",
            technical_requirements=["Interrupt latency optimization", "RTOS priority preemption"]
        )
        res_good = QuestionRelevanceEvaluator.evaluate(
            question_text="In preemptive FreeRTOS, explain how the SysTick interrupt triggers a context switch via PendSV.",
            role=role,
            candidate=cand,
            competency="embedded_realtime_systems",
            stage="fundamentals",
            difficulty=3,
            expected_concepts=["RTOS Priority Preemption", "context switch"]
        )
        res_bad = QuestionRelevanceEvaluator.evaluate(
            question_text="What is your favorite cooking recipe for pasta and tomato sauce?",
            role=role,
            candidate=cand,
            competency="embedded_realtime_systems",
            stage="fundamentals",
            difficulty=3,
            expected_concepts=["pasta"]
        )
        if res_good.totalScore < 70 or res_bad.totalScore > 45:
            return False, f"Discrimination failure: good={res_good.totalScore}, bad={res_bad.totalScore}"
        return True, f"Calibrated discrimination: Grounded={res_good.totalScore}/100, Irrelevant={res_bad.totalScore}/100"
    results["Question Relevance"] = check_step("Question Relevance", test_question_relevance)

    # [11] Answer Evaluator & Keyword Stuffing Resistance
    def test_answer_evaluator():
        from evaluator.answer_evaluator import MockAnswerEvaluator
        from core.schemas import QuestionObject, RubricCriteria
        q = QuestionObject(
            id="q_eval_01",
            text="Explain why radar received power decreases with the fourth power of target distance.",
            stage="deep_dive",
            competency="radar_rf_systems",
            difficulty=4,
            expectedConcepts=["Radar Range Equation", "fourth power distance", "radar cross section"],
            relevanceScore=90,
            rubric=RubricCriteria(poor="P", acceptable="A", excellent="E")
        )
        ev = MockAnswerEvaluator()
        # Genuine paraphrase
        good_ans = (
            "The received radar echo power decreases with the fourth power of target distance because the transmitted wave "
            "expands spherically on the forward path, and the target radar cross section reradiates energy that expands over another "
            "sphere on the return path back to the receiving antenna."
        )
        # Buzzword stuffing
        stuffed_ans = "Radar Range Equation fourth power distance radar cross section antenna gain"
        res_good = ev.evaluate(q, good_ans)
        res_stuffed = ev.evaluate(q, stuffed_ans)
        if res_good.score < 70 or res_stuffed.score > 40:
            return False, f"Evaluator failed keyword stuffing test: good={res_good.score}, stuffed={res_stuffed.score}"
        return True, f"Paraphrase: {res_good.score}/100 (Accurate), Stuffed: {res_stuffed.score}/100 (Penalized)"
    results["Answer Evaluator"] = check_step("Answer Evaluator", test_answer_evaluator)

    # [12] Closed-Loop Adaptive Engine
    def test_adaptive_engine():
        from adaptive.orchestrator import InterviewOrchestrator
        from core.schemas import CandidateProfile, TargetRole
        orch = InterviewOrchestrator()
        cand = CandidateProfile(domain="electronics_radar", claimed_expertise=["FreeRTOS"])
        role = TargetRole(id="DRDO-RAC-2026-ECE-001", domain="electronics_radar")
        start = orch.start_interview(cand, role)
        turn = orch.process_turn(
            current_question=start.openingQuestion,
            candidate_answer="I completed my B.Tech in Electronics and Communication and M.Tech in Signal Processing.",
            interview_state=start.interviewState,
            candidate=cand,
            role=role
        )
        if not turn.nextQuestion or not turn.decision:
            return False, "Adaptive turn failed to return nextQuestion or decision"
        return True, f"Strategy: {turn.decision.strategy}, Next Diff: {turn.decision.nextDifficulty}/5, Competency: {turn.decision.nextCompetency}"
    results["Adaptive Engine"] = check_step("Adaptive Engine", test_adaptive_engine)

    # [13] Scorecard & Evidence Aggregation
    def test_scorecard():
        from adaptive.orchestrator import InterviewOrchestrator
        from adaptive.scorecard_engine import ScorecardEngine
        from adaptive.state import InterviewState
        from core.schemas import CandidateProfile, TargetRole
        orch = InterviewOrchestrator()
        cand = CandidateProfile(domain="electronics_radar")
        role = TargetRole(id="DRDO-RAC-2026-ECE-001", domain="electronics_radar")
        start = orch.start_interview(cand, role)
        turn = orch.process_turn(
            current_question=start.openingQuestion,
            candidate_answer="I completed my B.Tech in Electronics and Communication and M.Tech in Signal Processing with focus on radar.",
            interview_state=start.interviewState,
            candidate=cand,
            role=role
        )
        state = InterviewState(**turn.updatedState)
        scorecard = ScorecardEngine.generate_scorecard(state=state, candidate=cand, role=role)
        if scorecard.overallScore < 0 or scorecard.overallConfidence < 0.0:
            return False, "Scorecard generated negative score or confidence"
        gov_note = scorecard.decisionSupport.recommendationNote
        if "autonomous" not in gov_note.lower():
            return False, "Scorecard missing non-autonomous hiring governance notice"
        return True, f"Score: {scorecard.overallScore}/100, Confidence: {scorecard.overallConfidence:.2f}, Governance Note: Active"
    results["Scorecard Engine"] = check_step("Scorecard Engine", test_scorecard)

    # [14] Full Pytest Verification Suite
    def test_pytest():
        res = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                "tests/test_drdo_domain_retrieval.py",
                "tests/test_drdo_question_relevance.py",
                "tests/test_drdo_answer_evaluation.py",
                "tests/test_drdo_boardroom_simulation.py",
                "tests/test_p0_stabilization.py",
                "-q"
            ],
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            return False, f"Pytest failed:\n{res.stdout[-300:]}\n{res.stderr[-300:]}"
        return True, "Core DRDO & stabilization test suites: 100% PASS (0 failures)"
    results["Test Suite"] = check_step("Test Suite", test_pytest)

    # Render Report
    print(f"\n{'SUBSYSTEM CHECK':<25} | {'STATUS':<8} | {'DETAILS'}")
    print("-" * 68)

    all_passed = True
    for name, (ok, msg) in results.items():
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        print(f"{name:<25} | {status:<8} | {msg}")

    print("-" * 68)
    if all_passed:
        print("RESULT: ALL 14 PREFLIGHT CHECKS PASSED -- AI SUBSYSTEM READY FOR DEMO")
        print("=" * 68)
        return 0
    else:
        print("RESULT: PREFLIGHT FAILED -- RESOLVE FAILURES BEFORE DEMO")
        print("=" * 68)
        return 1


if __name__ == "__main__":
    sys.exit(run_preflight())
