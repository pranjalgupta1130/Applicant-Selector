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

from core.schemas import CandidateProfile, TargetRole, QuestionObject, EvaluationResult, TurnResponse
from rag.retriever import KnowledgeRetriever
from generator.pipeline import QuestionGeneratorPipeline
from adaptive.state import InterviewState
from adaptive.policy import AdaptiveInterviewPolicy, PolicyDecision
from adaptive.orchestrator import InterviewOrchestrator



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


# -------------------------------------------------------------
# Phase C: Closed-Loop Interview Simulator
# -------------------------------------------------------------

class ClosedLoopInterviewSimulator:
    """
    Closed-loop interview simulation engine for BoardRoom AI (Phase C).
    Coordinates the full cycle:
    Question -> Answer -> Evaluator -> State Update -> Policy Decision -> Target Concept -> Next Question.
    """

    def __init__(
        self,
        retriever: Optional[KnowledgeRetriever] = None,
        generator: Optional[QuestionGeneratorPipeline] = None
    ):
        self.retriever = retriever or KnowledgeRetriever()
        self.generator = generator or QuestionGeneratorPipeline(retriever=self.retriever)
        self.orchestrator = InterviewOrchestrator(
            retriever=self.retriever,
            generator=self.generator
        )
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
        Runs an end-to-end closed loop interview across scripted candidate turns.
        """
        patcher = None
        if force_llm_outage:
            patcher = patch.object(self.generator, "_generate_with_gemini", side_effect=RuntimeError("Simulated LLM Outage"))
            patcher.start()

        try:
            # 1. Initialize interview session with opening ice-breaker question
            start_res = self.orchestrator.start_interview(candidate=candidate, role=self.role)
            current_question = start_res.openingQuestion
            current_state = start_res.interviewState

            turns_log = []

            for turn_idx, turn_input in enumerate(scripted_turns, 1):
                # Answer text
                cand_answer = turn_input.get(
                    "answer",
                    f"Candidate technical response for turn {turn_idx} addressing {', '.join(turn_input.get('covered', ['core fundamentals']))}."
                )

                # Simulated evaluation object from Member 4
                eval_input = None
                if "score" in turn_input:
                    eval_input = EvaluationResult(
                        score=turn_input["score"],
                        coveredConcepts=turn_input.get("covered", []),
                        missingConcepts=turn_input.get("missing", []),
                        reasoning=turn_input.get("reasoning", f"Turn {turn_idx} performance evaluated."),
                        confidence=turn_input.get("confidence", 0.90)
                    )

                # Execute turn through orchestrator
                turn_res: TurnResponse = self.orchestrator.process_turn(
                    current_question=current_question,
                    candidate_answer=cand_answer,
                    interview_state=current_state,
                    evaluation=eval_input,
                    candidate=candidate,
                    role=self.role
                )

                turns_log.append({
                    "turn": turn_idx,
                    "question_asked": {
                        "id": current_question.id,
                        "text": current_question.text,
                        "stage": current_question.stage,
                        "competency": current_question.competency,
                        "difficulty": current_question.difficulty,
                        "relevance_score": current_question.relevanceScore,
                        "is_fallback": current_question.isFallback
                    },
                    "evaluation": {
                        "score": turn_res.evaluation.score,
                        "covered_concepts": turn_res.evaluation.coveredConcepts,
                        "missing_concepts": turn_res.evaluation.missingConcepts,
                        "confidence": turn_res.evaluation.confidence
                    },
                    "decision": {
                        "strategy": turn_res.decision.strategy,
                        "next_difficulty": turn_res.decision.nextDifficulty,
                        "next_competency": turn_res.decision.nextCompetency,
                        "target_concepts": turn_res.decision.targetConcepts,
                        "question_type": turn_res.decision.questionType,
                        "reason": turn_res.decision.reason
                    },
                    "trace": turn_res.trace.model_dump(),
                    "termination": turn_res.termination.model_dump(),
                    "next_question_generated": turn_res.nextQuestion is not None
                })

                current_state = turn_res.updatedState
                if turn_res.termination.shouldTerminate:
                    break

                if turn_res.nextQuestion is not None:
                    current_question = turn_res.nextQuestion
                else:
                    break

        finally:
            if patcher:
                patcher.stop()

        return {
            "candidate": candidate.name,
            "turns_completed": len(turns_log),
            "final_state": current_state,
            "final_difficulty": current_state.get("difficulty", 1),
            "difficulty_trend": current_state.get("difficulty_trend", []),
            "score_history": current_state.get("score_history", []),
            "demonstrated_concepts": current_state.get("demonstrated_concepts", []),
            "missing_concepts": current_state.get("missing_concepts", []),
            "recovered_concepts": current_state.get("recovered_concepts", []),
            "persistent_weaknesses": current_state.get("persistent_weaknesses", []),
            "turns": turns_log
        }


def run_strong_candidate_simulation() -> Dict[str, Any]:
    """Golden Simulation A: Strong Candidate (85 -> 88 -> 91 -> 87 -> 93)."""
    sim = ClosedLoopInterviewSimulator()
    cand = CandidateProfile(
        name="Alex Rivera - Senior Engineer",
        skills=["Python", "FastAPI", "PostgreSQL", "Redis", "Distributed Systems"],
        experience_years=5.0
    )
    turns = [
        {"score": 85, "covered": ["REST APIs", "statelessness"], "missing": []},
        {"score": 88, "covered": ["HTTP status codes", "idempotency"], "missing": []},
        {"score": 91, "covered": ["JWT authentication", "refresh token rotation"], "missing": []},
        {"score": 87, "covered": ["B-Tree indexing", "composite indexing"], "missing": []},
        {"score": 93, "covered": ["horizontal scaling", "load balancing"], "missing": []}
    ]
    return sim.run_simulation(cand, turns)


def run_weak_candidate_simulation() -> Dict[str, Any]:
    """Golden Simulation B: Weak Candidate (52 -> 47 -> 43 -> 51 -> 56)."""
    sim = ClosedLoopInterviewSimulator()
    cand = CandidateProfile(
        name="Sam Taylor - Junior Applicant",
        skills=["Python Basics"],
        experience_years=0.5
    )
    turns = [
        {"score": 52, "covered": ["software architecture overview"], "missing": ["REST APIs"]},
        {"score": 47, "covered": [], "missing": ["REST APIs", "HTTP status codes"]},
        {"score": 43, "covered": [], "missing": ["REST APIs", "statelessness"]},
        {"score": 51, "covered": ["HTTP status codes"], "missing": ["idempotency"]},
        {"score": 56, "covered": ["idempotency"], "missing": ["concurrency race conditions"]}
    ]
    return sim.run_simulation(cand, turns)


def run_recovery_candidate_simulation() -> Dict[str, Any]:
    """Golden Simulation C: Strong -> Weak -> Recovery (88 -> 91 -> 48 -> 52 -> 84 -> 89)."""
    sim = ClosedLoopInterviewSimulator()
    cand = CandidateProfile(
        name="Jordan Lee - Mid-Level Engineer",
        skills=["Python", "SQL", "FastAPI"],
        experience_years=3.0
    )
    turns = [
        {"score": 88, "covered": ["software architecture overview", "recent technical project"], "missing": []},
        {"score": 91, "covered": ["REST APIs", "statelessness"], "missing": []},
        {"score": 48, "covered": [], "missing": ["JWT authentication", "refresh token rotation"]},
        {"score": 52, "covered": ["JWT structure"], "missing": ["JWT authentication"]},
        {"score": 84, "covered": ["JWT authentication", "refresh token rotation"], "missing": []},
        {"score": 89, "covered": ["B-Tree indexing", "indexing trade-offs"], "missing": []}
    ]
    return sim.run_simulation(cand, turns)


def run_specialist_candidate_simulation() -> Dict[str, Any]:
    """Golden Simulation D: Specialist (backend=90, database=88, system_design=45)."""
    sim = ClosedLoopInterviewSimulator()
    cand = CandidateProfile(
        name="Chris Morgan - Backend & DB Specialist",
        skills=["Python", "PostgreSQL", "Query Optimization"],
        experience_years=4.0
    )
    turns = [
        {"score": 90, "covered": ["software architecture overview"], "missing": []},
        {"score": 90, "covered": ["REST APIs", "idempotency"], "missing": []},
        {"score": 88, "covered": ["B-Tree indexing", "database transactions"], "missing": []},
        {"score": 88, "covered": ["composite indexing", "indexing trade-offs"], "missing": []},
        {"score": 45, "covered": [], "missing": ["horizontal scaling", "load balancing"]},
        {"score": 75, "covered": ["horizontal scaling"], "missing": []}
    ]
    return sim.run_simulation(cand, turns)



def run_insufficient_evidence_simulation() -> Dict[str, Any]:
    """Golden Simulation E: Insufficient Evidence Candidate."""
    sim = ClosedLoopInterviewSimulator()
    cand = CandidateProfile(
        name="Pat Quinn - Partial Session",
        skills=["Python", "FastAPI"],
        experience_years=2.0
    )
    # Only 3 turns: 2 on backend, 1 on database, 0 on system_design
    turns = [
        {"score": 85, "covered": ["software architecture overview"], "missing": []},
        {"score": 90, "covered": ["REST APIs", "idempotency"], "missing": []},
        {"score": 82, "covered": ["B-Tree indexing"], "missing": []}
    ]
    return sim.run_simulation(cand, turns)


def run_all_closed_loop_simulations() -> Dict[str, Any]:
    """Runs all 5 golden closed-loop simulations plus outage scenario."""
    return {
        "strong_candidate": run_strong_candidate_simulation(),
        "weak_candidate": run_weak_candidate_simulation(),
        "recovery_candidate": run_recovery_candidate_simulation(),
        "specialist_candidate": run_specialist_candidate_simulation(),
        "insufficient_evidence_candidate": run_insufficient_evidence_simulation(),
        "llm_outage_scenario": ClosedLoopInterviewSimulator().run_simulation(
            CandidateProfile(name="Morgan Fallback", skills=["Python", "SQL"]),
            [
                {"score": 85, "covered": ["REST APIs"], "missing": []},
                {"score": 88, "covered": ["B-Tree indexing"], "missing": []},
                {"score": 86, "covered": ["load balancing"], "missing": []}
            ],
            force_llm_outage=True
        )
    }


