"""
[DEPRECATED] Legacy Stateless Adaptive Interview Strategy Engine for BoardRoom AI.
Kept strictly for backwards compatibility with legacy tests.
CANONICAL STATEFUL ENGINE:
Use adaptive/policy.py (AdaptiveInterviewPolicy), adaptive/orchestrator.py (InterviewOrchestrator),
and the /api/interview/* endpoints.
"""


from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from core.schemas import AdaptiveContextRequest


class AdaptiveRecommendation(BaseModel):
    next_stage: str
    next_competency: str
    next_difficulty: int = Field(ge=1, le=5)
    strategy: str = Field(..., description="probe_missing_concept | escalate_difficulty | reinforce_fundamentals | pivot_competency | progress_stage | conclude_interview")
    missing_concepts_to_probe: List[str] = Field(default_factory=list)
    rationale: str


STAGE_PROGRESSION = [
    "ice_breaker",
    "fundamentals",
    "role_technical",
    "deep_dive",
    "scenario_managerial"
]

COMPETENCY_SEQUENCE_FOR_ROLE = [
    "ice_breaker",
    "cs_fundamentals",
    "backend",
    "database",
    "system_design",
    "scenario_managerial"
]


class AdaptiveInterviewEngine:
    """
    Decides interview flow, difficulty shifts, and next competency targets
    based on candidate performance and concept coverage.
    """

    @classmethod
    def recommend_next_step(cls, req: AdaptiveContextRequest) -> AdaptiveRecommendation:
        current_stage = req.currentStage
        current_comp = req.currentCompetency
        current_diff = req.currentDifficulty
        last_score = req.lastScore
        missing_concepts = req.missingConcepts or []
        questions_asked_count = len(req.previousQuestions)

        # Base case: Max interview length reached (e.g. 5-7 questions)
        if questions_asked_count >= 6:
            return AdaptiveRecommendation(
                next_stage="closing",
                next_competency=current_comp,
                next_difficulty=current_diff,
                strategy="conclude_interview",
                missing_concepts_to_probe=[],
                rationale="Interview has reached required depth across all stages."
            )

        # 1. Check for immediate missing concept probe
        # If candidate had a low/partial score (< 65) and specific missing concepts, probe them
        if last_score is not None and last_score < 65 and missing_concepts:
            return AdaptiveRecommendation(
                next_stage=current_stage,
                next_competency=current_comp,
                next_difficulty=max(1, current_diff - 1 if last_score < 45 else current_diff),
                strategy="probe_missing_concept",
                missing_concepts_to_probe=missing_concepts[:2],
                rationale=f"Candidate missed critical concepts ({', '.join(missing_concepts[:2])}); probing to evaluate baseline understanding."
            )

        # 2. Dynamic difficulty calibration based on score
        next_diff = current_diff
        if last_score is not None:
            if last_score >= 82 and current_diff < 5:
                next_diff = current_diff + 1
                diff_action = "escalated"
            elif last_score < 50 and current_diff > 1:
                next_diff = current_diff - 1
                diff_action = "reduced"
            else:
                diff_action = "maintained"
        else:
            diff_action = "initialized"

        # 3. Stage progression logic
        try:
            curr_stage_idx = STAGE_PROGRESSION.index(current_stage)
        except ValueError:
            curr_stage_idx = 0

        # Progress stage if questions asked match stage thresholds
        if questions_asked_count == 1:
            next_stage = "fundamentals"
            next_comp = "cs_fundamentals"
            strategy = "progress_stage"
            rationale = "Completed ice-breaker; advancing to fundamentals."
        elif questions_asked_count == 2:
            next_stage = "role_technical"
            next_comp = "backend"
            strategy = "progress_stage"
            rationale = "Fundamentals verified; progressing to role-specific technical evaluation."
        elif questions_asked_count == 3:
            # Stay in role_technical but pivot to database or stay if strong
            next_stage = "role_technical"
            next_comp = "database"
            strategy = "pivot_competency"
            rationale = f"Pivoting to database competency; difficulty {diff_action} to {next_diff}."
        elif questions_asked_count == 4:
            next_stage = "deep_dive"
            next_comp = "system_design"
            strategy = "progress_stage"
            rationale = f"Advancing to architectural deep dive; difficulty set to {next_diff}."
        elif questions_asked_count == 5:
            next_stage = "scenario_managerial"
            next_comp = "scenario_managerial"
            strategy = "progress_stage"
            rationale = "Advancing to real-world production scenario and incident triage."
        else:
            # Advance to next stage in sequence
            next_stage_idx = min(curr_stage_idx + 1, len(STAGE_PROGRESSION) - 1)
            next_stage = STAGE_PROGRESSION[next_stage_idx]
            next_comp = current_comp
            strategy = "progress_stage"
            rationale = f"Progressing to {next_stage} stage."

        return AdaptiveRecommendation(
            next_stage=next_stage,
            next_competency=next_comp,
            next_difficulty=next_diff,
            strategy=strategy,
            missing_concepts_to_probe=[],
            rationale=rationale
        )
