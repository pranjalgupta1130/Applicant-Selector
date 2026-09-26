"""
Concept-Level Evidence Aggregator for BoardRoom AI (Phase D).
Aggregates concept demonstrations across the entire interview trajectory,
preserving turn-by-turn provenance, demonstration frequency, score bounds,
question type diversity, and multi-tier mastery confidence.
"""

from typing import Dict, List, Any
from core.schemas import ConceptEvidence, ConceptEvidenceProvenance
from adaptive.state import InterviewState, ConceptMasteryLevel


class ConceptEvidenceAggregator:
    """
    Aggregates interview trajectory turns into structured, explainable concept evidence with provenance.
    """

    @classmethod
    def aggregate_from_state(cls, state: InterviewState) -> Dict[str, ConceptEvidence]:
        """
        Processes turns stored in InterviewState to produce a dictionary of concept -> ConceptEvidence.
        """
        aggregated: Dict[str, Dict[str, Any]] = {}

        turns = getattr(state, "turns", [])
        for t in turns:
            turn_idx = t.get("turn", 1)
            q_id = t.get("question_id", "q_unknown")
            q_type = t.get("question_type", "conceptual")
            stage = t.get("stage", "role_technical")
            comp = t.get("competency", "backend")
            score = t.get("score", 70)
            covered = t.get("covered_concepts", [])
            missing = t.get("missing_concepts", [])

            # 1. Process covered concepts
            for c in covered:
                entry = cls._get_or_create_entry(aggregated, c, comp)
                entry["testedCount"] += 1
                entry["scores"].append(score)
                entry["highestScore"] = max(entry["highestScore"], score)
                entry["latestScore"] = score
                entry["questionTypes"].add(q_type)
                entry["stages"].add(stage)

                if score >= 70:
                    entry["demonstratedCount"] += 1
                    is_demo = True
                elif score >= 50:
                    entry["partialCount"] += 1
                    is_demo = False
                else:
                    entry["missedCount"] += 1
                    is_demo = False

                entry["provenance"].append(
                    ConceptEvidenceProvenance(
                        turnId=turn_idx,
                        questionId=q_id,
                        questionType=q_type,
                        stage=stage,
                        score=score,
                        isDemonstrated=is_demo
                    )
                )

            # 2. Process missing concepts
            for m in missing:
                entry = cls._get_or_create_entry(aggregated, m, comp)
                entry["testedCount"] += 1
                entry["missedCount"] += 1
                entry["scores"].append(score)
                entry["highestScore"] = max(entry["highestScore"], score)
                entry["latestScore"] = score
                entry["questionTypes"].add(q_type)
                entry["stages"].add(stage)

                entry["provenance"].append(
                    ConceptEvidenceProvenance(
                        turnId=turn_idx,
                        questionId=q_id,
                        questionType=q_type,
                        stage=stage,
                        score=score,
                        isDemonstrated=False
                    )
                )

        # 3. Finalize models
        final_evidence: Dict[str, ConceptEvidence] = {}
        for c, data in aggregated.items():
            scores = data["scores"]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

            # Determine mastery
            if c in state.recovered_concepts:
                mastery = ConceptMasteryLevel.RECOVERED.value
            elif data["demonstratedCount"] >= 2:
                mastery = ConceptMasteryLevel.CONSISTENTLY_DEMONSTRATED.value
            elif data["demonstratedCount"] == 1 and data["missedCount"] == 0:
                mastery = ConceptMasteryLevel.DEMONSTRATED_ONCE.value
            elif data["partialCount"] > 0 and data["demonstratedCount"] == 0 and data["missedCount"] == 0:
                mastery = ConceptMasteryLevel.PARTIALLY_DEMONSTRATED.value
            elif data["missedCount"] >= 2:
                mastery = ConceptMasteryLevel.REPEATEDLY_MISSING.value
            else:
                mastery = ConceptMasteryLevel.PARTIALLY_DEMONSTRATED.value

            # Calculate confidence
            confidence = cls._calculate_concept_confidence(
                demonstrated_count=data["demonstratedCount"],
                partial_count=data["partialCount"],
                missed_count=data["missedCount"],
                qtypes_count=len(data["questionTypes"]),
                stages_count=len(data["stages"]),
                is_recovered=(c in state.recovered_concepts)
            )

            final_evidence[c] = ConceptEvidence(
                concept=c,
                competency=data["competency"],
                testedCount=data["testedCount"],
                demonstratedCount=data["demonstratedCount"],
                partialCount=data["partialCount"],
                missedCount=data["missedCount"],
                highestScore=data["highestScore"],
                latestScore=data["latestScore"],
                averageScore=avg_score,
                questionTypes=sorted(list(data["questionTypes"])),
                stages=sorted(list(data["stages"])),
                masteryLevel=mastery,
                confidence=confidence,
                provenance=data["provenance"]
            )

        return final_evidence

    @classmethod
    def _get_or_create_entry(cls, aggregated: Dict[str, Dict[str, Any]], concept: str, competency: str) -> Dict[str, Any]:
        if concept not in aggregated:
            aggregated[concept] = {
                "competency": competency,
                "testedCount": 0,
                "demonstratedCount": 0,
                "partialCount": 0,
                "missedCount": 0,
                "highestScore": 0,
                "latestScore": 0,
                "scores": [],
                "questionTypes": set(),
                "stages": set(),
                "provenance": []
            }
        return aggregated[concept]

    @classmethod
    def _calculate_concept_confidence(
        cls,
        demonstrated_count: int,
        partial_count: int,
        missed_count: int,
        qtypes_count: int,
        stages_count: int,
        is_recovered: bool = False
    ) -> float:
        """
        Lightweight deterministic formula bounding confidence between 0.0 and 0.95.
        Rewards multi-turn and cross-stage/type consistency; penalizes contradictory evidence.
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
            base = 0.05

        # Multi-question-type consistency bonus
        if qtypes_count >= 2 and demonstrated_count > 0:
            base += 0.08

        # Cross-stage consistency bonus
        if stages_count >= 2 and demonstrated_count > 0:
            base += 0.08

        # Contradictory evidence penalty (demonstrated in one turn, missed in another)
        if demonstrated_count > 0 and missed_count > 0 and not is_recovered:
            base = max(0.20, base - 0.20)

        return round(max(0.0, min(0.95, base)), 2)
