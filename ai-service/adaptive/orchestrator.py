"""
Central Closed-Loop Interview Orchestrator for BoardRoom AI (Phase C).
Coordinates:
1. Candidate answer reception
2. Answer evaluation ingestion (via Member 4 adapter or mock)
3. InterviewState updates (history, mastery, streaks, trends, recovery)
4. Prerequisite & mastery tracking
5. Adaptive Policy v2 evaluation
6. Deterministic target-concept selection
7. Grounded RAG retrieval & question generation
8. Quality gate enforcement & deterministic fallback
9. Explainable decision trace synthesis
10. Multi-criteria interview termination evaluation
"""

import logging
from typing import Optional, Dict, Any, List

from core.schemas import (
    CandidateProfile,
    TargetRole,
    QuestionObject,
    EvaluationResult,
    DecisionObject,
    DecisionTrace,
    TerminationDecision,
    TurnResponse,
    InterviewStartResponse
)
from adaptive.state import InterviewState
from adaptive.policy import AdaptiveInterviewPolicy, PolicyDecision
from adaptive.prerequisites import ConceptPrerequisiteEngine
from adaptive.target_concept import TargetConceptSelector
from adaptive.confidence import EvidenceConfidenceTracker
from adaptive.termination import InterviewTerminationEngine
from evaluator.answer_evaluator import AnswerEvaluationAdapter, BaseAnswerEvaluator
from generator.pipeline import QuestionGeneratorPipeline
from rag.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


