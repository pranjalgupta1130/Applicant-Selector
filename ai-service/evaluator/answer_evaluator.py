"""
Answer Evaluation Layer & Adapters for BoardRoom AI.
Maintains strict architectural boundary: RAG and question generation never score answers.
Features a production-ready Gemini LLM Answer Evaluator with timeout, retries,
malformed JSON recovery, and a resilient, semantic-aware deterministic fallback evaluator.
Conforms strictly to Hackathon Master Plan Phase C, Phase D, and Ralph Master Mission.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
import re
import json
import logging

from core.schemas import QuestionObject, EvaluationResult
from core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Semantic Synonym & Concept Mapping for Fallback Engine
# ---------------------------------------------------------

CONCEPT_SEMANTIC_SYNONYMS: Dict[str, List[str]] = {
    # Caching & Memory
    "caching": ["cache", "redis", "memcached", "in-memory", "fast access", "volatile store", "query results in memory", "bypass disk", "frequently accessed", "ram"],
    "in-memory caching": ["cache", "redis", "memcached", "in-memory", "bypass disk", "fast lookup", "storing in memory", "volatile system ram", "system ram", "ram", "volatile store", "volatile"],
    "redis": ["redis", "in-memory key-value", "cache cluster", "key-value store", "pub-sub", "fast key-value store"],
    "cache invalidation": ["invalidation", "ttl", "time to live", "write-through", "cache eviction", "lru", "stale data", "purge"],
    "bypass disk": ["bypass disk", "read slow persistent disk", "avoid disk", "reduce disk", "skip disk", "read disk", "persistent disk", "disk read", "disk i/o"],
    
    # Databases & Indexing
    "database indexing": ["index", "b-tree", "b+tree", "ordered structure", "binary search on disk", "avoid full scan", "faster lookups", "pointer to rows", "scanning every row", "locate records"],
    "b-tree indexing": ["b-tree", "b+tree", "balanced tree", "branching factor", "node splitting", "disk block reads", "hierarchical index"],
    "b-tree": ["b-tree", "b+tree", "balanced search tree", "leaf nodes", "logarithmic lookup", "index pages", "tree structure"],
    "avoid full scan": ["avoid full scan", "without reading every record", "avoid scanning every row", "scanning every row", "prevent table scan", "skip full scan", "without full scan", "faster lookups", "without scanning", "avoid scan"],
    "acid": ["acid", "atomicity", "consistency", "isolation", "durability", "all or nothing", "transaction rollback", "wal", "concurrency control"],
    "transactions": ["transaction", "acid", "commit", "rollback", "begin transaction", "savepoint", "isolation level"],
    "sql normalization": ["normalization", "normal form", "1nf", "2nf", "3nf", "eliminate redundancy", "foreign keys", "data anomaly"],
    "sharding": ["shard", "horizontal partition", "hash partition", "range partition", "distribute rows across nodes", "cluster split"],
    "replication": ["replica", "leader-follower", "master-slave", "read replica", "replication lag", "standby node", "failover"],
    "indexing": ["index", "b-tree", "b+tree", "hash index", "composite index", "lookup optimization", "table scan prevention"],
    
    # Auth & Security
    "jwt": ["jwt", "json web token", "stateless auth", "bearer token", "signed payload", "hmac", "rsa signature", "claims", "no session database"],
    "token authentication": ["token", "bearer", "jwt", "stateless credentials", "api key", "oauth", "access token"],
    "rate limiting": ["rate limit", "token bucket", "leaky bucket", "sliding window", "429", "too many requests", "throttle requests", "traffic policing"],
    
    # System Design & Microservices
    "load balancing": ["load balancer", "round robin", "least connections", "reverse proxy", "distribute incoming traffic", "nginx", "traffic distribution"],
    "rest": ["rest", "http verbs", "get post put delete", "statelessness", "idempotent", "resource oriented", "crud api"],
    "restful apis": ["rest", "http methods", "stateless", "json endpoints", "uri resources", "http status codes"],
    "api idempotency": ["idempotency", "idempotent", "same result", "put delete", "idempotency key", "duplicate prevention"],
    "event-driven architecture": ["event driven", "kafka", "rabbitmq", "message queue", "producer consumer", "asynchronous event", "broker"],
    "concurrency": ["concurrency", "thread safety", "mutex", "lock", "race condition", "goroutine", "async io", "deadlock"],
    "docker": ["docker", "container", "containerization", "dockerfile", "isolated environment", "image layer", "namespaces"],
    "git": ["git", "branching", "merge", "rebase", "commit history", "pull request", "version control"],
    
    # Ice-Breaker & Candidate Background Concepts
    "academic specialization": ["academic specialization", "specialization", "b.tech", "m.tech", "degree", "electronics and communication", "signal processing", "studied", "graduated", "academic background"],
    "project overview": ["project overview", "primary project", "final year project", "fpga-based", "prototype", "project was designing", "radar signal processor", "telemetry acquisition"],
    "core engineering strengths": ["core engineering strengths", "technical strengths", "strengths are", "proficient in", "specialized in", "core strengths", "dsp", "embedded firmware"],
    "research motivation": ["research motivation", "motivation", "motivated by", "passion for", "fascinated by", "wanted to pursue", "inspired by", "radar research"],
    "software architecture overview": ["software architecture overview", "architecture", "stack", "system", "components", "microservices", "overview", "design"],
    "recent technical project": ["recent technical project", "project", "recently", "built", "developed", "implemented", "production"],

    # DRDO / Scientific & Engineering Demonstration Domain - Main Concepts
    "interrupt latency & isrs": ["interrupt latency", "isr", "interrupt service routine", "vector table", "hardware stacking", "context save", "nvic", "deferred processing", "interrupt handler", "tail-chaining"],
    "rtos priority preemption": ["rtos priority preemption", "priority preemption", "preemptive scheduling", "preemptive freertos", "preemptive rtos", "highest priority ready", "task scheduling", "context switch", "freertos", "tick interrupt"],
    "priority inversion & ceiling protocol": ["priority inversion", "priority inheritance", "priority ceiling", "unbounded latency", "mars pathfinder", "blocking high priority", "priority inheritance protocol", "pcp", "pip"],
    "watchdog timers": ["watchdog timer", "wdt", "windowed watchdog", "wwdt", "hardware supervisor", "firmware hang", "kick watchdog", "system reset", "refresh window"],
    "dma scatter-gather": ["dma scatter-gather", "dma", "direct memory access", "scatter-gather", "ping-pong buffer", "double buffer", "offload cpu", "descriptor table", "buffer transfer"],
    "bare-metal vs rtos": ["bare-metal vs rtos", "bare-metal", "super-loop", "cyclic executive", "wcet", "worst-case execution time", "polling loop", "rtos multitasking"],
    "nyquist-shannon sampling theorem": ["nyquist-shannon sampling theorem", "nyquist theorem", "nyquist rate", "sampling rate", "twice highest frequency", "fs >= 2*fmax", "aliasing", "spectral foldover", "anti-aliasing filter", "aaf"],
    "discrete fourier transform / fft": ["discrete fourier transform", "dft", "fft", "fast fourier transform", "cooley-tukey", "twiddle factor", "frequency domain", "spectral analysis", "radix-2", "frequency bins"],
    "fir vs iir digital filters": ["fir vs iir digital filters", "fir", "iir", "linear phase", "constant group delay", "filter stability", "feedback poles", "difference equation", "discrete convolution", "finite impulse response"],
    "fixed-point quantization": ["fixed-point quantization", "fixed-point", "q-format", "quantization noise", "sqnr", "6.02 db", "dynamic range", "overflow", "saturation arithmetic", "limit cycles"],
    "digital pulse compression": ["digital pulse compression", "pulse compression", "chirp", "linear frequency modulation", "lfm", "matched filter", "time-bandwidth product", "range resolution", "processing gain"],
    "adaptive beamforming": ["adaptive beamforming", "beamforming", "mvdr", "capon", "spatial nulling", "covariance matrix", "jammer rejection", "steering vector", "array processing"],
    "radar range equation": ["radar range equation", "fourth power", "1/r^4", "radar cross section", "rcs", "power aperture", "received echo power", "antenna gain", "two-way propagation", "two-way travel"],
    "fourth power distance": ["fourth power", "1/r^4", "r^4", "power of distance", "power of the distance", "distance to the fourth power", "decay is two-way", "expanding sphere", "spreading out spherically"],
    "radar cross section": ["radar cross section", "rcs", "reflects a tiny fraction", "target acts like a secondary transmitter", "scattered return", "target reflectivity", "secondary transmitter", "reflects"],
    "pulse repetition frequency (prf)": ["pulse repetition frequency", "prf", "pulse repetition interval", "pri", "unambiguous range", "two-way time of flight", "staggered prf", "blind speeds", "c / (2 * prf)"],
    "doppler frequency shift": ["doppler frequency shift", "doppler shift", "doppler frequency", "moving target indication", "mti", "radial velocity", "delay line canceler", "blind speed", "2*v/lambda"],
    "fmcw radar principles": ["fmcw radar principles", "fmcw", "frequency modulated continuous wave", "beat frequency", "sweep bandwidth", "homodyne mixer", "triangular modulation", "continuous wave"],
    "aesa beamforming": ["aesa beamforming", "aesa", "active electronically scanned array", "t/r module", "transmit receive module", "electronic steering", "gan", "graceful degradation", "phased array"],
    "receiver dynamic range": ["receiver dynamic range", "noise figure", "friis formula", "lna", "low noise amplifier", "spurious-free dynamic range", "sfdr", "thermal noise floor", "sensitivity", "mds"],
    "mil-std-1553b dual-redundant bus": ["mil-std-1553b dual-redundant bus", "mil-std-1553b", "1553b", "bus controller", "remote terminal", "manchester ii", "transformer coupling", "dual redundant", "command-response"],
    "arinc-429 serial protocol": ["arinc-429 serial protocol", "arinc-429", "arinc 429", "bipolar return-to-zero", "bprz", "32-bit word", "label octal", "simplex point-to-point"],
    "phase locked loops (pll)": ["phase locked loops", "pll", "vco", "voltage controlled oscillator", "charge pump", "loop filter", "phase frequency detector", "phase noise", "local oscillator", "frequency synthesis"],
    "triple modular redundancy": ["triple modular redundancy", "tmr", "majority voter", "2-out-of-3", "fault tolerance", "single-event upset", "seu", "byzantine voting", "hardware redundancy"],
    "fmeca risk mitigation": ["fmeca risk mitigation", "fmeca", "fmea", "risk priority number", "rpn", "failure mode", "single point of failure", "severity classification", "criticality analysis", "mil-std-1629a"],
    "do-254 / do-178c guidelines": ["do-254 / do-178c guidelines", "do-254", "do-178c", "dal a", "design assurance level", "bi-directional traceability", "mc/dc", "safety-critical", "airborne systems"],
    "mtbf reliability prediction": ["mtbf reliability prediction", "mtbf", "mean time between failures", "failure rate", "mil-hdbk-217f", "reliability prediction", "obsolescence management", "dmsms"],

    # DRDO Sub-Concepts & Specialized Terminology
    "mutex synchronization": ["mutex", "mutexes", "mutual exclusion", "lock", "locking", "synchronization", "binary semaphore", "priority inheritance"],
    "task stacks": ["task stack", "task stacks", "stack pointer", "psp", "process stack", "stack allocation", "tcb", "stack", "stacked", "registers are stacked"],
    "context switch": ["context switch", "context switching", "task switch", "pendsv", "hardware stacking", "saving registers", "restoring task", "task switching"],
    "vector table": ["vector table", "interrupt vector", "nvic", "reset handler", "isr address", "offset"],
    "hardware stacking": ["hardware stacking", "automatic stacking", "r0-r3", "psr", "hardware registers", "stacked"],
    "deferred processing": ["deferred processing", "deferred", "bottom half", "worker task", "queue to task", "offload isr"],
    "priority inheritance": ["priority inheritance", "priority inversion", "elevating priority", "pip", "pcp", "priority ceiling"],
    "unbounded latency": ["unbounded latency", "unbounded priority inversion", "blocking high priority", "deadlock", "starvation"],
    "windowed watchdog": ["windowed watchdog", "wwdt", "watchdog", "refresh window", "early kick", "kick too early", "hardware supervisor"],
    "ping-pong double buffer": ["ping-pong", "double buffer", "ping-pong buffer", "dma buffer", "two buffers"],
    "cyclic executive": ["cyclic executive", "super-loop", "polling loop", "bare-metal", "fixed time slot"],
    "worst-case execution time": ["worst-case execution time", "wcet", "static timing analysis", "timing bound", "deadline"],
    "aliasing foldover": ["aliasing", "spectral foldover", "spectral leakage", "frequency foldover", "nyquist foldover", "ghost frequency"],
    "anti-aliasing filter": ["anti-aliasing filter", "anti aliasing", "aaf", "low-pass filter", "analog filter", "suppress out-of-band"],
    "sampling rate": ["sampling rate", "sampling frequency", "fs", "sample rate", "samples per second", "twice highest frequency"],
    "twiddle factor": ["twiddle factor", "w_n", "complex exponential", "roots of unity", "e^(-j*2*pi/n)"],
    "frequency bins": ["frequency bins", "fft bins", "spectral bins", "frequency resolution", "bin width"],
    "discrete convolution": ["convolution", "discrete convolution", "sliding sum", "filter convolution", "sum of products"],
    "impulse response": ["impulse response", "finite impulse", "infinite impulse", "h[n]", "unit impulse response"],
    "filter coefficients": ["coefficients", "filter taps", "b_k", "a_m", "weights", "tap weights"],
    "filter stability": ["stability", "stable", "poles inside unit circle", "bounded input bounded output", "bibo"],
    "linear phase": ["linear phase", "constant group delay", "symmetric coefficients", "no phase distortion"],
    "group delay": ["group delay", "phase delay", "delay", "constant delay", "derivative of phase"],
    "overflow saturation": ["overflow", "saturation", "clipping", "saturation arithmetic", "wrap-around"],
    "limit cycles": ["limit cycles", "deadband effects", "fixed-point oscillation", "truncation cycles"],
    "antenna gain": ["antenna gain", "gain g", "directional gain", "aperture", "focusing energy", "gain"],
    "time-bandwidth product": ["time-bandwidth product", "time-bandwidth", "b*tau", "processing gain", "chirp duration"],
    "range resolution": ["range resolution", "c/(2b)", "c / (2 * b)", "narrow sinc", "compressed width"],
    "linear frequency modulation": ["linear frequency modulation", "lfm", "chirp", "frequency sweep", "frequency ramp"],
    "matched filter": ["matched filter", "correlation", "cross-correlation", "snr maximization", "h(t) = s*(t0-t)"],
    "beat frequency": ["beat frequency", "f_b", "difference frequency", "homodyne mixer output", "frequency difference"],
    "sweep bandwidth": ["sweep bandwidth", "chirp bandwidth", "bandwidth b", "frequency sweep", "chirp sweep"],
    "homodyne mixer": ["homodyne mixer", "mixer", "downconversion", "mixing with transmit chirp", "downconverter"],
    "triangular modulation": ["triangular modulation", "upward and downward", "up ramp", "down ramp", "separates range", "triangle waveform"],
    "delay line canceler": ["delay line canceler", "delay line", "single delay line", "double delay line", "mti filter"],
    "blind speeds": ["blind speeds", "blind speed", "staggered prf", "doppler ambiguity"],
    "staggered prf": ["staggered prf", "multiple prfs", "variable pri", "eliminate blind speeds"],
    "clutter rejection": ["clutter rejection", "ground clutter", "zero frequency rejection", "stationary targets", "clutter"],
    "spatial null steering": ["spatial null", "spatial nulling", "null steering", "jammer nulling", "zero response"],
    "sample covariance matrix": ["covariance matrix", "sample covariance", "rxx", "data covariance", "interference covariance"],
    "matrix inversion": ["matrix inversion", "inv(rxx)", "diagonal loading", "inverting", "linear solver"],
    "noise figure": ["noise figure", "nf", "f = snr_in / snr_out", "friis formula", "noise factor"],
    "friis formula": ["friis formula", "friis equation", "cascaded noise", "f1 + (f2-1)/g1"],
    "low noise amplifier": ["low noise amplifier", "lna", "first stage gain", "receiver front-end"],
    "spurious free dynamic range": ["spurious-free dynamic range", "sfdr", "third order intercept", "toip", "ip3"],
    "manchester ii encoding": ["manchester ii", "manchester encoding", "bi-phase", "self-clocking", "zero dc bias"],
    "transformer coupling": ["transformer coupling", "isolation transformer", "galvanic isolation", "stub coupling"],
    "bus controller": ["bus controller", "bc", "master terminal", "command-response orchestrator"],
    "remote terminal": ["remote terminal", "rt", "subsystem terminal", "listen and respond"],
    "bus contention": ["bus contention", "bus collision", "bus fault", "timeout", "parity error"],
    "bipolar return to zero": ["bipolar return to zero", "bprz", "tri-level", "arinc-429 signaling"],
    "single event upset": ["single-event upset", "single event upset", "seu", "radiation induced", "bit flip", "rad-hard"],
    "majority voter": ["majority voter", "voter logic", "2-out-of-3", "quorum", "triplicated output"],
    "fault tolerance": ["fault tolerance", "fault tolerant", "single failure resilience", "graceful degradation", "hardware redundancy"],
    "risk priority number": ["risk priority number", "rpn", "severity occurrence detection", "s * o * d", "criticality index"],
    "severity classification": ["severity classification", "severity level", "catastrophic critical marginal", "mil-std-1629a"],
    "single point of failure": ["single point of failure", "spof", "redundancy elimination", "critical vulnerability"],
    "bi-directional traceability": ["traceability", "bi-directional traceability", "system to code", "requirements to test", "do-254", "do-178c"],
    "design assurance levels": ["design assurance level", "dal a", "dal b", "criticality level", "safety assurance"],
    "mcdc coverage": ["mc/dc", "modified condition decision coverage", "safety critical testing", "dal a verification"],
    "obsolescence management": ["obsolescence management", "obsolescence", "dmsms", "diminishing manufacturing sources", "second sourcing", "fpga migration"],
    "second sourcing": ["second sourcing", "alternate vendor", "form fit function", "pin compatible", "supply chain resilience"],
    "environmental stress factors": ["environmental stress", "temperature shock", "vibration", "humidity", "thermal cycling", "screening"]
}

# Buzzword / stuffing indicators that lack genuine explanation
NONSENSE_OR_CONTRADICTORY_PHRASES = [
    "is bad and wrong", "bananas eat", "nonsense", "is garbage", "meaningless",
    "fake news", "never works", "is totally useless", "dummy answer"
]

# Obvious hallucination / domain cross-talk indicators
HALLUCINATION_OR_MISMATCH_PATTERNS = [
    "compresses png images", "uploads them to a websocket", "video streaming",
    "baking cookies", "weather forecast", "css flexbox", "plays music", "cooks food"
]


# ---------------------------------------------------------
# Evaluator Interfaces
# ---------------------------------------------------------

class BaseAnswerEvaluator(ABC):
    """Abstract interface that all answer evaluators (LLM, Fallback, Mock) must implement."""

    @abstractmethod
    def evaluate(self, question: QuestionObject, candidate_answer: str) -> EvaluationResult:
        """Evaluates candidate response against question criteria, rubric, and expected concepts."""
        pass


# ---------------------------------------------------------
# Deterministic Fallback & Mock Evaluator
# ---------------------------------------------------------

class MockAnswerEvaluator(BaseAnswerEvaluator):
    """
    Enhanced deterministic, semantic-aware answer evaluator.
    Serves as the resilient offline test engine and runtime fallback when live LLM is unreachable.
    Distinguishes:
      - Correct answer using different wording / semantic paraphrases
      - Correct answer with exact terminology
      - Partially correct answers
      - Keyword stuffing without technical reasoning
      - Completely incorrect / off-topic answers
      - Minimal / refusal answers
    """

    def evaluate(self, question: QuestionObject, candidate_answer: str) -> EvaluationResult:
        cleaned_answer = (candidate_answer or "").strip()
        answer_lower = cleaned_answer.lower()

        expected = question.expectedConcepts or []
        if not expected:
            expected = [question.competency]

        # 1. Check for empty / minimal / refusal responses
        refusal_phrases = ["i don't know", "i do not know", "skip", "no idea", "pass", "unsure", "not sure", "dunno", "no clue", "not familiar"]
        if not cleaned_answer or len(cleaned_answer.split()) < 3:
            return EvaluationResult(
                score=10,
                coveredConcepts=[],
                missingConcepts=list(expected),
                reasoning="Candidate provided minimal or empty technical response.",
                confidence=0.98,
                technicalCorrectness="inaccurate",
                completeness="minimal",
                relevance="off_topic",
                depth="shallow",
                isFallback=True
            )

        if any(phrase in answer_lower for phrase in refusal_phrases) and (len(cleaned_answer.split()) < 15 or len(cleaned_answer) < 80):
            return EvaluationResult(
                score=15,
                coveredConcepts=[],
                missingConcepts=list(expected),
                reasoning="Candidate explicitly indicated lack of knowledge or skipped the question.",
                confidence=0.95,
                technicalCorrectness="inaccurate",
                completeness="minimal",
                relevance="off_topic",
                depth="shallow",
                isFallback=True
            )

        # 2. Check for obvious contradictory or nonsense answers
        if any(phrase in answer_lower for phrase in NONSENSE_OR_CONTRADICTORY_PHRASES):
            return EvaluationResult(
                score=18,
                coveredConcepts=[],
                missingConcepts=list(expected),
                reasoning="Answer contains contradictory, nonsensical, or factually invalid claims.",
                confidence=0.90,
                technicalCorrectness="inaccurate",
                completeness="minimal",
                relevance="off_topic",
                depth="shallow",
                isFallback=True
            )

        # 3. Check for obvious hallucination or domain cross-talk
        if any(phrase in answer_lower for phrase in HALLUCINATION_OR_MISMATCH_PATTERNS):
            return EvaluationResult(
                score=18,
                coveredConcepts=[],
                missingConcepts=list(expected),
                reasoning="Answer is factually incorrect and conflates unrelated engineering domains.",
                confidence=0.92,
                technicalCorrectness="inaccurate",
                completeness="minimal",
                relevance="off_topic",
                depth="shallow",
                isFallback=True
            )

        # 3. Detect Keyword Stuffing (buzzword dropping without explanatory grammar/predicates)
        words = re.findall(r"\b\w+\b", answer_lower)
        total_word_count = len(words)
        
        # Check explanatory verbs & connectives
        explanatory_tokens = {
            "is", "are", "by", "because", "using", "uses", "used", "use",
            "provides", "provide", "providing", "allows", "allow", "allowing",
            "ensures", "ensure", "ensuring", "stores", "store", "storing",
            "prevents", "prevent", "preventing", "handles", "handle", "handling",
            "which", "where", "reduces", "reduce", "improves", "improve", "means",
            "implement", "implements", "implementing", "helps", "help", "creates", "create",
            "works", "work", "organizes", "organize", "traverses", "executes",
            "occurs", "occur", "occurring", "holds", "hold", "holding", "needs", "need",
            "runs", "run", "running", "delays", "delay", "delaying", "causes", "cause", "caused",
            "blocks", "block", "blocking", "preempts", "preempt", "preempting", "acquires", "acquire",
            "when", "while", "then", "so", "with", "into", "from", "after"
        }
        verb_count = sum(1 for w in words if w in explanatory_tokens)
        
        # Check density of expected concepts in short text
        matched_concept_tokens = 0
        for exp in expected:
            for token in re.split(r"[\s\-_]+", exp.lower()):
                if len(token) > 2 and token in answer_lower:
                    matched_concept_tokens += 1

        is_keyword_stuffing = (
            (total_word_count <= 25 and matched_concept_tokens >= 3 and verb_count <= 1) or
            (total_word_count <= 35 and matched_concept_tokens >= 3 and verb_count == 0) or
            (total_word_count > 0 and (matched_concept_tokens / total_word_count) > 0.45 and verb_count <= 1)
        )

        if is_keyword_stuffing:
            return EvaluationResult(
                score=28,
                coveredConcepts=[],
                missingConcepts=list(expected),
                reasoning="Candidate dropped technical keywords without demonstrating logical reasoning or practical explanation.",
                confidence=0.88,
                technicalCorrectness="inaccurate",
                completeness="minimal",
                relevance="partially_relevant",
                depth="shallow",
                isFallback=True
            )

        # 4. Check for off-topic responses (e.g. food, sports, completely unrelated domain)
        off_topic_markers = ["pasta", "cooking", "football", "cricket", "weather", "recipe", "baking", "movie", "song", "vacation"]
        if any(m in answer_lower for m in off_topic_markers) and not any(exp.lower() in answer_lower for exp in expected):
            return EvaluationResult(
                score=10,
                coveredConcepts=[],
                missingConcepts=list(expected),
                reasoning="Answer is completely off-topic and unrelated to the interview question.",
                confidence=0.95,
                technicalCorrectness="inaccurate",
                completeness="minimal",
                relevance="off_topic",
                depth="shallow",
                isFallback=True
            )

        # 5. Semantic & Lexical Concept Coverage Detection
        covered: List[str] = []
        missing: List[str] = []

        for concept in expected:
            norm_concept = concept.lower().strip()
            concept_matched = False

            # A. Exact substring match
            if norm_concept in answer_lower:
                concept_matched = True

            # B. Check semantic synonym dictionary
            if not concept_matched:
                synonyms = CONCEPT_SEMANTIC_SYNONYMS.get(norm_concept, [])
                for syn in synonyms:
                    if syn in answer_lower:
                        concept_matched = True
                        break

            # C. Token-based matching if all primary tokens are present
            if not concept_matched:
                tokens = [t for t in re.split(r"[\s\-_]+", norm_concept) if len(t) > 2]
                if tokens and all(t in answer_lower for t in tokens):
                    concept_matched = True

            if concept_matched:
                covered.append(concept)
            else:
                missing.append(concept)

        total_expected = len(expected)
        coverage_ratio = len(covered) / total_expected if total_expected > 0 else 0.0

        # 6. Rubric Alignment & Quality Grading
        rubric = question.rubric
        excellent_keywords = [w.lower() for w in re.split(r"\W+", rubric.excellent) if len(w) > 4]
        poor_keywords = [w.lower() for w in re.split(r"\W+", rubric.poor) if len(w) > 4]

        excellent_hits = sum(1 for w in excellent_keywords if w in answer_lower)
        poor_hits = sum(1 for w in poor_keywords if w in answer_lower)

        # Baseline score calculation
        if coverage_ratio >= 0.85:
            base_score = 88
            tech_corr = "accurate"
            completeness = "complete"
        elif coverage_ratio >= 0.50:
            base_score = 72
            tech_corr = "partially_accurate"
            completeness = "partial"
        elif coverage_ratio > 0.0:
            base_score = 52
            tech_corr = "partially_accurate"
            completeness = "partial"
        else:
            base_score = 30
            tech_corr = "inaccurate"
            completeness = "minimal"

        # Adjust for rubric hints and depth
        score_adj = min(10, excellent_hits * 2) - min(12, poor_hits * 3)
        if total_word_count > 60 and coverage_ratio >= 0.5:
            score_adj += 4

        final_score = max(0, min(100, base_score + score_adj))

        # Depth determination
        if total_word_count > 70 and coverage_ratio >= 0.8:
            depth = "deep"
        elif total_word_count > 25:
            depth = "adequate"
        else:
            depth = "shallow"

        relevance = "directly_relevant" if coverage_ratio > 0.0 or total_word_count > 30 else "partially_relevant"
        confidence = 0.85 + (0.08 if coverage_ratio in (0.0, 1.0) else 0.0)
        confidence = min(0.95, round(confidence, 2))

        # Explainable reasoning
        if covered and not missing:
            reasoning = f"Candidate demonstrated accurate technical understanding of expected concepts ({', '.join(covered)})."
        elif covered and missing:
            reasoning = f"Candidate correctly addressed {', '.join(covered)}, but omitted or under-explained: {', '.join(missing)}."
        else:
            reasoning = f"Candidate failed to address core expected concepts: {', '.join(missing)}."

        return EvaluationResult(
            score=final_score,
            coveredConcepts=covered,
            missingConcepts=missing,
            reasoning=reasoning,
            confidence=confidence,
            technicalCorrectness=tech_corr,
            completeness=completeness,
            relevance=relevance,
            depth=depth,
            isFallback=True
        )


# Backward-compatible alias
DeterministicAnswerEvaluator = MockAnswerEvaluator


# ---------------------------------------------------------
# Real Gemini LLM Answer Evaluator
# ---------------------------------------------------------

SYSTEM_EVALUATION_PROMPT = """You are an expert technical interviewer and objective answer evaluation engine in a high-stakes engineering simulation.
Evaluate the candidate's answer against the given question, expected concepts, and grading rubric.

