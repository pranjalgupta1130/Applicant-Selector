"""
Canonical Source of Truth for Competency Concepts and Keywords in BoardRoom AI.
Provides unified, auditable concept definitions used consistently across:
1. Grounded RAG Retrieval (rag/retriever.py)
2. Question Relevance Evaluation (evaluator/relevance.py)
3. Target Concept Selection (adaptive/target_concept.py)
4. Competency Matrix & Evaluation (adaptive/competency_matrix.py, adaptive/competency_evaluator.py)
5. Final Scorecard Synthesis (adaptive/scorecard_engine.py)
"""

from typing import Dict, List


# Canonical competency core concepts
COMPETENCY_CORE_CONCEPTS: Dict[str, List[str]] = {
    "backend": [
        "REST APIs",
        "statelessness",
        "HTTP status codes",
        "idempotency",
        "JWT authentication",
        "refresh token rotation",
        "concurrency race conditions",
        "mutex synchronization"
    ],
    "database": [
        "B-Tree indexing",
        "composite indexing",
        "indexing trade-offs",
        "write amplification",
        "database transactions",
        "ACID guarantees",
        "database sharding",
        "cross-shard queries"
    ],
    "system_design": [
        "horizontal scaling",
        "load balancing",
        "stateless application tier",
        "read replicas",
        "caching strategies",
        "cache invalidation",
        "distributed locking",
        "two-phase commit"
    ],
    "cs_fundamentals": [
        "time complexity",
        "space complexity",
        "hash tables",
        "threads vs processes",
        "memory management"
    ],
    "scenario_managerial": [
        "incident triage",
        "post-mortem analysis",
        "technical debt management",
        "code review practices"
    ],
    "ice_breaker": [
        "software architecture overview",
        "recent technical project",
        "core engineering strengths"
    ],
    # ---------------------------------------------------------
    # DRDO / RAC Scientific & Engineering Demonstration Domain
    # ---------------------------------------------------------
    "embedded_realtime_systems": [
        "Interrupt Latency & ISRs",
        "RTOS Priority Preemption",
        "Priority Inversion & Ceiling Protocol",
        "Watchdog Timers",
        "DMA Scatter-Gather",
        "Bare-Metal vs RTOS"
    ],
    "digital_signal_processing": [
        "Nyquist-Shannon Sampling Theorem",
        "Discrete Fourier Transform / FFT",
        "FIR vs IIR Digital Filters",
        "Fixed-Point Quantization",
        "Digital Pulse Compression",
        "Adaptive Beamforming"
    ],
    "radar_rf_systems": [
        "Radar Range Equation",
        "Pulse Repetition Frequency (PRF)",
        "Doppler Frequency Shift",
        "FMCW Radar Principles",
        "AESA Beamforming",
        "Receiver Dynamic Range"
    ],
    "avionics_communication": [
        "MIL-STD-1553B Dual-Redundant Bus",
        "ARINC-429 Serial Protocol",
        "Phase Locked Loops (PLL)",
        "Digital Modulation BPSK/QPSK",
        "EMI/EMC Shielding",
        "Triple Modular Redundancy"
    ],
    "techno_managerial": [
        "FMECA Risk Mitigation",
        "DO-254 / DO-178C Guidelines",
        "MTBF Reliability Prediction",
        "Obsolescence Management",
        "Multi-Disciplinary Engineering Leadership"
    ],
    "expertise_validation": [
        "claim verification",
        "hands-on project implementation",
        "design constraint trade-offs",
        "individual technical ownership"
    ]
}


