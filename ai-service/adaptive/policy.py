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
    "applicant_validation",
    "core_technical",
    "deep_dive",
    "application_scenario",
    "system_engineering",
    "techno_managerial"
]

COMPETENCY_LADDER = [
    "ice_breaker",
    "applicant_validation",
    "core_technical",
    "deep_dive",
    "application_scenario",
    "system_engineering",
    "techno_managerial"
]

STAGE_QUESTION_QUOTAS = {
    "ice_breaker": 1,
    "applicant_validation": 1,
    "core_technical": 1,
    "deep_dive": 1,
    "application_scenario": 1,
    "system_engineering": 1,
    "techno_managerial": 1
}


class AdaptiveInterviewPolicy:
    """
    Deterministic rule engine that drives the adaptive interview journey.
    Guarantees logical progression while dynamically probing gaps, respecting
    concept prerequisites, tracking mastery, and adapting difficulty based on historical performance trends.
    """

    @classmethod
    def evaluate_next_step(cls, state: InterviewState, candidate_skills: Optional[List[str]] = None) -> PolicyDecision:
        total_questions = len(state.previous_questions)
        last_score = state.score_history[-1] if state.score_history else None
        current_diff = state.difficulty
        current_stage = state.current_stage
        current_comp = state.current_competency

        # Rule 1: Termination / Safety Cap Guard (Termination Engine holds authoritative decision)
        if total_questions >= 8 or state.current_stage == "closing":
            return PolicyDecision(
                next_stage="closing",
                next_competency=current_comp,
                next_difficulty=current_diff,
                strategy="conclude_interview",
                recommended_question_type="scenario",
                target_concepts=[],
                rationale=f"Interview reached maximum safety cap ({total_questions} questions completed).",
                adaptive_reason="Conclude interview session at maximum safety cap."
            )

        active_ladder = STAGE_LADDER
        active_quotas = STAGE_QUESTION_QUOTAS

        stage_aliases = {
            "fundamentals": "applicant_validation",
            "expertise_validation": "applicant_validation",
            "role_technical": "core_technical",
            "scenario_managerial": "application_scenario",
            "system_engineering_design": "system_engineering"
        }
        norm_stage = stage_aliases.get(current_stage, current_stage)

        stage_count = state.stage_question_counts.get(norm_stage, 0) + (state.stage_question_counts.get(current_stage, 0) if norm_stage != current_stage else 0)
        stage_quota = active_quotas.get(norm_stage, 1)

        try:
            curr_stage_idx = active_ladder.index(norm_stage)
        except ValueError:
            curr_stage_idx = 0

        # Determine if stage quota is fulfilled and resolve next stage
        quota_fulfilled = (stage_count >= stage_quota) or (norm_stage == "ice_breaker" and total_questions >= 1)
        if quota_fulfilled and curr_stage_idx < len(active_ladder) - 1:
            effective_next_stage = active_ladder[curr_stage_idx + 1]
        elif curr_stage_idx >= len(active_ladder) - 1 and quota_fulfilled:
            effective_next_stage = "closing"
        else:
            effective_next_stage = norm_stage

        # Helper to resolve domain-specific competency for any target stage
        role_key = state.role_id.lower()
        role_domain = "aerospace" if any(k in role_key for k in ("aerospace", "aerodynamics", "materials")) else "cyber" if any(k in role_key for k in ("cyber", "security")) else "radar"
        skill_text = " ".join(candidate_skills or []).lower()
        radar_expertise = "embedded_realtime_systems" if any(k in skill_text for k in ("embedded", "firmware", "c++", "microcontroller")) else "digital_signal_processing" if any(k in skill_text for k in ("dsp", "signal", "radar", "detection")) else "radar_rf_systems"

        def get_stage_competency(tgt_stage: str) -> str:
            if tgt_stage == "ice_breaker":
                return "ice_breaker"
            if role_domain == "aerospace":
                mapping = {
                    "applicant_validation": "aerodynamics_fundamentals",
                    "core_technical": "aerospace_aerodynamics",
                    "deep_dive": "fluid_mechanics_cfd",
                    "application_scenario": "aerodynamic_analysis",
                    "system_engineering": "system_engineering",
                    "techno_managerial": "techno_managerial"
                }
            elif role_domain == "cyber":
                mapping = {
                    "applicant_validation": "cybersecurity_fundamentals",
                    "core_technical": "network_security",
                    "deep_dive": "incident_response",
                    "application_scenario": "system_resilience",
                    "system_engineering": "system_engineering",
                    "techno_managerial": "techno_managerial"
                }
            else:
                mapping = {
                    "applicant_validation": radar_expertise,
                    "core_technical": "radar_rf_systems",
                    "deep_dive": "digital_signal_processing",
                    "application_scenario": "avionics_communication",
                    "system_engineering": "system_engineering",
                    "techno_managerial": "techno_managerial"
                }
            return mapping.get(tgt_stage, "system_engineering" if tgt_stage == "system_engineering" else "techno_managerial" if tgt_stage == "techno_managerial" else current_comp)

        resolved_next_comp = get_stage_competency(effective_next_stage) if current_comp == "ice_breaker" else current_comp

        # Rule 2: Persistent Weakness Remediation (Respect stage progression)
        unresolved_pw = [w for w in state.persistent_weaknesses if w not in state.demonstrated_concepts]
        if unresolved_pw and norm_stage != "ice_breaker":
            target_pw = unresolved_pw[0]
            next_diff = max(1, current_diff - 1)
            return PolicyDecision(
                next_stage=effective_next_stage,
                next_competency=get_stage_competency(effective_next_stage),
                next_difficulty=next_diff,
                strategy="remediate_persistent_weakness",
                recommended_question_type="debugging",
                target_concepts=[target_pw],
                rationale=f"Candidate exhibited persistent weakness on '{target_pw}' across multiple turns. Adjusting difficulty to {next_diff}/5 in stage '{effective_next_stage}'.",
                adaptive_reason=f"Remediating persistent weakness on '{target_pw}'."
            )

        # Rule 3: Prerequisite Dependency Guard
        unresolved_missing = [m for m in state.missing_concepts if m not in state.demonstrated_concepts]
        if unresolved_missing and norm_stage != "ice_breaker":
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
                    next_stage=effective_next_stage,
                    next_competency=get_stage_competency(effective_next_stage),
                    next_difficulty=next_diff,
                    strategy="reinforce_prerequisite",
                    recommended_question_type="conceptual",
                    target_concepts=[target_prereq],
                    rationale=f"Advanced concept '{target_gap}' requires prerequisite '{target_prereq}'. Probing foundational prerequisite in stage '{effective_next_stage}'.",
                    adaptive_reason=f"Reinforcing prerequisite '{target_prereq}' prior to advanced concept '{target_gap}'."
                )

        # Rule 4: Immediate Concept Gap Probing (Never trap in ice_breaker)
        if last_score is not None and last_score < 68 and unresolved_missing and norm_stage != "ice_breaker":
            target_gap = unresolved_missing[0]
            if last_score < 50 or state.rolling_score_trend == "declining" or state.has_consecutive_weak():
                next_diff = max(1, current_diff - 1)
                diff_note = f"reducing difficulty to {next_diff}/5 due to weak performance"
            else:
                next_diff = current_diff
                diff_note = f"maintaining difficulty at {next_diff}/5"

            return PolicyDecision(
                next_stage=effective_next_stage,
                next_competency=get_stage_competency(effective_next_stage),
                next_difficulty=next_diff,
                strategy="probe_missing_concept",
                recommended_question_type="follow_up",
                target_concepts=[target_gap],
                rationale=f"Candidate answer exhibited gap on '{target_gap}' (score {last_score}/100); probing gap directly in stage '{effective_next_stage}', {diff_note}.",
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

        # Rule 6: Stage & Competency Progression (Domain-Aware Ladder)
        # Check if all stages in ladder have completed their quota
        if curr_stage_idx >= len(active_ladder) - 1 and stage_count >= stage_quota:
            return PolicyDecision(
                next_stage="closing",
                next_competency=get_stage_competency("techno_managerial"),
                next_difficulty=next_diff,
                strategy="conclude_interview",
                recommended_question_type="scenario",
                target_concepts=[],
                rationale=f"All interview stages completed through final stage '{norm_stage}'. {diff_reason}",
                adaptive_reason="Conclude interview after comprehensive staged ladder progression."
            )

        # Check if stage quota is fulfilled or forcing out of ice_breaker
        if (stage_count >= stage_quota or norm_stage == "ice_breaker") and curr_stage_idx < len(active_ladder) - 1:
            next_stage_idx = curr_stage_idx + 1
            next_stage = active_ladder[next_stage_idx]
            strategy = "progress_stage"
            next_comp = get_stage_competency(next_stage)

            rationale = f"Stage '{norm_stage}' completed ({stage_count} question(s)). Progressing to stage '{next_stage}'. {diff_reason}"
            adaptive_reason = f"Advancing interview progression to {next_stage}."
        else:
            next_stage = norm_stage
            strategy = "pivot_competency" if stage_count > 0 else "progress_stage"
            next_comp = get_stage_competency(next_stage)
            rationale = f"Continuing {norm_stage} evaluation. {diff_reason}"
            adaptive_reason = f"Continuing {norm_stage} at difficulty {next_diff}."

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
            "expertise_validation": ["conceptual", "debugging"],
            "fundamentals": ["conceptual", "trade_off"],
            "role_technical": ["implementation", "design", "debugging", "trade_off"],
            "deep_dive": ["trade_off", "design", "debugging", "follow_up"],
            "application_scenario": ["scenario", "design"],
            "system_engineering_design": ["design", "trade_off"],
            "scenario_managerial": ["scenario", "debugging"],
            "techno_managerial": ["scenario", "trade_off"]
        }

        candidates = stage_preferred_types.get(stage, ["conceptual", "implementation", "scenario"])
        filtered = [t for t in candidates if t != last_type]
        return filtered[0] if filtered else candidates[0]
