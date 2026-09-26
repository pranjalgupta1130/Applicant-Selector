"""
Interview Simulation Engine for BoardRoom AI.
Runs end-to-end simulated interviews across 5 distinct candidate archetypes:
1. Strong Candidate (escalates to diff 5)
2. Weak Candidate (de-escalates / pins to diff 1, gap probed)
3. Backend Specialist with System-Design Weakness (pivots & probes architectural gap)
4. Resume-Heavy Candidate with Knowledge Gaps (calibrates and probes fundamentals)
5. LLM Outage / Fallback Scenario (full 5-question journey under 100% simulated LLM outage)
"""

from typing import List, Dict, Any, Optional
from unittest.mock import patch

from core.schemas import CandidateProfile, TargetRole, QuestionObject
from rag.retriever import KnowledgeRetriever
from generator.pipeline import QuestionGeneratorPipeline
from adaptive.state import InterviewState
from adaptive.policy import AdaptiveInterviewPolicy, PolicyDecision


class InterviewSimulator:
    """
    Simulates a multi-turn interview session using InterviewState, AdaptiveInterviewPolicy,
    and QuestionGeneratorPipeline.
    """

    def __init__(self, retriever: Optional[KnowledgeRetriever] = None):
        self.retriever = retriever or KnowledgeRetriever()
        self.generator = QuestionGeneratorPipeline(retriever=self.retriever)
        self.role = TargetRole(
            id="backend_engineer",
            title="Backend / Full-Stack Software Engineer",
            required_skills=["Python", "SQL", "REST APIs", "System Design", "Git"]
        )

    def run_simulation(
        self,
        candidate: CandidateProfile,
        scripted_turns: List[Dict[str, Any]],
        force_llm_outage: bool = False
    ) -> Dict[str, Any]:
        """
        Executes a multi-turn interview.
        For each turn:
          1. Policy evaluates InterviewState -> decides next stage, competency, difficulty, question_type, strategy
          2. Pipeline generates question based on policy decision
          3. Evaluator response is simulated (score, covered concepts, missing concepts)
          4. State records turn and updates concept coverage
        """
        state = InterviewState(
            candidate_id=candidate.id or "cand_sim",
            role_id=self.role.id,
            current_stage="ice_breaker",
            current_competency="ice_breaker",
            difficulty=1
        )

        turns_log = []

        patcher = None
        if force_llm_outage:
            patcher = patch.object(self.generator, "_generate_with_gemini", side_effect=RuntimeError("Simulated LLM 503 Outage"))
            patcher.start()

        try:
            for turn_idx, turn_input in enumerate(scripted_turns, 1):
                # 1. Policy determines next step
                decision: PolicyDecision = AdaptiveInterviewPolicy.evaluate_next_step(state)

                if decision.strategy == "conclude_interview":
                    turns_log.append({
                        "turn": turn_idx,
                        "action": "conclude_interview",
                        "rationale": decision.rationale
                    })
                    break

                # 2. Pipeline generates question grounded in policy decision
                q: QuestionObject = self.generator.generate(
                    candidate=candidate,
                    role=self.role,
                    stage=decision.next_stage,
                    competency=decision.next_competency,
                    difficulty=decision.next_difficulty,
                    previous_questions=state.previous_questions,
                    previous_missing_concepts=decision.target_concepts or state.missing_concepts,
                    question_type=decision.recommended_question_type,
                    adaptive_reason=decision.adaptive_reason
                )

                # 3. Simulate evaluation signal for this turn
                sim_score = turn_input.get("score", 75)
                sim_covered = turn_input.get("covered", q.expectedConcepts[:2])
                sim_missing = turn_input.get("missing", [])

                # 4. Record turn into InterviewState
                state.record_turn(
                    question_id=q.id,
                    question_text=q.text,
                    question_type=q.questionType or decision.recommended_question_type,
                    stage=decision.next_stage,
                    competency=decision.next_competency,
                    difficulty=decision.next_difficulty,
                    score=sim_score,
                    covered_concepts=sim_covered,
                    missing_concepts=sim_missing
                )

                turns_log.append({
                    "turn": turn_idx,
                    "stage": decision.next_stage,
                    "competency": decision.next_competency,
                    "difficulty": decision.next_difficulty,
                    "strategy": decision.strategy,
                    "question_type": q.questionType,
                    "question_id": q.id,
                    "question_text": q.text,
                    "relevance_score": q.relevanceScore,
                    "is_fallback": q.isFallback,
                    "sources": q.sources,
                    "simulated_score": sim_score,
                    "covered_concepts": sim_covered,
                    "missing_concepts": sim_missing,
                    "policy_rationale": decision.rationale
                })

        finally:
            if patcher:
                patcher.stop()

        return {
            "candidate": candidate.name,
            "turns_completed": len(turns_log),
            "final_stage": state.current_stage,
            "final_difficulty": state.difficulty,
            "difficulty_trend": state.difficulty_trend,
            "score_history": state.score_history,
            "concept_summary": state.get_concept_coverage_summary(),
            "turns": turns_log
        }


