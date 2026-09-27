"""
Concept Prerequisite Dependency Graph for BoardRoom AI.
Provides lightweight, deterministic concept prerequisite checking
without external vector databases or graph engines.
"""

from typing import Dict, List, Tuple, Optional


# Curated prerequisite dependency graph:
# dependent_concept -> list of required prerequisite concepts
CONCEPT_PREREQUISITE_GRAPH: Dict[str, List[str]] = {
    # Database Internals: B-Tree fundamentals -> indexing trade-offs -> write amplification
    "write amplification": ["indexing trade-offs", "B-Tree indexing"],
    "indexing trade-offs": ["B-Tree indexing"],
    "composite indexing": ["B-Tree indexing"],
    "cross-shard queries": ["database sharding"],
    "distributed transactions": ["database transactions"],
    "two-phase commit": ["distributed transactions"],
    "distributed locking": ["mutex synchronization"],
    "concurrency race conditions": ["threads vs processes"],
    # DRDO / RAC Scientific Concept Prerequisite Dependencies
    "Priority Inversion & Ceiling Protocol": ["RTOS Priority Preemption"],
    "DMA Scatter-Gather": ["Interrupt Latency & ISRs"],
    "Digital Pulse Compression": ["Nyquist-Shannon Sampling Theorem", "Discrete Fourier Transform / FFT"],
    "Adaptive Beamforming": ["Discrete Fourier Transform / FFT", "FIR vs IIR Digital Filters"],
    "AESA Beamforming": ["Radar Range Equation", "Doppler Frequency Shift"],
    "FMCW Radar Principles": ["Radar Range Equation"],
    "DO-254 / DO-178C Guidelines": ["FMECA Risk Mitigation"],
    "Triple Modular Redundancy": ["MIL-STD-1553B Dual-Redundant Bus"]
}


class ConceptPrerequisiteEngine:
    """
    Lightweight deterministic engine that checks prerequisite satisfaction
    and prevents jumping to advanced concepts prematurely.
    """

    @classmethod
    def normalize_concept(cls, concept: str) -> str:
        """Normalizes concept string for robust graph lookup."""
        return concept.strip().lower()

    @classmethod
    def get_prerequisites(cls, concept: str) -> List[str]:
        """Returns direct prerequisite concepts for a given target concept."""
        target_norm = cls.normalize_concept(concept)
        for c, prereqs in CONCEPT_PREREQUISITE_GRAPH.items():
            if cls.normalize_concept(c) == target_norm or target_norm in cls.normalize_concept(c):
                return list(prereqs)
        return []

    @classmethod
    def check_prerequisites_met(
        cls,
        target_concept: str,
        demonstrated_concepts: List[str],
        missing_concepts: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Determines whether all prerequisites for target_concept have been demonstrated.
        Returns:
            (is_met: bool, unmet_prerequisites: List[str])
        """
        prereqs = cls.get_prerequisites(target_concept)
        if not prereqs:
            return True, []

        norm_demonstrated = {cls.normalize_concept(d) for d in demonstrated_concepts}
        norm_missing = {cls.normalize_concept(m) for m in (missing_concepts or [])}

        unmet = []
        for p in prereqs:
            norm_p = cls.normalize_concept(p)
            # Prerequisite is unmet if:
            # 1. It is explicitly in missing concepts, OR
            # 2. It is not demonstrated yet (no partial or exact match in demonstrated)
            is_demonstrated = any(norm_p in d or d in norm_p for d in norm_demonstrated)
            is_missing = any(norm_p in m or m in norm_p for m in norm_missing)

            if is_missing or not is_demonstrated:
                unmet.append(p)

        return (len(unmet) == 0), unmet
