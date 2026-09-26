"""
Final Selector Scorecard & Evidence Synthesis Engine for BoardRoom AI (Phase D).
Aggregates the complete interview trajectory into:
1. Competency-Level Evidence Assessments
2. Technical vs Managerial Evidence Breakdown
3. Evidence-Backed Strengths & Gaps
4. Role Alignment Analysis
5. Chronological Machine-Readable Evidence Timeline
6. Frontend-Ready Dashboard Coverage Data
7. Explainable Decision Support for Human Selectors (strictly non-autonomous)
"""

from typing import Dict, List, Optional, Any
from core.schemas import (
    CandidateProfile,
    TargetRole,
    FinalScorecard,
    CompetencyEvidence,
    StrengthItem,
    GapItem,
    RoleAlignmentItem,
    RoleAlignmentAnalysis,
    EvidenceTimelineItem,
    CompetencyCoverageData,
    CoverageDashboardData,
    DecisionSupportReport
)
from adaptive.state import InterviewState
from adaptive.competency_matrix import RoleCompetencyMatrix
from adaptive.concept_evidence import ConceptEvidenceAggregator
from adaptive.competency_evaluator import CompetencyEvaluator
from adaptive.confidence import EvidenceConfidenceTracker
from adaptive.prerequisites import ConceptPrerequisiteEngine


