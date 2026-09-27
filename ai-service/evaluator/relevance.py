"""
Question Relevance Evaluator for BoardRoom AI.
Implements the explainable 5-factor scoring formula defined in Hackathon Master Plan Section 7.1:
  Question Relevance (0–100) =
    30% Role Alignment
  + 25% Candidate Expertise Alignment
  + 20% Target Competency Alignment
  + 15% Difficulty Appropriateness
  + 10% Specificity / Clarity
"""

import re
from typing import List, Optional, Tuple, Dict

from core.schemas import (
    CandidateProfile,
    TargetRole,
    QuestionRelevanceBreakdown
)


from core.concepts import (
    COMPETENCY_CORE_CONCEPTS,
    build_unified_competency_keyword_map,
    get_canonical_concepts_for_competency,
    get_all_canonical_concepts
)

# Canonical unified competency keyword map derived directly from core.concepts
COMPETENCY_KEYWORD_MAP = build_unified_competency_keyword_map()




class QuestionRelevanceEvaluator:
    """
    Evaluates generated interview questions using explainable, auditable rules
    and semantic concept alignment.
    """

    @classmethod
    def evaluate(
        cls,
        question_text: str,
        role: TargetRole,
        candidate: CandidateProfile,
        competency: str,
        stage: str,
        difficulty: int,
        expected_concepts: Optional[List[str]] = None
    ) -> QuestionRelevanceBreakdown:
        q_lower = question_text.lower()

        # 1. Role Alignment (Weight: 30%)
        role_score, role_reason = cls._score_role_alignment(q_lower, role)

        # 2. Candidate Expertise Alignment (Weight: 25%)
        candidate_score, cand_reason = cls._score_candidate_alignment(q_lower, candidate, difficulty)

        # 3. Target Competency Alignment (Weight: 20%)
        competency_score, comp_reason = cls._score_competency_alignment(q_lower, competency, expected_concepts)

        # 4. Difficulty Appropriateness (Weight: 15%)
        diff_score, diff_reason = cls._score_difficulty_appropriateness(stage, difficulty, question_text)

        # 5. Specificity & Clarity (Weight: 10%)
        clarity_score, clarity_reason = cls._score_clarity(question_text)

        # Weighted calculation
        total = round(
            (0.30 * role_score) +
            (0.25 * candidate_score) +
            (0.20 * competency_score) +
            (0.15 * diff_score) +
            (0.10 * clarity_score)
        )
        total = max(0, min(100, total))

        rationale = (
            f"Question relevance scored at {total}/100. "
            f"[Role: {role_score} ({role_reason})] "
            f"[Candidate: {candidate_score} ({cand_reason})] "
            f"[Competency: {competency_score} ({comp_reason})] "
            f"[Difficulty/Stage: {diff_score} ({diff_reason})] "
            f"[Clarity: {clarity_score} ({clarity_reason})]"
        )

        return QuestionRelevanceBreakdown(
            roleAlignment=role_score,
            candidateExpertiseAlignment=candidate_score,
            targetCompetencyAlignment=competency_score,
            difficultyAppropriateness=diff_score,
            specificityClarity=clarity_score,
            totalScore=total,
            rationale=rationale
        )

    # General software, systems, and DRDO scientific/engineering domain markers
    GENERAL_ENGINEERING_MARKERS = {
        "software", "engineer", "code", "programming", "system", "architecture",
        "database", "api", "backend", "frontend", "server", "service", "client",
        "performance", "latency", "scalability", "bug", "deploy", "design", "data",
        "algorithm", "queue", "cache", "network", "test", "security", "git", "cloud",
        "distributed", "lock", "concurrency", "async", "transaction", "redis", "sql",
        "nosql", "http", "rest", "endpoint", "microservice", "pipeline", "schema",
        "query", "index", "b-tree", "throughput", "memory", "thread", "process",
        "socket", "payload", "header", "auth", "token", "jwt", "idempotency",
        "migration", "incident", "triage", "outage", "replica", "sharding", "raft",
        # DRDO / ECE / Radar / Embedded / Avionics engineering markers
        "embedded", "rtos", "interrupt", "isr", "timer", "dma", "dsp", "sampling",
        "nyquist", "fourier", "fft", "filter", "fir", "iir", "radar", "prf", "pri",
        "doppler", "antenna", "rf", "aesa", "avionics", "mil-std-1553", "1553b",
        "arinc", "arinc-429", "bus", "fpga", "microcontroller", "adc", "dac",
        "modulation", "bpsk", "qpsk", "fmeca", "reliability", "mtbf", "telemetry",
        "sensor", "firmware", "vhdl", "verilog", "oscilloscope", "logic analyzer",
        "cortex", "arm", "bare-metal", "preemption", "priority inversion", "watchdog",
        "clutter", "beamforming", "chirp", "pulse compression", "cfar", "do-254", "do-178c"
    }

    @classmethod
    def _score_role_alignment(cls, q_lower: str, role: TargetRole) -> Tuple[int, str]:
        """Checks alignment with role skills, technical requirements, and engineering domain."""
        target_tokens = set([s.lower() for s in role.required_skills])
        target_tokens.update(["backend", "api", "server", "data", "architecture", "system", "service", "code"])
        if role.description:
            desc_words = [w.lower().strip(".,;:()") for w in role.description.split() if len(w) > 4]
            target_tokens.update(desc_words)
        if getattr(role, "technical_requirements", None):
            for req in role.technical_requirements:
                req_words = [w.lower().strip(".,;:()") for w in req.split() if len(w) > 4]
                target_tokens.update(req_words)
        if getattr(role, "title", None):
            title_words = [w.lower().strip(".,;:()") for w in role.title.split() if len(w) > 3]
            target_tokens.update(title_words)

        matches = [kw for kw in target_tokens if kw in q_lower]
        eng_matches = [marker for marker in cls.GENERAL_ENGINEERING_MARKERS if marker in q_lower]

        if len(matches) >= 2 or (len(matches) >= 1 and len(eng_matches) >= 2):
            matched_terms = list(set(matches + eng_matches))[:3]
            return 95, f"Matches key role requirements ({', '.join(matched_terms)})"
        elif len(matches) == 1:
            return 85, f"Mentions core skill ({matches[0]})"
        elif len(eng_matches) >= 2:
            return 80, f"Strong technical systems alignment ({', '.join(eng_matches[:2])})"
        elif len(eng_matches) == 1:
            return 70, f"Relevant general engineering question ({eng_matches[0]})"
        else:
            return 15, "Non-technical or completely unrelated to target role"

    @classmethod
    def _score_candidate_alignment(cls, q_lower: str, candidate: CandidateProfile, difficulty: int) -> Tuple[int, str]:
        """Checks alignment between question, candidate skills, claimed expertise, and experience."""
        cand_skills = [s.lower() for s in candidate.skills]
        if getattr(candidate, "claimed_expertise", None):
            for claim in candidate.claimed_expertise:
                cand_skills.append(claim.lower())
                cand_skills.extend([w.lower().strip(".,;:()") for w in claim.split() if len(w) > 4])
        if getattr(candidate, "specialization", None) and candidate.specialization:
            cand_skills.extend([w.lower().strip(".,;:()") for w in candidate.specialization.split() if len(w) > 4])
        matched_skills = [s for s in cand_skills if s in q_lower]
        has_eng_marker = any(marker in q_lower for marker in cls.GENERAL_ENGINEERING_MARKERS)

        # Non-technical question penalty
        if not has_eng_marker and not matched_skills:
            return 10, "Question is non-technical and does not evaluate candidate profile"

        # Experience vs Difficulty calibration
        exp = candidate.experience_years or 1.0
        exp_appropriate = True
        if exp < 1.5 and difficulty >= 4:
            exp_appropriate = False
        elif exp >= 5.0 and difficulty <= 1:
            exp_appropriate = False

        if matched_skills and exp_appropriate:
            return 95, f"Directly probes candidate skill ({', '.join(matched_skills[:2])}) at calibrated difficulty"
        elif matched_skills and not exp_appropriate:
            return 75, f"Targets candidate skill ({matched_skills[0]}) but difficulty differs from candidate seniority"
        elif not matched_skills and exp_appropriate:
            return 80, "Appropriate depth for candidate seniority within role scope"
        else:
            return 45, "Generic question with minimal personalization for candidate background"

    @classmethod
    def _score_competency_alignment(
        cls,
        q_lower: str,
        competency: str,
        expected_concepts: Optional[List[str]] = None
    ) -> Tuple[int, str]:
        """Checks alignment with target competency and expected concepts."""
        comp_norm = competency.lower().replace("-", "_").replace(" ", "_")
        keywords = COMPETENCY_KEYWORD_MAP.get(comp_norm, [])

        matched_kw = [
            k for k in keywords
            if re.search(r'(?:\b|_)' + re.escape(k) + r'(?:\b|_)', q_lower)
        ]

        # Also check expected concepts if provided
        concept_matches = 0
        if expected_concepts:
            for c in expected_concepts:
                words = c.lower().split()
                if any(re.search(r'\b' + re.escape(w) + r'\b', q_lower) for w in words if len(w) > 3):
                    concept_matches += 1

        if matched_kw and concept_matches > 0:
            return 98, f"Strong grounding in {competency} ({', '.join(matched_kw[:2])})"
        elif matched_kw:
            return 90, f"Strong competency match for {competency} ({matched_kw[0]})"
        elif concept_matches > 0:
            return 82, f"Covers target concepts in {competency}"
        else:
            has_eng = any(marker in q_lower for marker in cls.GENERAL_ENGINEERING_MARKERS)
            if not has_eng:
                return 10, f"Completely off-topic question with no relevance to {competency}"
            return 40, f"Question does not clearly address core technical elements of {competency}"


    @classmethod
    def _score_difficulty_appropriateness(cls, stage: str, difficulty: int, q_text: str) -> Tuple[int, str]:
        """Validates that requested difficulty and stage progression align."""
        stage_expected_diffs = {
            "ice_breaker": [1, 2],
            "applicant_validation": [1, 2, 3],
            "core_technical": [2, 3, 4],
            "deep_dive": [3, 4, 5],
            "application_scenario": [3, 4, 5],
            "system_engineering": [3, 4, 5],
            "techno_managerial": [3, 4, 5],
            "fundamentals": [1, 2, 3],
            "role_technical": [2, 3, 4],
            "scenario_managerial": [3, 4, 5]
        }
        allowed = stage_expected_diffs.get(stage, [1, 2, 3, 4, 5])

        if difficulty in allowed:
            return 95, f"Difficulty {difficulty}/5 matches {stage} stage"
        else:
            # Distance penalty
            min_dist = min([abs(difficulty - a) for a in allowed])
            score = max(30, 90 - (min_dist * 25))
            return score, f"Difficulty {difficulty} deviates from expected stage norm ({allowed})"

    @classmethod
    def _score_clarity(cls, q_text: str) -> Tuple[int, str]:
        """Checks question length, punctuation, and structural clarity."""
        words = q_text.strip().split()
        word_count = len(words)

        if word_count < 6:
            return 40, "Question is too brief to be meaningful"
        if word_count > 80:
            return 60, "Question is overly verbose"
        if not q_text.strip().endswith("?"):
            return 70, "Missing trailing question mark"

        # Check for multi-headed questions
        question_marks = q_text.count("?")
        if question_marks > 2:
            return 75, "Multiple compound questions in a single prompt"

        return 95, "Clear, concise, and focused single question"
