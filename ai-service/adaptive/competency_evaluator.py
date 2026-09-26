"""
Competency Evidence Evaluator for BoardRoom AI (Phase D).
Aggregates concept-level and turn-level performance into explainable competency assessments.
Maintains clear, non-negotiable architectural distinctions between:
- Competency Score (candidate technical proficiency where observed)
- Evidence Coverage (breadth of tested concepts vs benchmark expected concepts)
- Evidence Confidence (depth, multi-turn consistency, and repeatability of evidence)
- Uncertainty Detection (identifying unverified, contradictory, or thin competencies)
"""

from typing import Dict, List, Optional
from core.schemas import CompetencyEvidence, ConceptEvidence
from adaptive.state import InterviewState
from adaptive.competency_matrix import RoleCompetencyMatrix
from adaptive.concept_evidence import ConceptEvidenceAggregator


class CompetencyEvaluator:
    """
    Evaluates individual competencies strictly from accumulated interview evidence.
    """

    @classmethod
    def evaluate_all_competencies(
        cls,
        state: InterviewState,
        role_id: Optional[str] = "backend_engineer",
        concept_evidence_map: Optional[Dict[str, ConceptEvidence]] = None
    ) -> List[CompetencyEvidence]:
        """
        Evaluates each role competency defined in the RoleCompetencyMatrix.
        """
        if concept_evidence_map is None:
            concept_evidence_map = ConceptEvidenceAggregator.aggregate_from_state(state)

        role_competencies = RoleCompetencyMatrix.get_role_competencies(role_id)
        results: List[CompetencyEvidence] = []

        for comp in role_competencies:
            comp_eval = cls.evaluate_competency(
                competency=comp,
                state=state,
                role_id=role_id,
                concept_evidence_map=concept_evidence_map
            )
            results.append(comp_eval)

        return results

    @classmethod
    def evaluate_competency(
        cls,
        competency: str,
        state: InterviewState,
        role_id: Optional[str] = "backend_engineer",
        concept_evidence_map: Optional[Dict[str, ConceptEvidence]] = None
    ) -> CompetencyEvidence:
        """
        Calculates score, confidence, coverage, status, and explainable reasoning for one competency.
        """
        if concept_evidence_map is None:
            concept_evidence_map = ConceptEvidenceAggregator.aggregate_from_state(state)

        expected_pool = RoleCompetencyMatrix.get_expected_concepts(competency)

        # 1. Filter turns relevant to this competency (either explicit competency match or concept match)
        turns = getattr(state, "turns", [])
        relevant_turns = [
            t for t in turns
            if t.get("competency") == competency or
            any(
                any(exp.lower() in c.lower() or c.lower() in exp.lower() for exp in expected_pool)
                for c in (t.get("covered_concepts", []) + t.get("missing_concepts", []))
            )
        ]
        turn_scores = [t.get("score", 70) for t in relevant_turns if t.get("score") is not None]


        # 2. Collect tested, demonstrated, partial, and missing concepts
        demonstrated: List[str] = []
        partial: List[str] = []
        missing: List[str] = []
        contradictory: List[str] = []
        question_types: set = set()
        stages: set = set()

        for c, ev in concept_evidence_map.items():
            # Concept belongs to this competency if explicitly assigned or in expected pool
            is_relevant = (
                ev.competency == competency or
                any(exp.lower() in c.lower() or c.lower() in exp.lower() for exp in expected_pool)
            )
            if not is_relevant:
                continue

            for qt in ev.questionTypes:
                question_types.add(qt)
            for st in ev.stages:
                stages.add(st)

            if ev.demonstratedCount > 0 and ev.missedCount == 0:
                demonstrated.append(c)
            elif ev.demonstratedCount > 0 and ev.missedCount > 0:
                if ev.masteryLevel == "recovered":
                    demonstrated.append(c)
                else:
                    contradictory.append(c)
                    partial.append(c)
            elif ev.partialCount > 0 and ev.demonstratedCount == 0:
                partial.append(c)
            elif ev.missedCount > 0 and ev.demonstratedCount == 0:
                missing.append(c)

        tested_concepts = list(dict.fromkeys(demonstrated + partial + missing + contradictory))

        # 3. Calculate Evidence Coverage (tested expected concepts / total expected concepts)
        if expected_pool:
            tested_expected_hits = sum(
                1 for exp in expected_pool
                if any(exp.lower() in tc.lower() or tc.lower() in exp.lower() for tc in tested_concepts)
            )
            coverage = round(tested_expected_hits / len(expected_pool), 2)
        else:
            coverage = 1.0 if tested_concepts else 0.0

        # 4. Handle Untested Competencies
        if not relevant_turns and not tested_concepts:
            return CompetencyEvidence(
                competency=competency,
                score=0,
                confidence=0.0,
                coverage=0.0,
                status="untested",
                testedConcepts=[],
                demonstratedConcepts=[],
                partialConcepts=[],
                missingConcepts=[],
                evidenceCount=0,
                strongEvidence=[],
                weakEvidence=[],
                contradictoryEvidence=[],
                reasoning=f"Competency '{competency}' was not tested or observed in this interview session."
            )

        # 5. Handle Minimal / Insufficient Evidence (1 turn or 1 concept)
        if len(relevant_turns) <= 1 and len(tested_concepts) <= 1:
            raw_score = turn_scores[0] if turn_scores else 60
            conf = 0.40
            status = "insufficient_evidence"
            
            if demonstrated:
                strong_ev = [f"Demonstrated '{demonstrated[0]}' with score {raw_score}/100 in Turn {relevant_turns[0].get('turn', 1)}"]
                weak_ev = []
                reasoning = (
                    f"Candidate demonstrated '{demonstrated[0]}' (score {raw_score}/100), "
                    f"but evidence depth is insufficient (only 1 turn evaluated; coverage is {coverage:.0%})."
                )
            elif missing:
                strong_ev = []
                weak_ev = [f"Omitted '{missing[0]}' in Turn {relevant_turns[0].get('turn', 1)} (score {raw_score}/100)"]
                reasoning = (
                    f"Candidate struggled on '{missing[0]}' (score {raw_score}/100), "
                    f"but broader competency coverage remains insufficient (coverage {coverage:.0%})."
                )
            else:
                strong_ev = []
                weak_ev = []
                reasoning = f"Single evaluated turn on '{competency}' (score {raw_score}/100); insufficient evidence depth to confirm mastery."

            return CompetencyEvidence(
                competency=competency,
                score=raw_score,
                confidence=conf,
                coverage=coverage,
                status=status,
                testedConcepts=tested_concepts,
                demonstratedConcepts=demonstrated,
                partialConcepts=partial,
                missingConcepts=missing,
                evidenceCount=len(relevant_turns),
                strongEvidence=strong_ev,
                weakEvidence=weak_ev,
                contradictoryEvidence=contradictory,
                reasoning=reasoning
            )

        # 6. Calculate Proficiency Score (Deterministic Engineering Formula)
        avg_turn_score = sum(turn_scores) / len(turn_scores) if turn_scores else 60.0
        
        # Concept demonstration ratio
        total_eval_concepts = len(demonstrated) + len(partial) + len(missing)
        if total_eval_concepts > 0:
            demo_ratio = (len(demonstrated) + 0.5 * len(partial)) / total_eval_concepts
        else:
            demo_ratio = 0.5

        # Weighted calculation: 65% observed answer scores + 35% concept demonstration ratio
        comp_score = int(round(0.65 * avg_turn_score + 0.35 * (demo_ratio * 100)))
        comp_score = max(0, min(100, comp_score))

        # 7. Calculate Evidence Confidence
        # Base confidence from turn count
        turn_cnt = len(relevant_turns)
        if turn_cnt >= 3:
            conf_base = 0.85
        elif turn_cnt == 2:
            conf_base = 0.72
        else:
            conf_base = 0.45

        # Diversity bonus: tested across multiple question types
        if len(question_types) >= 2:
            conf_base += 0.06

        # Coverage factor bonus
        if coverage >= 0.50:
            conf_base += 0.05

        # Breadth bonus: demonstrated multiple concepts in competency
        if len(demonstrated) >= 2:
            conf_base += 0.08

        # Contradictory penalty
        if contradictory:
            conf_base = max(0.30, conf_base - 0.15)


        confidence = round(max(0.0, min(0.95, conf_base)), 2)

        # 8. Determine Status
        if confidence < 0.50 and turn_cnt <= 1:
            status = "insufficient_evidence"
        elif comp_score >= 75 and len(missing) == 0:
            status = "demonstrated"
        elif comp_score >= 60:
            status = "partially_demonstrated"
        else:
            status = "weak"

        # 9. Format Strong and Weak Evidence lists
        strong_ev = []
        for d in demonstrated:
            strong_ev.append(f"Demonstrated '{d}' across {concept_evidence_map[d].testedCount} turn(s)")
        
        weak_ev = []
        for m in missing:
            weak_ev.append(f"Omitted or struggled with '{m}'")

        # 10. Synthesize Explainable Evidence-Backed Reasoning
        turns_summary = f"{len(relevant_turns)} evaluated turn(s) with average score {avg_turn_score:.0f}/100"
        concepts_summary = f"{len(demonstrated)} demonstrated, {len(partial)} partial, {len(missing)} missing"
        
        reasoning = (
            f"Competency score is {comp_score}/100 (confidence: {confidence:.2f}, coverage: {coverage:.0%}) "
            f"derived from {turns_summary}. "
            f"Concepts evaluated: {concepts_summary}. "
        )
        if demonstrated:
            reasoning += f"Key demonstrated strengths: {', '.join(demonstrated[:3])}. "
        if missing:
            reasoning += f"Identified gaps: {', '.join(missing[:2])}. "
        if contradictory:
            reasoning += f"Contradictory evidence noted in {', '.join(contradictory)}. "

        return CompetencyEvidence(
            competency=competency,
            score=comp_score,
            confidence=confidence,
            coverage=coverage,
            status=status,
            testedConcepts=tested_concepts,
            demonstratedConcepts=demonstrated,
            partialConcepts=partial,
            missingConcepts=missing,
            evidenceCount=len(relevant_turns),
            strongEvidence=strong_ev,
            weakEvidence=weak_ev,
            contradictoryEvidence=contradictory,
            reasoning=reasoning.strip()
        )