class ScorecardEngine:
    """
    Central engine synthesizing accumulated interview evidence into an explainable FinalScorecard.
    """

    @classmethod
    def generate_scorecard(
        cls,
        state: InterviewState,
        candidate: Optional[CandidateProfile] = None,
        role: Optional[TargetRole] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> FinalScorecard:
        candidate = candidate or CandidateProfile()
        role = role or TargetRole()

        # 1. Aggregate Concept Evidence
        concept_evidence_map = ConceptEvidenceAggregator.aggregate_from_state(state)

        # 2. Evaluate Competency Evidence
        competencies = CompetencyEvaluator.evaluate_all_competencies(
            state=state,
            role_id=role.id,
            concept_evidence_map=concept_evidence_map
        )

        # 3. Calculate Overall Score & Confidence (Weighted by Role Competency Matrix)
        weights = RoleCompetencyMatrix.get_normalized_weights(role.id, custom_weights)
        
        weighted_score_sum = 0.0
        weighted_conf_sum = 0.0
        total_active_weight = 0.0

        for comp_ev in competencies:
            w = weights.get(comp_ev.competency, 0.20)
            if comp_ev.status != "untested":
                weighted_score_sum += comp_ev.score * w
                weighted_conf_sum += comp_ev.confidence * w
                total_active_weight += w

        session_evidence_coverage = EvidenceConfidenceTracker.compute_evidence_coverage(state)
        if total_active_weight > 0:
            overall_score = int(round(weighted_score_sum / total_active_weight))
            mean_comp_conf = weighted_conf_sum / total_active_weight
            overall_confidence = round(0.50 * mean_comp_conf + 0.50 * session_evidence_coverage, 2)
        else:
            overall_score = 0
            overall_confidence = 0.0


        overall_score = max(0, min(100, overall_score))
        overall_confidence = max(0.0, min(1.0, overall_confidence))

        # 4. Extract Evidence-Backed Strengths
        strengths = cls._extract_strengths(concept_evidence_map)

        # 5. Extract Evidence-Backed Gaps
        gaps = cls._extract_gaps(state, concept_evidence_map)

        # 6. Analyze Role Alignment
        role_alignment = cls._analyze_role_alignment(role, state, concept_evidence_map)

        # 7. Generate Evidence Timeline
        timeline = cls._generate_evidence_timeline(state)

        # 8. Build Coverage Dashboard Data
        coverage_data = cls._build_coverage_dashboard(state, competencies, concept_evidence_map)

        # 9. Technical vs Managerial Decision Support Breakdown
        decision_support = cls._build_decision_support(state, competencies, role_alignment)

        # 10. Synthesize Narrative Report Explanation
        explanation = cls._synthesize_report_explanation(
            candidate=candidate,
            role=role,
            overall_score=overall_score,
            overall_confidence=overall_confidence,
            competencies=competencies,
            strengths=strengths,
            gaps=gaps,
            role_alignment=role_alignment,
            evidence_coverage=session_evidence_coverage
        )


        return FinalScorecard(
            candidate=candidate,
            role=role,
            overallScore=overall_score,
            overallConfidence=overall_confidence,
            competencies=competencies,
            strengths=strengths,
            gaps=gaps,
            coverage=coverage_data,
            roleAlignment=role_alignment,
            decisionSupport=decision_support,
            evidenceTimeline=timeline,
            explanation=explanation
        )

    @classmethod
    def _extract_strengths(cls, concept_evidence_map: Dict[str, Any]) -> List[StrengthItem]:
        """Identifies concepts demonstrated consistently or with high proficiency."""
        strengths: List[StrengthItem] = []

        # Sort concepts by confidence and demonstrated count descending
        sorted_concepts = sorted(
            concept_evidence_map.values(),
            key=lambda x: (x.demonstratedCount, x.confidence, x.highestScore),
            reverse=True
        )

        for ev in sorted_concepts:
            if ev.demonstratedCount > 0 and ev.highestScore >= 70:
                supporting_turns = [p.turnId for p in ev.provenance if p.isDemonstrated]
                turns_str = ", ".join(map(str, sorted(list(set(supporting_turns)))))
                
                evidence_text = (
                    f"Successfully demonstrated across {ev.demonstratedCount} turn(s) "
                    f"(Turn(s) {turns_str}) with top score {ev.highestScore}/100 and average {ev.averageScore:.0f}/100."
                )
                strengths.append(
                    StrengthItem(
                        area=ev.concept,
                        competency=ev.competency,
                        evidence=evidence_text,
                        confidence=ev.confidence,
                        supportingTurns=sorted(list(set(supporting_turns)))
                    )
                )

        return strengths[:6]

    @classmethod
    def _extract_gaps(cls, state: InterviewState, concept_evidence_map: Dict[str, Any]) -> List[GapItem]:
        """Extracts unmastered concepts, persistent weaknesses, and prerequisite gaps."""
        gaps: List[GapItem] = []

        # Concepts missed across turns
        for c, ev in concept_evidence_map.items():
            # If concept was recovered, do not treat it as an active gap
            if c in state.recovered_concepts:
                continue

            if ev.missedCount > 0 and ev.demonstratedCount == 0:
                supporting_turns = [p.turnId for p in ev.provenance if not p.isDemonstrated]
                turns_str = ", ".join(map(str, sorted(list(set(supporting_turns)))))

                # Check prerequisite status
                prereqs_met, unmet = ConceptPrerequisiteEngine.check_prerequisites_met(
                    target_concept=c,
                    demonstrated_concepts=state.demonstrated_concepts,
                    missing_concepts=state.missing_concepts
                )
                prereq_status = f"Unmet prerequisite: {', '.join(unmet)}" if not prereqs_met and unmet else None

                severity = "high" if (c in state.persistent_weaknesses or ev.missedCount >= 2) else "moderate"
                evidence_text = (
                    f"Omitted or struggled across {ev.missedCount} turn(s) "
                    f"(Turn(s) {turns_str}); lowest/latest score was {ev.latestScore}/100."
                )

                gaps.append(
                    GapItem(
                        area=c,
                        competency=ev.competency,
                        evidence=evidence_text,
                        severity=severity,
                        supportingTurns=sorted(list(set(supporting_turns))),
                        prerequisiteStatus=prereq_status
                    )
                )

        # Sort gaps: high severity first
        gaps.sort(key=lambda g: (0 if g.severity == "high" else 1, len(g.supportingTurns)), reverse=False)
        return gaps[:6]

    @classmethod
    def _analyze_role_alignment(
        cls,
        role: TargetRole,
        state: InterviewState,
        concept_evidence_map: Dict[str, Any]
    ) -> RoleAlignmentAnalysis:
        """Compares stated role requirements against candidate demonstrated evidence."""
        reqs = role.required_skills or ["Python", "SQL", "REST APIs", "System Design"]
        
        demonstrated_reqs: List[str] = []
        partial_reqs: List[str] = []
        insufficient_reqs: List[str] = []
        missing_reqs: List[str] = []
        items: List[RoleAlignmentItem] = []

        for req in reqs:
            req_lower = req.lower().strip()
            
            # Find matching concept evidence
            matching_ev = [
                ev for c, ev in concept_evidence_map.items()
                if req_lower in c.lower() or c.lower() in req_lower
            ]

            if not matching_ev:
                insufficient_reqs.append(req)
                items.append(
                    RoleAlignmentItem(
                        requirement=req,
                        status="insufficiently_tested",
                        evidence=f"Requirement '{req}' was not directly evaluated during this session.",
                        confidence=0.0
                    )
                )
            else:
                top_ev = max(matching_ev, key=lambda x: (x.demonstratedCount, x.highestScore))
                if top_ev.demonstratedCount >= 1 and top_ev.missedCount == 0:
                    demonstrated_reqs.append(req)
                    items.append(
                        RoleAlignmentItem(
                            requirement=req,
                            status="demonstrated",
                            evidence=f"Demonstrated via '{top_ev.concept}' (score: {top_ev.highestScore}/100 across {top_ev.testedCount} turns).",
                            confidence=top_ev.confidence
                        )
                    )
                elif top_ev.demonstratedCount > 0 and top_ev.missedCount > 0:
                    partial_reqs.append(req)
                    items.append(
                        RoleAlignmentItem(
                            requirement=req,
                            status="partially_demonstrated",
                            evidence=f"Partial mastery of '{top_ev.concept}' (both positive and struggling signals observed).",
                            confidence=top_ev.confidence
                        )
                    )
                elif top_ev.partialCount > 0:
                    partial_reqs.append(req)
                    items.append(
                        RoleAlignmentItem(
                            requirement=req,
                            status="partially_demonstrated",
                            evidence=f"Adequate foundational knowledge observed for '{top_ev.concept}'.",
                            confidence=top_ev.confidence
                        )
                    )
                else:
                    missing_reqs.append(req)
                    items.append(
                        RoleAlignmentItem(
                            requirement=req,
                            status="missing",
                            evidence=f"Candidate struggled or omitted concepts related to '{req}'.",
                            confidence=top_ev.confidence
                        )
                    )

        total_reqs = len(reqs)
        alignment_score = int(round(
            (len(demonstrated_reqs) * 100 + len(partial_reqs) * 50) / max(1, total_reqs)
        ))
        alignment_score = max(0, min(100, alignment_score))

        rationale = (
            f"Candidate satisfies {len(demonstrated_reqs)}/{total_reqs} mandatory role requirements "
            f"with verified evidence. {len(partial_reqs)} requirement(s) are partially verified, "
            f"and {len(insufficient_reqs)} remain unverified."
        )

        return RoleAlignmentAnalysis(
            roleId=role.id,
            roleTitle=role.title,
            alignmentScore=alignment_score,
            demonstratedRequirements=demonstrated_reqs,
            partiallyDemonstratedRequirements=partial_reqs,
            insufficientlyTestedRequirements=insufficient_reqs,
            missingRequirements=missing_reqs,
            details=items,
            rationale=rationale
        )

    @classmethod
    def _generate_evidence_timeline(cls, state: InterviewState) -> List[EvidenceTimelineItem]:
        """Converts interview turns into a machine-readable chronological timeline."""
        timeline: List[EvidenceTimelineItem] = []
        turns = getattr(state, "turns", [])

        for t in turns:
            turn_idx = t.get("turn", 1)
            stage = t.get("stage", "role_technical")
            comp = t.get("competency", "backend")
            diff = t.get("difficulty", 1)
            q_id = t.get("question_id", "q")
            q_text = t.get("question_text", "")
            q_type = t.get("question_type", "conceptual")
            score = t.get("score", 70)
            covered = t.get("covered_concepts", [])
            missing = t.get("missing_concepts", [])

            # Determine turn status
            if any(c in state.recovered_concepts for c in covered) and score >= 75:
                status = "recovered"
            elif score >= 75 and covered:
                status = "demonstrated"
            elif score >= 50:
                status = "partially_demonstrated"
            else:
                status = "missing"

            summary = f"Turn {turn_idx} ({comp}, diff {diff}/5, {q_type}): score {score}/100. Status: {status}."
            if covered:
                summary += f" Demonstrated: {', '.join(covered)}."
            if missing:
                summary += f" Gaps: {', '.join(missing)}."

            timeline.append(
                EvidenceTimelineItem(
                    turn=turn_idx,
                    stage=stage,
                    competency=comp,
                    difficulty=diff,
                    questionId=q_id,
                    questionText=q_text,
                    questionType=q_type,
                    score=score,
                    coveredConcepts=covered,
                    missingConcepts=missing,
                    evidenceStatus=status,
                    summary=summary
                )
            )

        return timeline

    @classmethod
    def _build_coverage_dashboard(
        cls,
        state: InterviewState,
        competencies: List[CompetencyEvidence],
        concept_evidence_map: Dict[str, Any]
    ) -> CoverageDashboardData:
        """Constructs dashboard-ready structured coverage breakdown."""
        overall_coverage = EvidenceConfidenceTracker.compute_evidence_coverage(state)
        comp_coverage_list: List[CompetencyCoverageData] = []

        for c in competencies:
            comp_coverage_list.append(
                CompetencyCoverageData(
                    competency=c.competency,
                    coverage=c.coverage,
                    score=c.score,
                    confidence=c.confidence,
                    status=c.status
                )
            )

        return CoverageDashboardData(
            overallEvidenceCoverage=overall_coverage,
            competencyCoverage=comp_coverage_list,
            testedConceptsCount=len(concept_evidence_map),
            demonstratedConceptsCount=len(state.demonstrated_concepts),
            missingConceptsCount=len(state.missing_concepts),
            stagesVisitedCount=sum(1 for cnt in state.stage_question_counts.values() if cnt > 0)
        )

    @classmethod
    def _build_decision_support(
        cls,
        state: InterviewState,
        competencies: List[CompetencyEvidence],
        role_alignment: RoleAlignmentAnalysis
    ) -> DecisionSupportReport:
        """Generates clear, separated decision support for technical and managerial dimensions."""
        turns = getattr(state, "turns", [])
        
        # Technical turns summary
        tech_turns = [
            t for t in turns
            if t.get("competency") in ("backend", "database", "system_design", "cs_fundamentals")
        ]
        if tech_turns:
            avg_tech = sum(t["score"] for t in tech_turns) / len(tech_turns)
            tech_summary = (
                f"Candidate completed {len(tech_turns)} technical turn(s) with an average score of {avg_tech:.0f}/100. "
                f"Demonstrated technical core proficiency across {len(state.demonstrated_concepts)} concepts."
            )
        else:
            tech_summary = "Limited technical evidence observed."

        # Managerial / Scenario turns summary
        man_turns = [
            t for t in turns
            if t.get("stage") == "scenario_managerial" or t.get("competency") == "scenario_managerial"
        ]
        if man_turns:
            avg_man = sum(t["score"] for t in man_turns) / len(man_turns)
            man_summary = (
                f"Evaluated across {len(man_turns)} scenario/managerial turn(s) (average score {avg_man:.0f}/100). "
                f"Candidate exhibited appropriate communication and decision-making trade-offs."
            )
        else:
            man_summary = "Insufficient managerial evidence — interview session focused on technical competencies."

        # Role suitability summary
        suitability = (
            f"Candidate role alignment score is {role_alignment.alignmentScore}/100. "
            f"{len(role_alignment.demonstratedRequirements)} requirements demonstrated; "
            f"{len(role_alignment.insufficientlyTestedRequirements)} requirement(s) require further inquiry."
        )

        # Areas requiring further assessment
        further_assessment = []
        for c in competencies:
            if c.status == "insufficient_evidence":
                further_assessment.append(f"{c.competency.capitalize()} (insufficient depth; only {c.evidenceCount} turn)")
            elif c.status == "untested":
                further_assessment.append(f"{c.competency.capitalize()} (untested)")
            elif c.status == "weak":
                further_assessment.append(f"{c.competency.capitalize()} (identified technical gaps: {', '.join(c.missingConcepts[:2])})")

        for req in role_alignment.insufficientlyTestedRequirements:
            further_assessment.append(f"Role Requirement: {req}")

        return DecisionSupportReport(
            technicalEvidence=tech_summary,
            managerialEvidence=man_summary,
            roleAlignmentEvidence=suitability,
            areasRequiringFurtherAssessment=list(dict.fromkeys(further_assessment)),
            recommendationNote="Decision-support summary for human selector. BoardRoom AI does not make autonomous hiring decisions."
        )

    @classmethod
    def _synthesize_report_explanation(
        cls,
        candidate: CandidateProfile,
        role: TargetRole,
        overall_score: int,
        overall_confidence: float,
        competencies: List[CompetencyEvidence],
        strengths: List[StrengthItem],
        gaps: List[GapItem],
        role_alignment: RoleAlignmentAnalysis,
        evidence_coverage: float = 0.0
    ) -> str:
        """
        Synthesizes an explainable, non-generic report narrative derived strictly from actual evidence.
        """
        cand_name = candidate.name or "Candidate"
        role_title = role.title or "Target Role"

        paragraphs = []
        paragraphs.append(
            f"**Candidate Evaluation Summary for {cand_name} ({role_title})**\n"
            f"The candidate achieved an overall weighted competency score of {overall_score}/100 "
            f"with an evidence confidence of {overall_confidence:.2f} (evidence coverage: {evidence_coverage:.0%}, role alignment: {role_alignment.alignmentScore}%). "
            f"This evaluation is strictly derived from multi-turn interview responses and concept demonstration provenance."
        )


        comp_lines = []
        for c in competencies:
            comp_lines.append(f"- **{c.competency.capitalize()}**: {c.score}/100 (Confidence: {c.confidence:.2f}, Status: {c.status}) — {c.reasoning}")
        paragraphs.append("**Competency Breakdown:**\n" + "\n".join(comp_lines))

        if strengths:
            str_lines = [f"- **{s.area}** ({s.competency}): {s.evidence}" for s in strengths[:4]]
            paragraphs.append("**Verified Strengths:**\n" + "\n".join(str_lines))

        if gaps:
            gap_lines = [f"- **{g.area}** ({g.competency}, severity: {g.severity}): {g.evidence}" for g in gaps[:4]]
            paragraphs.append("**Areas for Development / Gaps:**\n" + "\n".join(gap_lines))

        paragraphs.append(
            f"**Selector Recommendation Guidance:**\n"
            f"{role_alignment.rationale} Human interviewers should consult the detailed evidence timeline "
            f"before making final hiring decisions."
        )

        return "\n\n".join(paragraphs)