class InterviewOrchestrator:
    """
    Central Orchestrator powering the closed-loop adaptive interview engine.
    Ensures that every subsequent turn is a traceable consequence of previous performance.
    """

    def __init__(
        self,
        retriever: Optional[KnowledgeRetriever] = None,
        generator: Optional[QuestionGeneratorPipeline] = None,
        eval_adapter: Optional[AnswerEvaluationAdapter] = None
    ):
        self.retriever = retriever or KnowledgeRetriever()
        self.generator = generator or QuestionGeneratorPipeline(retriever=self.retriever)
        self.eval_adapter = eval_adapter or AnswerEvaluationAdapter()

    def start_interview(
        self,
        candidate: Optional[CandidateProfile] = None,
        role: Optional[TargetRole] = None
    ) -> InterviewStartResponse:
        """
        Initializes a clean interview state and generates the opening ice-breaker question.
        """
        candidate = candidate or CandidateProfile()
        role = role or TargetRole()

        # Resolve domain if not explicitly provided
        if not getattr(role, "domain", None):
            if any(k in role.id.lower() for k in ("ece", "radar", "drdo", "scientist")):
                role.domain = "electronics_radar"
            else:
                role.domain = "cyber_computing"

        state = InterviewState(
            candidate_id=candidate.id or "cand_default",
            role_id=role.id or "backend_engineer",
            current_stage="ice_breaker",
            current_competency="ice_breaker",
            difficulty=1
        )

        opening_q = self.generator.generate(
            candidate=candidate,
            role=role,
            stage="ice_breaker",
            competency="ice_breaker",
            difficulty=1,
            previous_questions=[],
            previous_missing_concepts=[],
            question_type="conceptual",
            adaptive_reason="Opening interview ice-breaker to assess engineering background and core technical strengths."
        )

        if opening_q and opening_q.id:
            state.used_fallback_ids.append(opening_q.id)

        return InterviewStartResponse(
            interviewState=state.model_dump(),
            openingQuestion=opening_q
        )

    def process_turn(
        self,
        current_question: QuestionObject,
        candidate_answer: str,
        interview_state: Optional[Any] = None,
        evaluation: Optional[Any] = None,
        candidate: Optional[CandidateProfile] = None,
        role: Optional[TargetRole] = None
    ) -> TurnResponse:
        """
        Processes one closed-loop turn:
        Answer -> Evaluation -> State Update -> Policy -> Target Concept -> Next Question.
        """
        candidate = candidate or CandidateProfile()
        role = role or TargetRole()

        if not getattr(role, "domain", None):
            if any(k in role.id.lower() for k in ("ece", "radar", "drdo", "scientist")):
                role.domain = "electronics_radar"
            else:
                role.domain = "cyber_computing"

        # 1. State Hydration
        state = self._hydrate_state(interview_state, current_question, candidate, role)

        # 2. Answer Evaluation (via Member 4 contract adapter)
        eval_result = self.eval_adapter.process_evaluation(
            question=current_question,
            candidate_answer=candidate_answer,
            incoming_evaluation=evaluation
        )

        # 3. State Update: Record turn, mastery, streaks, rolling trend
        state.record_turn(
            question_id=current_question.id,
            question_text=current_question.text,
            question_type=current_question.questionType or "conceptual",
            stage=current_question.stage,
            competency=current_question.competency,
            difficulty=current_question.difficulty,
            score=eval_result.score,
            covered_concepts=eval_result.coveredConcepts,
            missing_concepts=eval_result.missingConcepts
        )

        # 4. Prerequisite & Concept Status Update
        unresolved_missing = [
            m for m in state.missing_concepts
            if m not in state.demonstrated_concepts
        ]
        prereq_issues = []
        for m in unresolved_missing:
            is_met, unmet = ConceptPrerequisiteEngine.check_prerequisites_met(
                target_concept=m,
                demonstrated_concepts=state.demonstrated_concepts,
                missing_concepts=state.missing_concepts
            )
            if not is_met:
                prereq_issues.extend(unmet)
        state.prerequisite_issues = list(dict.fromkeys(prereq_issues))

        # 5. Adaptive Policy Evaluation (Policy v2)
        policy_decision: PolicyDecision = AdaptiveInterviewPolicy.evaluate_next_step(state, candidate_skills=candidate.skills)

        # 6. Target-Concept Selection
        target_concepts = TargetConceptSelector.select_targets(
            state=state,
            policy_decision=policy_decision,
            candidate_skills=candidate.skills
        )
        if target_concepts:
            policy_decision.target_concepts = target_concepts

        # 7. Synthesize Machine-Readable Decision Trace
        trace_reason = self._build_explainable_reason(
            state=state,
            eval_result=eval_result,
            policy_decision=policy_decision,
            target_concepts=target_concepts
        )

        trace = DecisionTrace(
            previousScore=eval_result.score,
            trend=state.rolling_score_trend,
            missingConcepts=list(eval_result.missingConcepts),
            persistentWeaknesses=list(state.persistent_weaknesses),
            prerequisiteIssues=list(state.prerequisite_issues),
            strategy=policy_decision.strategy,
            nextDifficulty=policy_decision.next_difficulty,
            nextCompetency=policy_decision.next_competency,
            questionType=policy_decision.recommended_question_type,
            targetConcepts=target_concepts,
            reason=trace_reason
        )

        # 8. Termination Evaluation (Authoritative decision engine)
        termination = InterviewTerminationEngine.evaluate_termination(
            state=state,
            policy_decision=policy_decision
        )

        # 9. Next Question Generation (if not terminating)
        next_question: Optional[QuestionObject] = None
        if not termination.shouldTerminate:
            # If policy suggested conclude but termination engine decided to continue, guard target stage
            target_stage = policy_decision.next_stage
            if target_stage == "closing":
                target_stage = state.current_stage if state.current_stage != "closing" else "scenario_managerial"

            try:
                next_question = self.generator.generate(
                    candidate=candidate,
                    role=role,
                    stage=target_stage,
                    competency=policy_decision.next_competency,
                    difficulty=policy_decision.next_difficulty,
                    previous_questions=state.previous_questions,
                    previous_missing_concepts=target_concepts or state.missing_concepts,
                    question_type=policy_decision.recommended_question_type,
                    adaptive_reason=trace_reason
                )
            except Exception as e:
                logger.error(f"Question generation failed: {e}; invoking safe fallback generator.")
                # Fallback to curated question bank
                next_question = self.generator._fallback_generation(
                    candidate=candidate,
                    role=role,
                    stage=target_stage,
                    competency=policy_decision.next_competency,
                    difficulty=policy_decision.next_difficulty,
                    retrieved_chunks=[],
                    previous_questions=state.previous_questions,
                    previous_missing_concepts=target_concepts or state.missing_concepts,
                    question_type=policy_decision.recommended_question_type,
                    used_fallback_ids=state.used_fallback_ids
                )
                next_question.adaptiveReason = trace_reason

            if next_question and next_question.id:
                state.used_fallback_ids.append(next_question.id)

            state.current_stage = policy_decision.next_stage
            state.current_competency = policy_decision.next_competency
            state.difficulty = policy_decision.next_difficulty
        else:
            # Authoritative termination: harmonize strategy
            policy_decision.strategy = "conclude_interview"
            trace.strategy = "conclude_interview"
            state.current_stage = "closing"

        decision_obj = DecisionObject(
            strategy=policy_decision.strategy,
            nextDifficulty=policy_decision.next_difficulty,
            nextCompetency=policy_decision.next_competency,
            targetConcepts=target_concepts,
            questionType=policy_decision.recommended_question_type,
            reason=trace_reason
        )


        return TurnResponse(
            updatedState=state.model_dump(),
            evaluation=eval_result,
            decision=decision_obj,
            nextQuestion=next_question,
            termination=termination,
            trace=trace
        )

    def _hydrate_state(
        self,
        raw_state: Optional[Any],
        current_question: QuestionObject,
        candidate: CandidateProfile,
        role: TargetRole
    ) -> InterviewState:
        """Hydrates or initializes an InterviewState instance safely."""
        if isinstance(raw_state, InterviewState):
            return raw_state
        if isinstance(raw_state, dict) and raw_state:
            try:
                return InterviewState(**raw_state)
            except Exception as e:
                logger.warning(f"Error hydrating InterviewState from dict ({e}); initializing fresh state.")

        return InterviewState(
            candidate_id=candidate.id or "cand_default",
            role_id=role.id or "backend_engineer",
            current_stage=current_question.stage,
            current_competency=current_question.competency,
            difficulty=current_question.difficulty
        )

    def _build_explainable_reason(
        self,
        state: InterviewState,
        eval_result: EvaluationResult,
        policy_decision: PolicyDecision,
        target_concepts: List[str]
    ) -> str:
        """
        Builds a human-readable and machine-readable explanation derived strictly
        from actual state values, streaks, scores, and policy strategies.
        Avoids generic filler phrases.
        """
        strategy = policy_decision.strategy
        score = eval_result.score
        trend = state.rolling_score_trend
        target_str = ", ".join(target_concepts) if target_concepts else policy_decision.next_competency
        diff = policy_decision.next_difficulty
        qtype = policy_decision.recommended_question_type

        if strategy == "remediate_persistent_weakness":
            return (
                f"Candidate repeatedly missed '{target_str}' across multiple turns (persistent weakness detected). "
                f"De-escalating difficulty to {diff}/5 using a {qtype} question to diagnose fundamental misconceptions."
            )

        if strategy == "reinforce_prerequisite":
            return (
                f"Candidate attempted advanced topic with unverified foundations. "
                f"Targeting prerequisite '{target_str}' at difficulty {diff}/5 ({qtype}) to reinforce core building blocks."
            )

        if strategy == "probe_missing_concept":
            return (
                f"Candidate scored {score}/100 and omitted '{target_str}' in previous response. "
                f"Trend is {trend}; probing missing concept directly at difficulty {diff}/5 ({qtype})."
            )

        if strategy == "progress_after_recovery":
            return (
                f"Candidate successfully demonstrated recovery of '{state.recovered_concepts[-1]}' (score: {score}/100). "
                f"Resuming stage progression to '{policy_decision.next_stage}' at difficulty {diff}/5."
            )

        if state.has_consecutive_strong(threshold=2):
            return (
                f"Candidate achieved sustained strong performance ({state.consecutive_strong_count} consecutive scores >= 80, latest: {score}/100, trend: {trend}). "
                f"Escalating difficulty to {diff}/5 ({qtype}) in {policy_decision.next_stage}."
            )

        if state.has_consecutive_weak(threshold=2) or (trend == "declining" and score < 55):
            return (
                f"Candidate exhibited consecutive weak performance ({state.consecutive_weak_count} scores < 55, trend: {trend}). "
                f"Calibrating difficulty down to {diff}/5 to re-establish baseline confidence."
            )

        if strategy == "progress_stage":
            return (
                f"Stage requirements fulfilled. Progressing from '{current_stage_or_last(state)}' to '{policy_decision.next_stage}' "
                f"at calibrated difficulty {diff}/5 ({qtype}) focusing on '{target_str}'."
            )

        if strategy == "pivot_competency":
            return (
                f"Broadening evaluation coverage: pivoting technical focus to '{policy_decision.next_competency}' "
                f"at difficulty {diff}/5 ({qtype})."
            )

        if strategy == "conclude_interview":
            return f"Interview journey concluded: {policy_decision.rationale}"

        return (
            f"Candidate scored {score}/100 (trend: {trend}); advancing {strategy} in '{policy_decision.next_stage}' "
            f"at difficulty {diff}/5 targeting '{target_str}'."
        )


def current_stage_or_last(state: InterviewState) -> str:
    """Helper returning last recorded stage or current state stage."""
    return state.current_stage if state.current_stage else "ice_breaker"
