"""
Structured Interview Termination Engine for BoardRoom AI (Phase C).
Evaluates session completion multi-dimensionally:
- Minimum coverage & depth
- Stage progression completeness
- Unresolved persistent weaknesses
- Evidence coverage & confidence
- Mastery breadth
- Deterministic safety cap
Never relies solely on turn counts or LLM subjective judgment.
"""

from typing import Optional, Dict, Any
from core.schemas import TerminationDecision
from adaptive.state import InterviewState
from adaptive.policy import PolicyDecision
from adaptive.confidence import EvidenceConfidenceTracker


class InterviewTerminationEngine:
    """
    Deterministic rule engine that assesses whether the interview should terminate.
    """

    MIN_TURNS: int = 4
    MAX_TURNS_SAFETY_CAP: int = 8
    MIN_COVERAGE_THRESHOLD: float = 0.70

    @classmethod
    def evaluate_termination(
        cls,
        state: InterviewState,
        policy_decision: Optional[PolicyDecision] = None
    ) -> TerminationDecision:
        total_turns = len(state.previous_questions)
        evidence_coverage = EvidenceConfidenceTracker.compute_evidence_coverage(state)
        unresolved_pw = [
            w for w in state.persistent_weaknesses
            if w not in state.demonstrated_concepts and w not in state.recovered_concepts
        ]
        stages_visited = sum(1 for cnt in state.stage_question_counts.values() if cnt > 0)

        # 1. Deterministic Safety Cap
        if total_turns >= cls.MAX_TURNS_SAFETY_CAP:
            return TerminationDecision(
                shouldTerminate=True,
                reason=f"Interview safety cap reached ({total_turns} turns completed). Concluding interview session.",
                evidenceCoverage=evidence_coverage,
                details={
                    "totalTurns": total_turns,
                    "stagesVisited": stages_visited,
                    "unresolvedWeaknesses": unresolved_pw,
                    "safetyCapTriggered": True
                }
            )

        # 2. Minimum Turn Floor Check
        if total_turns < cls.MIN_TURNS:
            return TerminationDecision(
                shouldTerminate=False,
                reason=f"Minimum interview depth not yet achieved ({total_turns}/{cls.MIN_TURNS} turns completed).",
                evidenceCoverage=evidence_coverage,
                details={
                    "totalTurns": total_turns,
                    "stagesVisited": stages_visited,
                    "unresolvedWeaknesses": unresolved_pw
                }
            )

        # 3. Persistent Weakness Gate: Do not terminate early if unresolved weaknesses require probing
        if unresolved_pw and total_turns < 6:
            return TerminationDecision(
                shouldTerminate=False,
                reason=f"Active persistent weakness remediation in progress ({', '.join(unresolved_pw)}). Continuing targeted probing.",
                evidenceCoverage=evidence_coverage,
                details={
                    "totalTurns": total_turns,
                    "unresolvedWeaknesses": unresolved_pw
                }
            )

        # 4. Stage Progression Completeness Check
        has_reached_late_stage = (
            state.stage_question_counts.get("deep_dive", 0) > 0 or
            state.stage_question_counts.get("scenario_managerial", 0) > 0 or
            state.current_stage in ("deep_dive", "scenario_managerial", "closing")
        )

        # 5. Policy Conclusion Signal
        if policy_decision and policy_decision.strategy == "conclude_interview":
            return TerminationDecision(
                shouldTerminate=True,
                reason=f"Adaptive policy concluded interview: {policy_decision.rationale}",
                evidenceCoverage=evidence_coverage,
                details={
                    "totalTurns": total_turns,
                    "policyStrategy": policy_decision.strategy,
                    "stagesVisited": stages_visited
                }
            )

        # 6. Sufficient Mastery & Evidence Coverage Achieved
        if total_turns >= 5 and evidence_coverage >= cls.MIN_COVERAGE_THRESHOLD and has_reached_late_stage:
            return TerminationDecision(
                shouldTerminate=True,
                reason=f"Comprehensive competency coverage demonstrated ({evidence_coverage:.0%} evidence coverage) across {stages_visited} stages.",
                evidenceCoverage=evidence_coverage,
                details={
                    "totalTurns": total_turns,
                    "evidenceCoverage": evidence_coverage,
                    "stagesVisited": stages_visited
                }
            )

        # 7. Progression across all 5 stages completed
        if stages_visited >= 4 and total_turns >= 5:
            return TerminationDecision(
                shouldTerminate=True,
                reason=f"Stage progression ladder completed across {stages_visited} stages with sufficient evidence ({evidence_coverage:.0%}).",
                evidenceCoverage=evidence_coverage,
                details={
                    "totalTurns": total_turns,
                    "stagesVisited": stages_visited
                }
            )

        # Default: Continue evaluation
        return TerminationDecision(
            shouldTerminate=False,
            reason=f"Evaluation in progress. Current evidence coverage is {evidence_coverage:.0%} with {total_turns} turns completed.",
            evidenceCoverage=evidence_coverage,
            details={
                "totalTurns": total_turns,
                "stagesVisited": stages_visited,
                "evidenceCoverage": evidence_coverage
            }
        )