# -------------------------------------------------------------
# 5 Pre-Configured Golden Scenarios
# -------------------------------------------------------------

def run_all_5_golden_simulations() -> Dict[str, Any]:
    sim = InterviewSimulator()
    results = {}

    # Scenario 1: Strong Candidate (Escalates to difficulty 5)
    cand_strong = CandidateProfile(
        name="Jordan - Senior Backend Lead",
        skills=["Python", "FastAPI", "PostgreSQL", "Redis", "Distributed Systems"],
        experience_years=5.0
    )
    turns_strong = [
        {"score": 92, "covered": ["tech stack", "backend ownership"], "missing": []},
        {"score": 88, "covered": ["HTTP verbs", "idempotency"], "missing": []},
        {"score": 90, "covered": ["JWT structure", "refresh token rotation"], "missing": []},
        {"score": 85, "covered": ["B-Tree index", "query execution plan"], "missing": []},
        {"score": 89, "covered": ["CAP theorem", "eventual consistency"], "missing": []},
        {"score": 94, "covered": ["production triage", "circuit breaker"], "missing": []}
    ]
    results["strong_candidate"] = sim.run_simulation(cand_strong, turns_strong)

    # Scenario 2: Weak Candidate (Struggles, difficulty pinned at 1, gap probed)
    cand_weak = CandidateProfile(
        name="Casey - Junior Applicant",
        skills=["Python Basics"],
        experience_years=0.5
    )
    turns_weak = [
        {"score": 60, "covered": ["background"], "missing": []},
        {"score": 42, "covered": ["basic loop"], "missing": ["process vs thread", "shared memory"]},
        {"score": 45, "covered": ["thread definition"], "missing": ["shared memory race conditions"]},
        {"score": 40, "covered": [], "missing": ["REST constraints"]},
        {"score": 48, "covered": ["GET verb"], "missing": ["idempotency"]},
        {"score": 45, "covered": [], "missing": ["SQL transactions"]}
    ]
    results["weak_candidate"] = sim.run_simulation(cand_weak, turns_weak)

    # Scenario 3: Backend Specialist with System-Design Weakness
    cand_specialist = CandidateProfile(
        name="Robin - API Specialist",
        skills=["Python", "SQL", "FastAPI"],
        experience_years=3.0
    )
    turns_specialist = [
        {"score": 90, "covered": ["API background"], "missing": []},
        {"score": 86, "covered": ["REST verbs", "status codes"], "missing": []},
        {"score": 88, "covered": ["JWT auth", "cookies"], "missing": []},
        {"score": 46, "covered": ["sharding definition"], "missing": ["cross-shard queries", "resharding"]},
        {"score": 75, "covered": ["cross-shard queries"], "missing": []},
        {"score": 85, "covered": ["incident triage"], "missing": []}
    ]
    results["specialist_with_gap"] = sim.run_simulation(cand_specialist, turns_specialist)

    # Scenario 4: Resume-Heavy Candidate with Knowledge Gaps
    cand_resume = CandidateProfile(
        name="Taylor - Claimed 6 Yrs Senior",
        skills=["Architecture", "Python", "Cloud"],
        experience_years=6.0
    )
    turns_resume = [
        {"score": 78, "covered": ["leadership"], "missing": []},
        {"score": 52, "covered": ["B-Tree reads"], "missing": ["B-Tree update overhead", "write amplification"]},
        {"score": 76, "covered": ["B-Tree update overhead"], "missing": []},
        {"score": 50, "covered": ["cache aside"], "missing": ["cache stampede prevention"]},
        {"score": 74, "covered": ["mutex locks"], "missing": []},
        {"score": 80, "covered": ["post-mortem"], "missing": []}
    ]
    results["resume_heavy_candidate"] = sim.run_simulation(cand_resume, turns_resume)

    # Scenario 5: Full LLM Outage / Fallback Scenario
    cand_fallback = CandidateProfile(
        name="Morgan - Resilient Fallback",
        skills=["Python", "SQL"],
        experience_years=2.5
    )
    turns_fallback = [
        {"score": 80, "covered": ["background"], "missing": []},
        {"score": 82, "covered": ["OOP abstraction"], "missing": []},
        {"score": 80, "covered": ["REST idempotency"], "missing": []},
        {"score": 85, "covered": ["B-Tree index"], "missing": []},
        {"score": 82, "covered": ["distributed cache"], "missing": []},
        {"score": 85, "covered": ["production triage"], "missing": []}
    ]
    results["llm_outage_scenario"] = sim.run_simulation(cand_fallback, turns_fallback, force_llm_outage=True)

    return results