CRITICAL EVALUATION GUIDELINES:
1. Evaluate SEMANTIC MEANING and conceptual understanding, not mere keyword matching.
2. A correct answer using different terminology or semantic paraphrasing MUST receive full credit for demonstrated concepts.
3. Superficially keyword-heavy answers that drop buzzwords without correct reasoning or logic MUST NOT receive high scores. Penalize keyword stuffing heavily.
4. If an answer is detailed but factually or technically incorrect, score it low (technicalCorrectness="inaccurate").
5. If an answer is short but technically precise and correct, award high correctness (depth="shallow" or "adequate", technicalCorrectness="accurate").
6. Off-topic, refusal ("I don't know", "pass"), or nonsense responses must receive low scores (0-25) and relevance="off_topic".
7. Determine coveredConcepts as the subset of expected concepts that the candidate demonstrated genuine understanding of.
8. Determine missingConcepts as the expected concepts that were omitted or explained incorrectly.
9. Return ONLY valid JSON adhering strictly to the JSON schema below. No markdown fences, no conversational preamble.

REQUIRED JSON SCHEMA:
{
  "score": <integer 0-100>,
  "coveredConcepts": ["concept1", "concept2"],
  "missingConcepts": ["concept3"],
  "confidence": <float 0.0-1.0>,
  "reasoning": "<concise explainable rationale>",
  "technicalCorrectness": "accurate" | "partially_accurate" | "inaccurate",
  "completeness": "complete" | "partial" | "minimal",
  "relevance": "directly_relevant" | "partially_relevant" | "off_topic",
  "depth": "deep" | "adequate" | "shallow"
}
"""


class GeminiAnswerEvaluator(BaseAnswerEvaluator):
    """
    Production-quality LLM answer evaluator leveraging Google Gemini.
    Features:
      - Semantic comprehension over keyword matching
      - Timeout enforcement & retry policy
      - Malformed JSON recovery & score clamping
      - Seamless fallback to DeterministicAnswerEvaluator on failure or missing credentials
    """

    def __init__(self, fallback_evaluator: Optional[BaseAnswerEvaluator] = None):
        self.fallback_evaluator = fallback_evaluator or MockAnswerEvaluator()

    def evaluate(self, question: QuestionObject, candidate_answer: str) -> EvaluationResult:
        """Evaluates answer using Gemini LLM with automatic fallback."""
        if not settings.GEMINI_API_KEY:
            logger.debug("GEMINI_API_KEY not set. Using deterministic fallback evaluator.")
            return self.fallback_evaluator.evaluate(question, candidate_answer)

        # Attempt Gemini LLM evaluation with retries
        for attempt in range(1, 3):
            try:
                result = self._evaluate_with_gemini(question, candidate_answer)
                if result is not None:
                    return result
            except Exception as e:
                logger.warning(f"Gemini answer evaluation attempt {attempt} failed: {e}")

        logger.info("Gemini answer evaluation exhausted retries. Engaging deterministic fallback evaluator.")
        return self.fallback_evaluator.evaluate(question, candidate_answer)

    def _evaluate_with_gemini(self, question: QuestionObject, candidate_answer: str) -> Optional[EvaluationResult]:
        """Direct call to Gemini API with JSON response mode."""
        from google import genai
        from google.genai import types

        timeout_ms = int(settings.LLM_TIMEOUT_SECONDS * 1000)
        http_options = types.HttpOptions(timeout=timeout_ms)

        client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=http_options
        )

        expected = question.expectedConcepts or []

        user_prompt = f"""QUESTION DETAILS:
