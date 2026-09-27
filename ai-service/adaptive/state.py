"""
Interview State Model & Concept Coverage Tracking for BoardRoom AI (Phase B v2).
Tracks session progression, concept demonstrations, weak/strong areas,
question types, rolling score trends, consecutive streaks, persistent weaknesses,
and multi-tier mastery confidence.
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class ConceptMasteryLevel(str, Enum):
    UNTESTED = "untested"
    DEMONSTRATED_ONCE = "demonstrated_once"
    CONSISTENTLY_DEMONSTRATED = "consistently_demonstrated"
    PARTIALLY_DEMONSTRATED = "partially_demonstrated"
    REPEATEDLY_MISSING = "repeatedly_missing"
    RECOVERED = "recovered"


class ConceptCoverage(BaseModel):
    concept: str
    status: str = Field(..., description="'demonstrated' | 'partially_demonstrated' | 'missing'")
    mastery_level: ConceptMasteryLevel = ConceptMasteryLevel.UNTESTED
    demonstration_count: int = 0
    missing_count: int = 0
    question_id: Optional[str] = None
    competency: Optional[str] = None
    stage: Optional[str] = None


class InterviewState(BaseModel):
    """
    Comprehensive state tracking model across an active candidate interview session.
    Maintains historical trajectory, rolling trends, streaks, and concept mastery.
    """
    candidate_id: str = "cand_default"
    role_id: str = "backend_engineer"
    current_stage: str = "ice_breaker"
    current_competency: str = "ice_breaker"
    difficulty: int = Field(default=1, ge=1, le=5)

    # Concept-Level Coverage Tracking (Demonstrated vs Partial vs Missing)
    demonstrated_concepts: List[str] = Field(default_factory=list)
    partially_demonstrated_concepts: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    concept_map: Dict[str, str] = Field(default_factory=dict, description="concept_name -> status")

    # Aggregated Strengths & Weaknesses
    weak_concepts: List[str] = Field(default_factory=list)
    strong_concepts: List[str] = Field(default_factory=list)

    # Question & Trajectory History
    previous_questions: List[str] = Field(default_factory=list)
    question_ids: List[str] = Field(default_factory=list)
    question_types: List[str] = Field(default_factory=list)
    score_history: List[int] = Field(default_factory=list)
    difficulty_trend: List[int] = Field(default_factory=list)

    # Fallback deduplication tracking
    used_fallback_ids: List[str] = Field(default_factory=list)

    # Stage & Competency Counters
    stage_question_counts: Dict[str, int] = Field(default_factory=lambda: {
        "ice_breaker": 0,
        "applicant_validation": 0,
        "core_technical": 0,
        "deep_dive": 0,
        "application_scenario": 0,
        "system_engineering": 0,
        "techno_managerial": 0
    })
    competency_scores: Dict[str, List[int]] = Field(default_factory=dict)

    # Phase B: Performance Trend Tracking
    rolling_score_trend: str = Field(default="neutral", description="improving | declining | stable | neutral")
    consecutive_strong_count: int = Field(default=0, description="Consecutive scores >= 80")
    consecutive_weak_count: int = Field(default=0, description="Consecutive scores < 55")
    persistent_weaknesses: List[str] = Field(default_factory=list, description="Concepts missing/weak across >= 2 turns")

    # Phase B: Mastery Confidence Tracking
    consistently_demonstrated_concepts: List[str] = Field(default_factory=list, description="Demonstrated >= 2 times")
    demonstrated_once_concepts: List[str] = Field(default_factory=list, description="Demonstrated exactly once")
    repeatedly_missing_concepts: List[str] = Field(default_factory=list, description="Missing >= 2 times")
    recovered_concepts: List[str] = Field(default_factory=list, description="Previously missing, subsequently demonstrated")
    mastery_levels: Dict[str, str] = Field(default_factory=dict, description="concept -> mastery level")
    concept_demonstration_counts: Dict[str, int] = Field(default_factory=dict)
    concept_missing_counts: Dict[str, int] = Field(default_factory=dict)
    concept_partial_counts: Dict[str, int] = Field(default_factory=dict)
    turns: List[Dict[str, Any]] = Field(default_factory=list, description="Historical turn logs")
    prerequisite_issues: List[str] = Field(default_factory=list, description="Detected prerequisite gaps")


    def _compute_score_trend(self) -> str:
        """Computes rolling performance trend across recent 2-3 scores."""
        if len(self.score_history) < 2:
            return "neutral"
        if len(self.score_history) == 2:
            delta = self.score_history[-1] - self.score_history[-2]
        else:
            delta = (self.score_history[-1] - self.score_history[-2]) * 0.7 + (self.score_history[-2] - self.score_history[-3]) * 0.3

        if delta >= 6:
            return "improving"
        elif delta <= -6:
            return "declining"
        else:
            return "stable"

    def record_turn(
        self,
        question_id: str,
        question_text: str,
        question_type: str,
        stage: str,
        competency: str,
        difficulty: int,
        score: Optional[int] = None,
        covered_concepts: Optional[List[str]] = None,
        missing_concepts: Optional[List[str]] = None
    ):
        """
        Updates session state upon completing an interview turn / evaluation.
        Distinguishes demonstrated, partially demonstrated, and missing knowledge,
        updates rolling score trends, streaks, and mastery confidence.
        """
        self.previous_questions.append(question_text)
        self.question_ids.append(question_id)
        self.question_types.append(question_type)
        self.difficulty_trend.append(difficulty)
        self.current_stage = stage
        self.current_competency = competency
        self.difficulty = difficulty

        if stage in self.stage_question_counts:
            self.stage_question_counts[stage] += 1
        else:
            self.stage_question_counts[stage] = 1

        if score is not None:
            self.score_history.append(score)
            if competency not in self.competency_scores:
                self.competency_scores[competency] = []
            self.competency_scores[competency].append(score)

            # Update consecutive strong / weak streaks
            if score >= 80:
                self.consecutive_strong_count += 1
                self.consecutive_weak_count = 0
            elif score < 55:
                self.consecutive_weak_count += 1
                self.consecutive_strong_count = 0
            else:
                self.consecutive_strong_count = 0
                self.consecutive_weak_count = 0

            # Update rolling trend
            self.rolling_score_trend = self._compute_score_trend()

        # Concept-Level Coverage & Mastery Tracking
        covered = covered_concepts or []
        missing = missing_concepts or []

        for c in covered:
            if score is None or score >= 75:
                self.concept_map[c] = "demonstrated"
                self.concept_demonstration_counts[c] = self.concept_demonstration_counts.get(c, 0) + 1

                # Check for recovery: was it previously missing?
                if c in self.missing_concepts or self.concept_missing_counts.get(c, 0) > 0:
                    if c not in self.recovered_concepts:
                        self.recovered_concepts.append(c)
                    if c in self.persistent_weaknesses:
                        self.persistent_weaknesses.remove(c)
                    if c in self.repeatedly_missing_concepts:
                        self.repeatedly_missing_concepts.remove(c)

                # Update mastery level
                if self.concept_demonstration_counts[c] >= 2:
                    self.mastery_levels[c] = ConceptMasteryLevel.CONSISTENTLY_DEMONSTRATED.value
                    if c not in self.consistently_demonstrated_concepts:
                        self.consistently_demonstrated_concepts.append(c)
                    if c in self.demonstrated_once_concepts:
                        self.demonstrated_once_concepts.remove(c)
                else:
                    self.mastery_levels[c] = ConceptMasteryLevel.DEMONSTRATED_ONCE.value
                    if c not in self.demonstrated_once_concepts:
                        self.demonstrated_once_concepts.append(c)

                if c not in self.demonstrated_concepts:
                    self.demonstrated_concepts.append(c)
                if c not in self.strong_concepts:
                    self.strong_concepts.append(c)
                if c in self.missing_concepts:
                    self.missing_concepts.remove(c)
                if c in self.partially_demonstrated_concepts:
                    self.partially_demonstrated_concepts.remove(c)

            elif score >= 50:
                self.concept_map[c] = "partially_demonstrated"
                self.concept_partial_counts[c] = self.concept_partial_counts.get(c, 0) + 1

                if c not in self.consistently_demonstrated_concepts and c not in self.demonstrated_once_concepts:
                    self.mastery_levels[c] = ConceptMasteryLevel.PARTIALLY_DEMONSTRATED.value

                if c not in self.partially_demonstrated_concepts:
                    self.partially_demonstrated_concepts.append(c)
            else:
                self.concept_map[c] = "missing"
                self.concept_missing_counts[c] = self.concept_missing_counts.get(c, 0) + 1
                if self.concept_missing_counts[c] >= 2:
                    self.mastery_levels[c] = ConceptMasteryLevel.REPEATEDLY_MISSING.value
                    if c not in self.repeatedly_missing_concepts:
                        self.repeatedly_missing_concepts.append(c)
                    if c not in self.persistent_weaknesses:
                        self.persistent_weaknesses.append(c)

                if c not in self.missing_concepts:
                    self.missing_concepts.append(c)
                if c not in self.weak_concepts:
                    self.weak_concepts.append(c)

        for m in missing:
            self.concept_map[m] = "missing"
            self.concept_missing_counts[m] = self.concept_missing_counts.get(m, 0) + 1

            if self.concept_missing_counts[m] >= 2:
                self.mastery_levels[m] = ConceptMasteryLevel.REPEATEDLY_MISSING.value
                if m not in self.repeatedly_missing_concepts:
                    self.repeatedly_missing_concepts.append(m)
                if m not in self.persistent_weaknesses:
                    self.persistent_weaknesses.append(m)
            else:
                if m not in self.mastery_levels or self.mastery_levels[m] == ConceptMasteryLevel.UNTESTED.value:
                    self.mastery_levels[m] = ConceptMasteryLevel.PARTIALLY_DEMONSTRATED.value

            if m not in self.missing_concepts:
                self.missing_concepts.append(m)
            if m not in self.weak_concepts:
                self.weak_concepts.append(m)
            if m in self.strong_concepts:
                self.strong_concepts.remove(m)
            if m in self.demonstrated_concepts:
                self.demonstrated_concepts.remove(m)
            if m in self.consistently_demonstrated_concepts:
                self.consistently_demonstrated_concepts.remove(m)
            if m in self.demonstrated_once_concepts:
                self.demonstrated_once_concepts.remove(m)

        self.turns.append({
            "turn": len(self.previous_questions),
            "question_id": question_id,
            "question_text": question_text,
            "question_type": question_type,
            "stage": stage,
            "competency": competency,
            "difficulty": difficulty,
            "score": score,
            "covered_concepts": list(covered),
            "missing_concepts": list(missing)
        })

        # Enforce invariant consistency across all concept structures
        self.validate_and_synchronize_invariants()

    def validate_and_synchronize_invariants(self) -> None:
        """
        Enforces and validates core state invariants across overlapping concept structures:
        1. No concept can be simultaneously in demonstrated_concepts and missing_concepts.
        2. demonstrated_once_concepts and consistently_demonstrated_concepts are strictly disjoint.
        3. All demonstrated sub-tiers are subsets of demonstrated_concepts.
        4. Mastery levels accurately match demonstration / missing counts and recovery status.
        5. Recovered concepts are purged from persistent weaknesses.
        6. strong_concepts and weak_concepts do not overlap.
        7. concept_map accurately reflects canonical status.
        """
        # Deduplicate all lists while preserving order
        self.demonstrated_concepts = list(dict.fromkeys(self.demonstrated_concepts))
        self.partially_demonstrated_concepts = list(dict.fromkeys(self.partially_demonstrated_concepts))
        self.missing_concepts = list(dict.fromkeys(self.missing_concepts))
        self.strong_concepts = list(dict.fromkeys(self.strong_concepts))
        self.weak_concepts = list(dict.fromkeys(self.weak_concepts))
        self.consistently_demonstrated_concepts = list(dict.fromkeys(self.consistently_demonstrated_concepts))
        self.demonstrated_once_concepts = list(dict.fromkeys(self.demonstrated_once_concepts))
        self.repeatedly_missing_concepts = list(dict.fromkeys(self.repeatedly_missing_concepts))
        self.recovered_concepts = list(dict.fromkeys(self.recovered_concepts))
        self.persistent_weaknesses = list(dict.fromkeys(self.persistent_weaknesses))

        # Invariant 1: Demonstrated vs Missing mutual exclusivity
        for d in self.demonstrated_concepts:
            if d in self.missing_concepts:
                self.missing_concepts.remove(d)
            if d in self.partially_demonstrated_concepts:
                self.partially_demonstrated_concepts.remove(d)
            if d in self.weak_concepts:
                self.weak_concepts.remove(d)

        # Invariant 2: Recovered concepts purged from active weaknesses
        for r in self.recovered_concepts:
            if r in self.persistent_weaknesses:
                self.persistent_weaknesses.remove(r)
            if r in self.repeatedly_missing_concepts:
                self.repeatedly_missing_concepts.remove(r)
            if r in self.missing_concepts:
                self.missing_concepts.remove(r)

        # Invariant 3: demonstrated_once vs consistently_demonstrated disjointness
        demo_once = []
        demo_cons = []
        for d in self.demonstrated_concepts:
            cnt = self.concept_demonstration_counts.get(d, 0)
            if cnt >= 2:
                demo_cons.append(d)
                self.mastery_levels[d] = ConceptMasteryLevel.CONSISTENTLY_DEMONSTRATED.value
            else:
                demo_once.append(d)
                if self.mastery_levels.get(d) != ConceptMasteryLevel.RECOVERED.value:
                    self.mastery_levels[d] = ConceptMasteryLevel.DEMONSTRATED_ONCE.value

        self.demonstrated_once_concepts = demo_once
        self.consistently_demonstrated_concepts = demo_cons

        # Invariant 4: Strong vs Weak non-overlapping
        for s in self.strong_concepts:
            if s in self.weak_concepts:
                self.weak_concepts.remove(s)

        # Invariant 5: Update concept_map canonical status
        for d in self.demonstrated_concepts:
            self.concept_map[d] = "demonstrated"
        for p in self.partially_demonstrated_concepts:
            if p not in self.demonstrated_concepts:
                self.concept_map[p] = "partially_demonstrated"
        for m in self.missing_concepts:
            if m not in self.demonstrated_concepts:
                self.concept_map[m] = "missing"

    def assert_invariants_valid(self) -> bool:
        """Asserts that state invariants are strictly preserved without contradiction."""
        assert set(self.demonstrated_concepts).isdisjoint(set(self.missing_concepts)), "demonstrated and missing concepts overlap"
        assert set(self.demonstrated_once_concepts).isdisjoint(set(self.consistently_demonstrated_concepts)), "demonstrated_once and consistently_demonstrated overlap"
        assert set(self.recovered_concepts).isdisjoint(set(self.persistent_weaknesses)), "recovered and persistent weaknesses overlap"
        assert set(self.strong_concepts).isdisjoint(set(self.weak_concepts)), "strong and weak concepts overlap"
        return True


    def is_persistent_weakness(self, concept: str) -> bool:
        """Returns True if concept has been missed/weak across multiple turns."""
        return concept in self.persistent_weaknesses or self.concept_missing_counts.get(concept, 0) >= 2

    def has_consecutive_strong(self, threshold: int = 2) -> bool:
        """Returns True if candidate has achieved consecutive high scores >= 80."""
        return self.consecutive_strong_count >= threshold

    def has_consecutive_weak(self, threshold: int = 2) -> bool:
        """Returns True if candidate has exhibited consecutive low scores < 55."""
        return self.consecutive_weak_count >= threshold

    def has_recovered(self, concept: str) -> bool:
        """Returns True if concept was previously missed and has now been demonstrated."""
        return concept in self.recovered_concepts

    def get_concept_coverage_summary(self) -> Dict[str, Any]:
        """Returns structured breakdown of demonstrated, partial, missing knowledge, and mastery confidence."""
        return {
            "total_concepts_tracked": len(self.concept_map),
            "demonstrated_count": len(self.demonstrated_concepts),
            "partially_demonstrated_count": len(self.partially_demonstrated_concepts),
            "missing_count": len(self.missing_concepts),
            "demonstrated": self.demonstrated_concepts,
            "partially_demonstrated": self.partially_demonstrated_concepts,
            "missing": self.missing_concepts,
            "concept_map": self.concept_map,
            # Phase B Mastery & Trend Summary
            "consistently_demonstrated": self.consistently_demonstrated_concepts,
            "demonstrated_once": self.demonstrated_once_concepts,
            "repeatedly_missing": self.repeatedly_missing_concepts,
            "recovered": self.recovered_concepts,
            "persistent_weaknesses": self.persistent_weaknesses,
            "mastery_levels": self.mastery_levels,
            "rolling_score_trend": self.rolling_score_trend,
            "consecutive_strong_count": self.consecutive_strong_count,
            "consecutive_weak_count": self.consecutive_weak_count
        }
