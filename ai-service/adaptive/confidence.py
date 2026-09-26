"""
Evidence Confidence Tracker for BoardRoom AI (Phase C).
Provides lightweight, explainable, deterministic evidence-confidence indicators
based on demonstration frequency, cross-stage validation, and multi-question-type consistency.
Explicitly avoids false statistical claims while giving evaluators grounded confidence metrics.
"""

from typing import Dict, Any, List
from adaptive.state import InterviewState


class EvidenceConfidenceTracker:
    """
    Computes interview evidence-confidence and overall coverage metrics deterministically.
    """

    @classmethod
    def calculate_concept_confidence(
        cls,
        demonstrated_count: int,
        partial_count: int,
        missed_count: int,
        qtypes_count: int = 1,
        stages_count: int = 1,
        is_recovered: bool = False
    ) -> float:
        """
        Canonical deterministic formula bounding confidence between 0.0 and 0.95.
        Rewards multi-turn and cross-stage/type consistency; penalizes contradictory evidence.
        Preserves the strongest behaviors across all subsystems.
        """
        if is_recovered:
            base = 0.80
        elif demonstrated_count >= 3:
            base = 0.85
        elif demonstrated_count >= 2:
            base = 0.75
        elif demonstrated_count == 1:
            base = 0.50
        elif partial_count > 0 and demonstrated_count == 0 and missed_count == 0:
            base = 0.35
        elif missed_count == 1:
            base = 0.20
        else:
            # Repeatedly missing or untested
            base = 0.05

        # Multi-question-type consistency bonus (+0.08)
        if qtypes_count >= 2 and demonstrated_count > 0:
            base += 0.08

        # Cross-stage consistency bonus (+0.08)
        if stages_count >= 2 and demonstrated_count > 0:
            base += 0.08

        # Contradictory evidence penalty (demonstrated in one turn, missed in another)
        if demonstrated_count > 0 and missed_count > 0 and not is_recovered:
            base = max(0.20, base - 0.20)

        # Clamp deterministically between 0.0 and 0.95 (never claim 100% certainty)
        return round(max(0.0, min(0.95, base)), 2)

    @classmethod
    def compute_concept_confidence(cls, state: InterviewState) -> Dict[str, float]:
        """
        Calculates confidence score (0.0 to 0.95) for each evaluated concept.
        Higher confidence requires multi-turn, multi-type, or multi-stage confirmation.
        """
        confidences: Dict[str, float] = {}

        # Scan turns history for stage and question type diversity per concept
        concept_stages: Dict[str, set] = {}
        concept_types: Dict[str, set] = {}

        # If state maintains turn history
        turns = getattr(state, "turns", [])
        for t in turns:
            stg = t.get("stage", "")
            qtype = t.get("question_type", "")
            for c in t.get("covered_concepts", []):
                concept_stages.setdefault(c, set()).add(stg)
                concept_types.setdefault(c, set()).add(qtype)

        for concept in state.concept_map:
            demo_count = state.concept_demonstration_counts.get(concept, 0)
            missing_count = state.concept_missing_counts.get(concept, 0)
            partial_count = state.concept_partial_counts.get(concept, 0)
            is_recovered = concept in state.recovered_concepts
            qtypes_cnt = len(concept_types.get(concept, set()))
            stages_cnt = len(concept_stages.get(concept, set()))

            confidences[concept] = cls.calculate_concept_confidence(
                demonstrated_count=demo_count,
                partial_count=partial_count,
                missed_count=missing_count,
                qtypes_count=qtypes_cnt,
                stages_count=stages_cnt,
                is_recovered=is_recovered
            )

        return confidences


    @classmethod
    def compute_evidence_coverage(cls, state: InterviewState) -> float:
        """
        Calculates overall evidence coverage (0.0 to 1.0) based on stage progress,
        question count, and breadth of demonstrated concepts.
        """
        total_questions = len(state.previous_questions)
        if total_questions == 0:
            return 0.0

        # Stages covered (up to 5 stages)
        stages_visited = sum(1 for cnt in state.stage_question_counts.values() if cnt > 0)
        stage_factor = min(1.0, stages_visited / 4.0)

        # Demonstration breadth
        total_concepts_tracked = len(state.concept_map)
        demonstrated_count = len(state.demonstrated_concepts)
        breadth_factor = min(1.0, demonstrated_count / 5.0) if total_concepts_tracked > 0 else 0.0

        # Turn depth factor (4-6 questions is standard depth)
        depth_factor = min(1.0, total_questions / 5.0)

        # Weighted coverage score
        coverage = (stage_factor * 0.40) + (breadth_factor * 0.35) + (depth_factor * 0.25)
        return round(max(0.0, min(1.0, coverage)), 2)

    @classmethod
    def get_summary(cls, state: InterviewState) -> Dict[str, Any]:
        """Provides human-readable and structured evidence diagnostics."""
        confidences = cls.compute_concept_confidence(state)
        coverage = cls.compute_evidence_coverage(state)

        high_conf = [c for c, conf in confidences.items() if conf >= 0.70]
        medium_conf = [c for c, conf in confidences.items() if 0.40 <= conf < 0.70]
        low_conf = [c for c, conf in confidences.items() if conf < 0.40]

        return {
            "evidenceCoverage": coverage,
            "conceptConfidences": confidences,
            "highConfidenceConcepts": high_conf,
            "mediumConfidenceConcepts": medium_conf,
            "lowConfidenceConcepts": low_conf,
            "stagesVisitedCount": sum(1 for cnt in state.stage_question_counts.values() if cnt > 0),
            "totalConceptsTracked": len(state.concept_map),
            "rationale": f"Candidate demonstrated {len(high_conf)} high-confidence concepts across {len(state.previous_questions)} turns; overall evidence coverage is {coverage:.0%}."
        }