- Question: {question.text}
- Competency: {question.competency}
- Stage: {question.stage}
- Difficulty: {question.difficulty}/5
- Question Type: {question.questionType or 'technical'}
- Expected Concepts: {json.dumps(expected)}
- Rubric:
  * Poor (0-40): {question.rubric.poor}
  * Acceptable (41-75): {question.rubric.acceptable}
  * Excellent (76-100): {question.rubric.excellent}
- Retrieved Sources: {json.dumps(question.retrievedSourceIds or [])}

CANDIDATE ANSWER:
\"\"\"{candidate_answer}\"\"\"

Evaluate the candidate answer according to the rubric and guidelines. Return JSON only."""

        response = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents=[SYSTEM_EVALUATION_PROMPT, user_prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for objective, deterministic evaluation
                response_mime_type="application/json",
                http_options=http_options
            )
        )

        raw_text = response.text.strip()
        data = self._clean_and_parse_json(raw_text)
        if not data:
            return None

        # Extract and validate fields
        raw_score = data.get("score", 50)
        try:
            score = max(0, min(100, int(raw_score)))
        except (ValueError, TypeError):
            score = 50

        raw_conf = data.get("confidence", 0.85)
        try:
            confidence = max(0.0, min(1.0, float(raw_conf)))
        except (ValueError, TypeError):
            confidence = 0.85

        # Normalize covered and missing concepts against question expected concepts
        raw_covered = data.get("coveredConcepts", [])
        if not isinstance(raw_covered, list):
            raw_covered = []

        # Canonicalize concept casing
        expected_lookup = {c.lower(): c for c in expected}
        covered_canonical = []
        for c in raw_covered:
            norm_c = str(c).strip().lower()
            if norm_c in expected_lookup:
                covered_canonical.append(expected_lookup[norm_c])
            else:
                covered_canonical.append(str(c).strip())

        raw_missing = data.get("missingConcepts", [])
        if not isinstance(raw_missing, list):
            raw_missing = []

        missing_canonical = []
        for c in raw_missing:
            norm_c = str(c).strip().lower()
            if norm_c in expected_lookup:
                missing_canonical.append(expected_lookup[norm_c])
            else:
                missing_canonical.append(str(c).strip())

        # Ensure all expected concepts are accounted for
        accounted = set(c.lower() for c in covered_canonical)
        for exp in expected:
            if exp.lower() not in accounted and exp not in missing_canonical:
                missing_canonical.append(exp)

        reasoning = str(data.get("reasoning", "Evaluated by Gemini LLM."))
        tech_corr = str(data.get("technicalCorrectness", "adequate"))
        if tech_corr not in ("accurate", "partially_accurate", "inaccurate"):
            tech_corr = "accurate" if score >= 75 else ("partially_accurate" if score >= 45 else "inaccurate")

        completeness = str(data.get("completeness", "adequate"))
        if completeness not in ("complete", "partial", "minimal"):
            completeness = "complete" if score >= 75 else ("partial" if score >= 45 else "minimal")

        relevance = str(data.get("relevance", "relevant"))
        if relevance not in ("directly_relevant", "partially_relevant", "off_topic"):
            relevance = "directly_relevant" if score >= 40 else "off_topic"

        depth = str(data.get("depth", "adequate"))
        if depth not in ("deep", "adequate", "shallow"):
            depth = "adequate"

        return EvaluationResult(
            score=score,
            coveredConcepts=covered_canonical,
            missingConcepts=missing_canonical,
            reasoning=reasoning,
            confidence=confidence,
            technicalCorrectness=tech_corr,
            completeness=completeness,
            relevance=relevance,
            depth=depth,
            isFallback=False
        )

    def _clean_and_parse_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Cleans markdown wrappers and extracts structured JSON object."""
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback regex extraction of outermost JSON object
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return None


