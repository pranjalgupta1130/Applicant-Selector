"""
Deterministic Adaptive Interview Policy for BoardRoom AI (Phase B v2).
Decides stage progression, competency pivots, difficulty escalation/de-escalation,
concept gap probing, prerequisite reinforcement, and persistent weakness remediation
based on deterministic evaluation signals and historical performance state.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from adaptive.state import InterviewState
from adaptive.prerequisites import ConceptPrerequisiteEngine


class PolicyDecision(BaseModel):
    next_stage: str
    next_competency: str
    next_difficulty: int = Field(ge=1, le=5)
    strategy: str = Field(
        ...,
        description="probe_missing_concept | reinforce_prerequisite | remediate_persistent_weakness | progress_after_recovery | escalate_difficulty | reinforce_fundamentals | pivot_competency | progress_stage | conclude_interview"
    )
    recommended_question_type: str = Field(..., description="conceptual | implementation | debugging | trade_off | scenario | design | follow_up")
    target_concepts: List[str] = Field(default_factory=list)
    rationale: str
    adaptive_reason: str


STAGE_LADDER = [
    "ice_breaker",
    "fundamentals",
    "role_technical",
    "deep_dive",
    "scenario_managerial"
]

COMPETENCY_LADDER = [
    "ice_breaker",
    "cs_fundamentals",
    "backend",
    "database",
    "system_design",
    "scenario_managerial"
]

STAGE_QUESTION_QUOTAS = {
    "ice_breaker": 1,
    "fundamentals": 1,
    "role_technical": 1,
    "deep_dive": 1,
    "scenario_managerial": 1
}


class AdaptiveInterviewPolicy:
    """
    Deterministic rule engine that drives the adaptive interview journey.
    Guarantees logical progression while dynamically probing gaps, respecting
    concept prerequisites, tracking mastery, and adapting difficulty based on historical performance trends.
    """

    @classmethod
    def evaluate_next_step(cls, state: InterviewState) -> PolicyDecision:
        total_questions = len(state.previous_questions)
        last_score = state.score_history[-1] if state.score_history else None
        current_diff = state.difficulty
        current_stage = state.current_stage
        current_comp = state.current_competency

        # Rule 1: Termination Guard
        if total_questions >= 6:
            return PolicyDecision(
                next_stage="closing",
                next_competency=current_comp,
                next_difficulty=current_diff,
                strategy="conclude_interview",
                recommended_question_type="scenario",
                target_concepts=[],
                rationale="Interview journey reached required depth (6 questions across all stages).",
                adaptive_reason="Conclude interview after comprehensive staged evaluation."
            )

        # Rule 2: Persistent Weakness Remediation
        # If candidate has persistent weaknesses that remain unresolved
        unresolved_pw = [w for w in state.persistent_weaknesses if w not in state.demonstrated_concepts]
        if unresolved_pw:
            target_pw = unresolved_pw[0]
            next_diff = max(1, current_diff - 1)
            return PolicyDecision(
                next_stage=current_stage,
                next_competency=current_comp,
                next_difficulty=next_diff,
                strategy="remediate_persistent_weakness",
                recommended_question_type="debugging",
                target_concepts=[target_pw],
                rationale=f"Candidate exhibited persistent weakness on '{target_pw}' across multiple turns. De-escalating difficulty to {next_diff}/5 to diagnose and remediate core misunderstanding.",
                adaptive_reason=f"Remediating persistent weakness on '{target_pw}'."
            )

        # Rule 3: Prerequisite Dependency Guard
        # If candidate exhibits gaps on an advanced concept whose prerequisites are unmet
        unresolved_missing = [m for m in state.missing_concepts if m not in state.demonstrated_concepts]
        if unresolved_missing:
            target_gap = unresolved_missing[0]
            prereqs_met, unmet_prereqs = ConceptPrerequisiteEngine.check_prerequisites_met(
                target_gap,
                state.demonstrated_concepts,
                state.missing_concepts
            )
            if not prereqs_met and unmet_prereqs:
                target_prereq = unmet_prereqs[0]
                next_diff = max(1, current_diff - 1)
                return PolicyDecision(
                    next_stage=current_stage,
                    next_competency=current_comp,
                    next_difficulty=next_diff,
                    strategy="reinforce_prerequisite",
                    recommended_question_type="conceptual",
                    target_concepts=[target_prereq],
                    rationale=f"Advanced concept '{target_gap}' requires prerequisite '{target_prereq}', which is unverified or missing. Probing foundational prerequisite first before advancing.",
                    adaptive_reason=f"Reinforcing prerequisite '{target_prereq}' prior to advanced concept '{target_gap}'."
                )

        # Rule 4: Immediate Concept Gap Probing
        # If candidate had a low/partial score (< 68) and has unresolved missing concepts (with prerequisites satisfied)
        if last_score is not None and last_score < 68 and unresolved_missing:
            target_gap = unresolved_missing[0]
            # De-escalate difficulty if candidate struggled (< 50), performance is declining, or exhibits repeated weakness
            if last_score < 50 or state.rolling_score_trend == "declining" or state.has_consecutive_weak():
                next_diff = max(1, current_diff - 1)
                diff_note = f"reducing difficulty to {next_diff}/5 due to repeated weak performance"
            else:
                next_diff = current_diff
                diff_note = f"maintaining difficulty at {next_diff}/5"

            return PolicyDecision(
                next_stage=current_stage,
                next_competency=current_comp,
                next_difficulty=next_diff,
                strategy="probe_missing_concept",
                recommended_question_type="follow_up",
                target_concepts=[target_gap],
                rationale=f"Candidate answer exhibited gap on '{target_gap}' (score {last_score}/100); probing gap directly, {diff_note}.",
                adaptive_reason=f"Adaptive probe targeting missing concept: '{target_gap}'"
            )

        # Rule 5: Historical Performance Trend & Difficulty Calibration
        next_diff = current_diff
        recovery_prefix = ""
        if state.recovered_concepts and last_score is not None and last_score >= 75:
            recovery_prefix = f"Candidate successfully recovered previously missed concept '{state.recovered_concepts[-1]}'. "

        # 5a. Repeated Strong Performance / Improving Trend
        if state.has_consecutive_strong(threshold=2) or (state.rolling_score_trend == "improving" and last_score is not None and last_score >= 82):
            if current_diff < 5:
                next_diff = current_diff + 1
            else:
                next_diff = 5
            diff_reason = f"{recovery_prefix}Candidate demonstrated sustained strong performance ({state.consecutive_strong_count} consecutive strong answers, trend: {state.rolling_score_trend}); escalating difficulty to {next_diff}/5."

        # 5b. Repeated Weak Performance / Declining Trend
        elif state.has_consecutive_weak(threshold=2) or (state.rolling_score_trend == "declining" and last_score is not None and last_score < 55):
            if current_diff > 1:
                next_diff = current_diff - 1
            else:
                next_diff = 1
            diff_reason = f"Candidate exhibited declining/repeated weak performance ({state.consecutive_weak_count} consecutive weak answers, trend: {state.rolling_score_trend}); reducing difficulty to {next_diff}/5 to reinforce fundamentals."

        # 5c. Standard Single-Turn Calibration
        elif last_score is not None:
            if last_score >= 82 and current_diff < 5:
                next_diff = current_diff + 1
                diff_reason = f"{recovery_prefix}Candidate demonstrated mastery (score {last_score}/100); escalating difficulty to {next_diff}/5."
            elif last_score < 50 and current_diff > 1:
                next_diff = current_diff - 1
                diff_reason = f"Candidate struggled (score {last_score}/100); reducing difficulty to {next_diff}/5 to re-establish baseline."
            else:
                diff_reason = f"{recovery_prefix}Candidate performed adequately (score {last_score}/100); maintaining difficulty at {next_diff}/5."
        else:
            diff_reason = "Initial difficulty set for interview opening."

        # Rule 6: Stage & Competency Progression
        stage_count = state.stage_question_counts.get(current_stage, 0)
        stage_quota = STAGE_QUESTION_QUOTAS.get(current_stage, 1)

        try:
            curr_stage_idx = STAGE_LADDER.index(current_stage)
        except ValueError:
            curr_stage_idx = 0

        # Check if stage quota is fulfilled
        if stage_count >= stage_quota and curr_stage_idx < len(STAGE_LADDER) - 1:
            next_stage_idx = curr_stage_idx + 1
            next_stage = STAGE_LADDER[next_stage_idx]
            strategy = "progress_stage"

            # Transition competency naturally to match stage
            if next_stage == "fundamentals":
                next_comp = "cs_fundamentals"
            elif next_stage == "role_technical":
                next_comp = "backend"
            elif next_stage == "deep_dive":
                next_comp = "database" if "database" not in state.competency_scores else "system_design"
            elif next_stage == "scenario_managerial":
                next_comp = "scenario_managerial"
            else:
                next_comp = current_comp

            rationale = f"Stage '{current_stage}' quota met ({stage_count} questions). Progressing to stage '{next_stage}'. {diff_reason}"
            adaptive_reason = f"Advancing interview progression to {next_stage}."
        else:
            # Stay in stage, but optionally pivot competency within role_technical or deep_dive
            next_stage = current_stage
            strategy = "pivot_competency" if stage_count > 0 else "progress_stage"

            if current_stage == "role_technical" and stage_count == 1:
                next_comp = "database" if current_comp != "database" else "backend"
                rationale = f"Broadening technical coverage: pivoting from '{current_comp}' to '{next_comp}'. {diff_reason}"
                adaptive_reason = f"Pivoting technical competency to {next_comp}."
            elif current_stage == "deep_dive" and stage_count == 1:
                next_comp = "system_design" if current_comp != "system_design" else "backend"
                rationale = f"Deepening architectural evaluation: pivoting from '{current_comp}' to '{next_comp}'. {diff_reason}"
                adaptive_reason = f"Pivoting deep dive competency to {next_comp}."
            else:
                next_comp = current_comp
                rationale = f"Continuing {current_stage} evaluation. {diff_reason}"
                adaptive_reason = f"Continuing {current_stage} at difficulty {next_diff}."

        # Rule 7: Question Type Diversity Mapping (Avoid repeating same type)
        last_type = state.question_types[-1] if state.question_types else None
        recommended_type = cls._select_diverse_question_type(next_stage, last_type)

        return PolicyDecision(
            next_stage=next_stage,
            next_competency=next_comp,
            next_difficulty=next_diff,
            strategy=strategy,
            recommended_question_type=recommended_type,
            target_concepts=[],
            rationale=rationale,
            adaptive_reason=adaptive_reason
        )

    @classmethod
    def _select_diverse_question_type(cls, stage: str, last_type: Optional[str]) -> str:
        """Selects a question type appropriate to the stage while rotating away from last type."""
        stage_preferred_types = {
            "ice_breaker": ["conceptual"],
            "fundamentals": ["conceptual", "trade_off"],
            "role_technical": ["implementation", "design", "debugging", "trade_off"],
            "deep_dive": ["trade_off", "design", "debugging", "follow_up"],
            "scenario_managerial": ["scenario", "debugging"]
        }

        candidates = stage_preferred_types.get(stage, ["conceptual", "implementation", "scenario"])
        filtered = [t for t in candidates if t != last_type]
        return filtered[0] if filtered else candidates[0]
