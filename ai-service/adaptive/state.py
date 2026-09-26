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

    # Stage & Competency Counters
    stage_question_counts: Dict[str, int] = Field(default_factory=lambda: {
        "ice_breaker": 0,
        "fundamentals": 0,
        "role_technical": 0,
        "deep_dive": 0,
        "scenario_managerial": 0
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
            if m in self.demonstrated_concepts:
                self.demonstrated_concepts.remove(m)
            if m in self.consistently_demonstrated_concepts:
                self.consistently_demonstrated_concepts.remove(m)
            if m in self.demonstrated_once_concepts:
                self.demonstrated_once_concepts.remove(m)

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