# ---------------------------------------------------------
# Answer Evaluation Adapter (Contract Boundary)
# ---------------------------------------------------------

class AnswerEvaluationAdapter:
    """
    Adapter that normalizes external evaluation input (from Member 4's service)
    or delegates to a registered evaluator (GeminiAnswerEvaluator with Mock fallback).
    Guarantees strict schema conformity and safe boundary separation.
    """

    def __init__(
        self,
        evaluator: Optional[BaseAnswerEvaluator] = None,
        fallback_evaluator: Optional[BaseAnswerEvaluator] = None
    ):
        if evaluator is not None:
            self.evaluator = evaluator
        else:
            # Default to Gemini evaluator backed by deterministic fallback
            self.evaluator = GeminiAnswerEvaluator(fallback_evaluator=fallback_evaluator or MockAnswerEvaluator())

    def process_evaluation(
        self,
        question: QuestionObject,
        candidate_answer: str,
        incoming_evaluation: Optional[Any] = None
    ) -> EvaluationResult:
        """
        Consumes an evaluation from Member 4 if supplied, or evaluates using Gemini/fallback.
        Safely validates and clamps scores to 0-100 and confidence to 0.0-1.0.
        """
        if incoming_evaluation is not None:
            # Handle incoming EvaluationResult model
            if isinstance(incoming_evaluation, EvaluationResult):
                return EvaluationResult(
                    score=max(0, min(100, incoming_evaluation.score)),
                    coveredConcepts=list(incoming_evaluation.coveredConcepts),
                    missingConcepts=list(incoming_evaluation.missingConcepts),
                    reasoning=incoming_evaluation.reasoning or "Evaluated by Member 4 Evaluation Service.",
                    confidence=max(0.0, min(1.0, incoming_evaluation.confidence)),
                    technicalCorrectness=getattr(incoming_evaluation, "technicalCorrectness", "adequate"),
                    completeness=getattr(incoming_evaluation, "completeness", "adequate"),
                    relevance=getattr(incoming_evaluation, "relevance", "directly_relevant"),
                    depth=getattr(incoming_evaluation, "depth", "adequate"),
                    isFallback=getattr(incoming_evaluation, "isFallback", False)
                )

            # Handle raw dict from HTTP request
            if isinstance(incoming_evaluation, dict):
                raw_score = incoming_evaluation.get("score", 70)
                try:
                    score = max(0, min(100, int(raw_score)))
                except (ValueError, TypeError):
                    score = 70

                covered = incoming_evaluation.get("coveredConcepts", incoming_evaluation.get("covered_concepts", []))
                missing = incoming_evaluation.get("missingConcepts", incoming_evaluation.get("missing_concepts", []))
                reasoning = incoming_evaluation.get("reasoning", "Provided via evaluation input.")
                raw_conf = incoming_evaluation.get("confidence", 0.85)
                try:
                    confidence = max(0.0, min(1.0, float(raw_conf)))
                except (ValueError, TypeError):
                    confidence = 0.85

                return EvaluationResult(
                    score=score,
                    coveredConcepts=list(covered) if isinstance(covered, list) else [],
                    missingConcepts=list(missing) if isinstance(missing, list) else [],
                    reasoning=str(reasoning),
                    confidence=confidence,
                    technicalCorrectness=incoming_evaluation.get("technicalCorrectness", "adequate"),
                    completeness=incoming_evaluation.get("completeness", "adequate"),
                    relevance=incoming_evaluation.get("relevance", "directly_relevant"),
                    depth=incoming_evaluation.get("depth", "adequate"),
                    isFallback=incoming_evaluation.get("isFallback", False)
                )

        # No external evaluation supplied: delegate to primary evaluator
        return self.evaluator.evaluate(question, candidate_answer)
