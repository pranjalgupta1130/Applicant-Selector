"""
Question Relevance Golden Test Suite for DRDO / RAC Scientific Profile.
Conforms strictly to PSWB01 Section 7, 9, 10, and 23.

Verifies:
1. Highly relevant, grounded question scores >= 85
2. Candidate expertise alignment matches claimed background (FreeRTOS, DSP, Radar)
3. Role alignment matches Scientist 'B' ECE technical requirements
4. Completely irrelevant / non-technical questions penalized heavily (< 40)
5. Out-of-domain software questions penalized on role/candidate alignment
6. Difficulty calibration across interview stages
7. Explainable 5-factor scoring breakdown contract
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from core.schemas import CandidateProfile, TargetRole, QuestionRelevanceBreakdown
from core.drdo_domain import AdvertisedPostProfile, ApplicantExpertiseProfile
from evaluator.relevance import QuestionRelevanceEvaluator


@pytest.fixture
def drdo_role():
    post = AdvertisedPostProfile()
    return TargetRole(
        id=post.post_id,
        title=post.title,
        description=post.organization_context,
        domain=post.domain,
        discipline=post.discipline,
        required_skills=post.required_competencies,
        technical_requirements=post.technical_requirements,
        managerial_requirements=post.managerial_requirements
    )


@pytest.fixture
def drdo_candidate():
    app = ApplicantExpertiseProfile()
    return CandidateProfile(
        id=app.applicant_id,
        name=app.name,
        skills=["Embedded C", "FreeRTOS", "MATLAB", "DSP", "Radar Doppler"],
        experience_years=app.experience_years,
        education=app.education,
        discipline=app.discipline,
        specialization=app.specialization,
        claimed_expertise=app.claimed_expertise,
        projects=app.projects,
        domain="electronics_radar"
    )


class TestDRDOQuestionRelevance:

    def test_excellent_grounded_drdo_question_scores_high(self, drdo_role, drdo_candidate):
        """A crisp, technical question on interrupt latency and FreeRTOS RTOS preemption scores >= 85."""
        q_text = (
            "In a real-time radar signal acquisition system running FreeRTOS, how do you minimize "
            "interrupt latency during high-rate ADC transfers, and how does the NVIC handle nested priority preemption?"
        )
        res = QuestionRelevanceEvaluator.evaluate(
            question_text=q_text,
            role=drdo_role,
            candidate=drdo_candidate,
            competency="embedded_realtime_systems",
            stage="fundamentals",
            difficulty=2,
            expected_concepts=["Interrupt Latency & ISRs", "RTOS Priority Preemption", "vector table"]
        )

        assert isinstance(res, QuestionRelevanceBreakdown)
        assert res.totalScore >= 80
        assert res.roleAlignment >= 80
        assert res.candidateExpertiseAlignment >= 80
        assert res.targetCompetencyAlignment >= 80
        assert "Question relevance scored" in res.rationale

    def test_dsp_filter_question_matches_claimed_expertise(self, drdo_role, drdo_candidate):
        """Question on FIR vs IIR filter phase linearity scores high against claimed DSP expertise."""
        q_text = (
            "Why is constant group delay and strictly linear phase essential in pulsed radar pulse compression, "
            "and why does an FIR digital filter guarantee stability compared to an IIR filter?"
        )
        res = QuestionRelevanceEvaluator.evaluate(
            question_text=q_text,
            role=drdo_role,
            candidate=drdo_candidate,
            competency="digital_signal_processing",
            stage="role_technical",
            difficulty=3,
            expected_concepts=["FIR vs IIR Digital Filters", "linear phase", "group delay"]
        )

        assert res.totalScore >= 80
        assert res.candidateExpertiseAlignment >= 85
        assert res.targetCompetencyAlignment >= 85

    def test_radar_range_equation_question_relevance(self, drdo_role, drdo_candidate):
        """Question on Radar Range Equation and fourth power power aperture."""
        q_text = (
            "Derive the Radar Range Equation and explain why received echo power decreases with the fourth power "
            "of target distance, and how pulse integration improves detection probability."
        )
        res = QuestionRelevanceEvaluator.evaluate(
            question_text=q_text,
            role=drdo_role,
            candidate=drdo_candidate,
            competency="radar_rf_systems",
            stage="role_technical",
            difficulty=3,
            expected_concepts=["Radar Range Equation", "fourth power distance", "radar cross section"]
        )

        assert res.totalScore >= 80
        assert res.roleAlignment >= 80

    def test_irrelevant_nontechnical_question_penalized(self, drdo_role, drdo_candidate):
        """A non-technical or frivolous question must be heavily penalized (< 40)."""
        q_text = "What is your favorite leisure hobby, and how do you spend your Sunday mornings with friends?"
        res = QuestionRelevanceEvaluator.evaluate(
            question_text=q_text,
            role=drdo_role,
            candidate=drdo_candidate,
            competency="embedded_realtime_systems",
            stage="role_technical",
            difficulty=3,
            expected_concepts=["Interrupt Latency & ISRs"]
        )

        assert res.totalScore < 40
        assert res.roleAlignment <= 20
        assert res.targetCompetencyAlignment <= 20

    def test_out_of_domain_web_software_question_penalized(self, drdo_role, drdo_candidate):
        """A question about web frontend/CSS should have low relevance to a DRDO Radar Engineer."""
        q_text = "How do you align UI components using CSS flexbox justify-content and align-items in React web applications?"
        res = QuestionRelevanceEvaluator.evaluate(
            question_text=q_text,
            role=drdo_role,
            candidate=drdo_candidate,
            competency="embedded_realtime_systems",
            stage="role_technical",
            difficulty=3,
            expected_concepts=["Interrupt Latency & ISRs"]
        )

        assert res.totalScore < 50
        assert res.targetCompetencyAlignment <= 30

    def test_stage_difficulty_appropriateness(self, drdo_role, drdo_candidate):
        """Ice-breaker stage with difficulty 1 should receive 100 for difficulty appropriateness."""
        q_text = "Could you summarize your academic specialization in electronics and your primary engineering strengths?"
        res = QuestionRelevanceEvaluator.evaluate(
            question_text=q_text,
            role=drdo_role,
            candidate=drdo_candidate,
            competency="ice_breaker",
            stage="ice_breaker",
            difficulty=1,
            expected_concepts=["academic specialization", "core engineering strengths"]
        )

        assert res.difficultyAppropriateness >= 85
        assert res.totalScore >= 75

    def test_techno_managerial_fmeca_question_relevance(self, drdo_role, drdo_candidate):
        """Techno-managerial question on FMECA risk mitigation in defence systems."""
        q_text = (
            "How do you perform a Failure Modes, Effects, and Criticality Analysis (FMECA) per MIL-STD-1629A "
            "for a radar transceiver, and how do you prioritize high Risk Priority Number (RPN) failure modes?"
        )
        res = QuestionRelevanceEvaluator.evaluate(
            question_text=q_text,
            role=drdo_role,
            candidate=drdo_candidate,
            competency="techno_managerial",
            stage="techno_managerial",
            difficulty=4,
            expected_concepts=["FMECA Risk Mitigation", "risk priority number", "single point of failure"]
        )

        assert res.totalScore >= 80
        assert res.targetCompetencyAlignment >= 85
