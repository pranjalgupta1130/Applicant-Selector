"""
Deterministic Target Concept Selection Layer for BoardRoom AI (Phase C).
Selects the next conceptual target with explainable deterministic priority:
1. Persistent unresolved weaknesses
2. Prerequisite gaps
3. Latest missing concepts
4. Repeatedly missing concepts
5. Stage / competency requirements & coverage gaps
"""

from typing import List, Optional, Dict
from adaptive.state import InterviewState
from adaptive.prerequisites import ConceptPrerequisiteEngine
from adaptive.policy import PolicyDecision


from core.concepts import (
    COMPETENCY_CORE_CONCEPTS,
    get_canonical_concepts_for_competency,
    get_all_canonical_concepts
)




class TargetConceptSelector:
    """
    Deterministic Concept Selection Engine.
    Ensures that every generated question has a traceably justified target concept.
    """

    @classmethod
    def select_targets(
        cls,
        state: InterviewState,
        policy_decision: Optional[PolicyDecision] = None,
        candidate_skills: Optional[List[str]] = None
    ) -> List[str]:
        # 1. Check for persistent unresolved weaknesses
        unresolved_pw = [
            w for w in state.persistent_weaknesses
            if w not in state.demonstrated_concepts and w not in state.recovered_concepts
        ]
        if policy_decision and policy_decision.strategy == "remediate_persistent_weakness":
            if policy_decision.target_concepts:
                return list(policy_decision.target_concepts)
            if unresolved_pw:
                return [unresolved_pw[0]]

        # 2. Check for prerequisite gaps
        unresolved_missing = [
            m for m in state.missing_concepts
            if m not in state.demonstrated_concepts
        ]
        for m in unresolved_missing:
            prereqs_met, unmet = ConceptPrerequisiteEngine.check_prerequisites_met(
                target_concept=m,
                demonstrated_concepts=state.demonstrated_concepts,
                missing_concepts=state.missing_concepts
            )
            if not prereqs_met and unmet:
                if policy_decision and policy_decision.strategy == "reinforce_prerequisite":
                    if policy_decision.target_concepts:
                        return list(policy_decision.target_concepts)
                return [unmet[0]]

        # 3. Check for immediate gap probing (latest missing concepts)
        if policy_decision and policy_decision.strategy == "probe_missing_concept":
            if policy_decision.target_concepts:
                return list(policy_decision.target_concepts)
            if unresolved_missing:
                return [unresolved_missing[0]]

        # 4. Check for repeatedly missing concepts
        unresolved_repeated = [
            m for m in state.repeatedly_missing_concepts
            if m not in state.demonstrated_concepts and m not in state.recovered_concepts
        ]
        if unresolved_repeated:
            return [unresolved_repeated[0]]

        # If policy already has explicit target concepts, use them
        if policy_decision and policy_decision.target_concepts:
            return list(policy_decision.target_concepts)

        # 5. Competency & stage requirements / coverage gaps
        competency = policy_decision.next_competency if policy_decision else state.current_competency
        comp_pool = COMPETENCY_CORE_CONCEPTS.get(competency, COMPETENCY_CORE_CONCEPTS.get("backend", []))

        # Filter out concepts already demonstrated or tested
        untested_in_competency = [
            c for c in comp_pool
            if c not in state.demonstrated_concepts and c not in state.concept_map
        ]
        if untested_in_competency:
            return [untested_in_competency[0]]

        # If all core concepts tested, return top untested or partially demonstrated
        partially = [
            c for c in comp_pool
            if c in state.partially_demonstrated_concepts and c not in state.demonstrated_concepts
        ]
        if partially:
            return [partially[0]]

        # Default fallback to primary concept of competency
        return [comp_pool[0]] if comp_pool else ["system design"]