# Lexical keywords for grounding and relevance evaluation
_BASE_COMPETENCY_KEYWORDS: Dict[str, List[str]] = {
    "cs_fundamentals": [
        "oop", "inheritance", "composition", "polymorphism", "encapsulation",
        "process", "thread", "concurrency", "stack", "heap", "memory",
        "garbage collection", "tcp", "handshake", "socket", "git", "os"
    ],
    "backend": [
        "rest", "api", "http", "verb", "idempotent", "stateless", "jwt",
        "auth", "token", "refresh", "session", "middleware", "rate limit",
        "cookie", "endpoint", "controller", "payload", "microservice"
    ],
    "database": [
        "sql", "nosql", "index", "b-tree", "acid", "transaction", "isolation",
        "read committed", "repeatable read", "phantom", "table scan",
        "migration", "schema", "connection pool", "wal", "foreign key"
    ],
    "system_design": [
        "cache", "redis", "cache-aside", "write-through", "ttl", "stampede",
        "load balancer", "layer 4", "layer 7", "sharding", "consistent hashing",
        "cap theorem", "pacelc", "message queue", "kafka", "cqrs", "event sourcing"
    ],
    "scenario_managerial": [
        "incident", "production", "outage", "timeout", "504", "cpu",
        "triage", "mitigate", "post-mortem", "technical debt", "stakeholder",
        "prioritize", "code review", "mentor", "velocity", "refactor"
    ],
    "ice_breaker": [
        "background", "project", "experience", "journey", "role", "introduction",
        "interest", "learning", "tech stack", "tools", "challenge", "specialization"
    ],
    "embedded_realtime_systems": [
        "interrupt", "latency", "isr", "rtos", "freertos", "preemption", "priority",
        "inversion", "ceiling", "mutex", "semaphore", "watchdog", "timer", "dma",
        "scatter-gather", "bare-metal", "microcontroller", "arm", "cortex", "jitter"
    ],
    "digital_signal_processing": [
        "dsp", "nyquist", "sampling", "aliasing", "fourier", "dft", "fft", "fir",
        "iir", "filter", "quantization", "fixed-point", "floating-point", "pulse compression",
        "chirp", "beamforming", "spectral", "frequency", "bandwidth", "decimation"
    ],
    "radar_rf_systems": [
        "radar", "range equation", "prf", "pri", "doppler", "velocity", "fmcw",
        "chirp", "aesa", "phased array", "dynamic range", "noise figure", "rcs",
        "cross section", "receiver", "transmitter", "antenna", "clutter", "mti"
    ],
    "avionics_communication": [
        "avionics", "mil-std-1553", "1553b", "arinc-429", "arinc", "bus controller",
        "remote terminal", "pll", "modulation", "bpsk", "qpsk", "emi", "emc",
        "shielding", "triple modular redundancy", "tmr", "fault tolerance", "telemetry"
    ],
    "techno_managerial": [
        "fmeca", "fmea", "risk", "mitigation", "do-254", "do-178c", "safety-critical",
        "mtbf", "reliability", "lifecycle", "obsolescence", "qualification",
        "multidisciplinary", "prioritization", "traceability", "system engineering"
    ],
    "expertise_validation": [
        "claimed", "project", "hands-on", "implementation", "ownership",
        "architecture", "hardware", "firmware", "schematic", "validation"
    ]
}


def build_unified_competency_keyword_map() -> Dict[str, List[str]]:
    """
    Builds the unified competency keyword map by merging base keywords with canonical concepts.
    Uses exact phrases and words with len >= 4 to avoid false substring matches.
    """
    unified: Dict[str, List[str]] = {}
    for comp, kw_list in _BASE_COMPETENCY_KEYWORDS.items():
        words = list(kw_list)
        for concept in COMPETENCY_CORE_CONCEPTS.get(comp, []):
            concept_lower = concept.lower()
            if concept_lower not in words:
                words.append(concept_lower)
            for part in concept_lower.split():
                if len(part) >= 4 and part not in words and part not in ("with", "from", "into", "over", "read"):
                    words.append(part)
        unified[comp] = list(dict.fromkeys(words))
    return unified


def get_canonical_concepts_for_competency(competency: str) -> List[str]:
    """Returns canonical assessment concepts for a given competency."""
    return list(COMPETENCY_CORE_CONCEPTS.get(competency, []))


def get_all_canonical_concepts() -> Dict[str, List[str]]:
    """Returns dictionary of all canonical competency concept definitions."""
    return {k: list(v) for k, v in COMPETENCY_CORE_CONCEPTS.items()}
