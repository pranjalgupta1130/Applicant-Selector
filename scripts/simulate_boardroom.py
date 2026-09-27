"""
================================================================================
BoardRoom AI (PSWB01) — DRDO/RAC Board Room Interview Simulation
Executable End-to-End Demonstration Script
================================================================================
Demonstrates the full 7-stage DRDO Board Room interview ladder:
  Stage 1: Ice-Breaking / Introduction (Specialization & Research Focus)
  Stage 2: Expertise Validation (Probing Claimed RTOS/Firmware Expertise)
  Stage 3: Core Technical (Digital Signal Processing & Sampling Theory)
  Stage 4: Deep Dive (FMCW Radar Principles & Homodyne Mixing)
  Stage 5: Application / Scenario (Radar Range Equation & 1/R^4 Propagation)
  Stage 6: System Engineering Design (MIL-STD-1553B Dual-Redundant Avionics Bus)
  Stage 7: Techno-Managerial (FMECA Risk Mitigation & Mission Reliability)

Includes:
  - Domain resolution (electronics_radar) with zero cross-domain contamination
  - Claimed vs. Demonstrated Expertise tracking
  - Semantic Answer Evaluation resisting keyword stuffing
  - Complete DecisionTrace logging for every adaptive turn
  - Evidence-based Selector Scorecard with Decision Support (strictly non-autonomous)
"""

import sys
import os
import json
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from core.drdo_domain import (
    DRDODomainProfile,
    AdvertisedPostProfile,
    ApplicantExpertiseProfile,
    get_domain_profile
)
from core.schemas import CandidateProfile, TargetRole, QuestionObject
from adaptive.state import InterviewState
from rag.retriever import KnowledgeRetriever
from generator.pipeline import QuestionGeneratorPipeline
from evaluator.answer_evaluator import MockAnswerEvaluator
from adaptive.policy import AdaptiveInterviewPolicy
from adaptive.scorecard_engine import ScorecardEngine
from adaptive.orchestrator import InterviewOrchestrator


def print_banner(text: str, ch="="):
    width = 78
    print("\n" + ch * width)
    print(f" {text}")
    print(ch * width)


def print_stage_box(turn_num: int, stage: str, competency: str, difficulty: int):
    print(f"\n[{'-'*76}]")
    print(f" TURN {turn_num} | STAGE: {stage.upper():<22} | COMPETENCY: {competency:<25} | LEVEL: {difficulty}/5")
    print(f"[{'-'*76}]")


def run_boardroom_simulation():
    print_banner("PSWB01 -- DRDO/RAC BOARD ROOM INTERVIEW SIMULATION (BoardRoom AI)")
    print("Initializing Domain-Aware RAG Engine and Calibrated Evaluator...")

    # Initialize subsystems
    retriever = KnowledgeRetriever(use_embeddings=True)
    generator = QuestionGeneratorPipeline(retriever=retriever)
    orchestrator = InterviewOrchestrator(
        retriever=retriever,
        generator=generator
    )

    # 1. Load DRDO Domain, Post, and Candidate
    domain_prof = get_domain_profile("electronics_radar")
    post_prof = AdvertisedPostProfile()
    applicant_prof = ApplicantExpertiseProfile()

    candidate = CandidateProfile(
        id=applicant_prof.applicant_id,
        name=applicant_prof.name,
        skills=["Embedded C", "FreeRTOS", "MATLAB", "DSP", "Radar Doppler"],
        experience_years=applicant_prof.experience_years,
        education=applicant_prof.education,
        discipline=applicant_prof.discipline,
        specialization=applicant_prof.specialization,
        claimed_expertise=applicant_prof.claimed_expertise,
        projects=applicant_prof.projects,
        domain="electronics_radar"
    )

    role = TargetRole(
        id=post_prof.post_id,
        title=post_prof.title,
        domain="electronics_radar",
        discipline=post_prof.discipline,
        technical_requirements=post_prof.technical_requirements,
        managerial_requirements=post_prof.managerial_requirements,
        required_skills=post_prof.required_competencies,
        description=post_prof.organization_context
    )

    print(f"\n[1] APPLICANT PROFILE LOADED:")
    print(f"    Name:           {candidate.name}")
    print(f"    Education:      {candidate.education}")
    print(f"    Discipline:     {candidate.discipline} ({candidate.specialization})")
    print(f"    Claimed Skills: {', '.join(candidate.claimed_expertise)}")
    print(f"    Primary Project: {candidate.projects[0]}")

    print(f"\n[2] ADVERTISED POST LOADED:")
    print(f"    Post ID:        {role.id}")
    print(f"    Position:       {role.title}")
    print(f"    Domain:         {role.domain} (Strict Boundary Enforcement Active)")
    print(f"    Required Areas: {', '.join(post_prof.required_competencies)}")

    print(f"\n[3] COMPETENCY MAPPING:")
    for comp in domain_prof.competencies:
        print(f"    - {comp:<30} (Prerequisites mapped in DAG)")

    # Candidate scripted high-proficiency answers tailored to each stage
def generate_strong_candidate_answer(question: QuestionObject) -> str:
    """Intelligently provides a high-proficiency answer addressing the specific question asked."""
    q_lower = (question.text + " " + question.competency + " " + " ".join(question.expectedConcepts)).lower()

    if "ice_breaker" in question.competency or question.stage == "ice_breaker":
        return (
            "I completed my B.Tech in Electronics and Communication and M.Tech in Signal Processing. "
            "My primary project was designing an FPGA-based pulse Doppler radar signal processor prototype, "
            "where I implemented real-time FFT decimation and digital pulse compression in hardware. "
            "My core engineering strengths are embedded firmware and signal processing, motivated by defence radar research."
        )

    if any(k in q_lower for k in ["rtos", "preemption", "priority inversion", "mutex", "context switch", "task stack"]):
        return (
            "In preemptive FreeRTOS, the SysTick interrupt invokes the scheduler to perform a context switch "
            "via the PendSV exception on ARM Cortex-M. The current task's registers are stacked onto its Process Stack "
            "Pointer (PSP) task stacks, and the highest-priority ready task is restored. Mutex synchronization includes "
            "Priority Inheritance to prevent unbounded priority inversion, whereas binary semaphores are pure signaling mechanisms without ownership."
        )

    if "interrupt" in q_lower or "isr" in q_lower or "nvic" in q_lower:
        return (
            "Interrupt latency comprises pipeline flush, vector table fetch, and hardware register stacking. "
            "ISRs must remain minimal and non-blocking, delegating heavy processing to deferred tasks via queues. "
            "The ARM NVIC handles tail-chaining to switch directly between pending interrupts without unstacking overhead."
        )

    if "fmcw" in q_lower or "beat frequency" in q_lower or "sweep bandwidth" in q_lower:
        return (
            "In FMCW radar principles, the transmitter sends a continuous linear chirp sweep with sweep bandwidth B. "
            "The returned echo is mixed with the currently transmitted chirp in a homodyne mixer, producing a beat frequency "
            "f_b proportional to two-way time of flight and target distance. Triangular modulation separates target range from Doppler frequency shift."
        )

    if "doppler" in q_lower or "mti" in q_lower or "blind speed" in q_lower or "canceler" in q_lower:
        return (
            "The Doppler frequency shift is f_d = 2 * v_r / lambda. In Moving Target Indication (MTI), delay line "
            "canceler filters subtract successive pulse echoes to achieve clutter rejection of stationary ground clutter at zero frequency, "
            "and staggered PRF sequences eliminate blind speeds."
        )

    if "radar range" in q_lower or "fourth power" in q_lower or "range equation" in q_lower or "antenna gain" in q_lower:
        return (
            "The received radar echo power decreases with the fourth power of target distance because of two-way spherical spreading. "
            "The transmitted wave expands over an area proportional to R squared on the forward path with directional antenna gain G focusing energy, "
            "and the target's radar cross section reradiates energy that expands over another sphere on the return path, yielding received power "
            "proportional to 1 / R^4."
        )

    if "beamforming" in q_lower or "mvdr" in q_lower or "spatial null" in q_lower:
        return (
            "The MVDR Capon beamformer minimizes total output interference and noise power subject to a distortionless unity gain constraint "
            "in the target look direction: w = inv(Rxx) * a(theta) / (a(theta)^H * inv(Rxx) * a(theta)). Spatial null steering dynamically "
            "places nulls on jammer directions using sample covariance matrix inversion with diagonal loading for numerical stability."
        )

    if "1553" in q_lower or "arinc" in q_lower or "avionics" in question.competency or "bus controller" in q_lower:
        return (
            "MIL-STD-1553B employs a dual-redundant shielded twisted-pair bus running at 1 Mbps with Manchester II encoding "
            "and transformer coupling for galvanic isolation and common-mode noise rejection. The Bus Controller orchestrates all command-response "
            "transfers to remote terminals, switching to Bus B if Bus A detects bus contention, timeout, or parity errors."
        )

    if "fmeca" in q_lower or "risk" in q_lower or "techno_managerial" in question.competency or "reliability" in q_lower:
        return (
            "Under MIL-STD-1629A, FMECA systematically evaluates potential component failure modes, their severity classification, occurrence, "
            "and detection to calculate the Risk Priority Number (RPN = S * O * D). High-RPN single points of failure in radar power "
            "distribution are mitigated through hardware fault tolerance, watchdog resets, and fail-safe graceful degradation."
        )

    # Fallback DSP Nyquist answer
    return (
        "According to the Nyquist-Shannon Sampling Theorem, the sampling rate must exceed twice the maximum frequency "
        "component to avoid spectral foldover aliasing. Before ADC sampling, an analog hardware anti-aliasing filter "
        "is mandatory to suppress out-of-band energy below the ADC dynamic range noise floor."
    )


def run_boardroom_simulation():
    print_banner("PSWB01 -- DRDO/RAC BOARD ROOM INTERVIEW SIMULATION (BoardRoom AI)")
    print("Initializing Domain-Aware RAG Engine and Calibrated Evaluator...")

    # Initialize subsystems
    retriever = KnowledgeRetriever(use_embeddings=True)
    generator = QuestionGeneratorPipeline(retriever=retriever)
    orchestrator = InterviewOrchestrator(
        retriever=retriever,
        generator=generator
    )

    # 1. Load DRDO Domain, Post, and Candidate
    domain_prof = get_domain_profile("electronics_radar")
    post_prof = AdvertisedPostProfile()
    applicant_prof = ApplicantExpertiseProfile()

    candidate = CandidateProfile(
        id=applicant_prof.applicant_id,
        name=applicant_prof.name,
        skills=["Embedded C", "FreeRTOS", "MATLAB", "DSP", "Radar Doppler"],
        experience_years=applicant_prof.experience_years,
        education=applicant_prof.education,
        discipline=applicant_prof.discipline,
        specialization=applicant_prof.specialization,
        claimed_expertise=applicant_prof.claimed_expertise,
        projects=applicant_prof.projects,
        domain="electronics_radar"
    )

    role = TargetRole(
        id=post_prof.post_id,
        title=post_prof.title,
        domain="electronics_radar",
        discipline=post_prof.discipline,
        technical_requirements=post_prof.technical_requirements,
        managerial_requirements=post_prof.managerial_requirements,
        required_skills=post_prof.required_competencies,
        description=post_prof.organization_context
    )

    print(f"\n[1] APPLICANT PROFILE LOADED:")
    print(f"    Name:           {candidate.name}")
    print(f"    Education:      {candidate.education}")
    print(f"    Discipline:     {candidate.discipline} ({candidate.specialization})")
    print(f"    Claimed Skills: {', '.join(candidate.claimed_expertise)}")
    print(f"    Primary Project: {candidate.projects[0]}")

    print(f"\n[2] ADVERTISED POST LOADED:")
    print(f"    Post ID:        {role.id}")
    print(f"    Position:       {role.title}")
    print(f"    Domain:         {role.domain} (Strict Boundary Enforcement Active)")
    print(f"    Required Areas: {', '.join(post_prof.required_competencies)}")

    print(f"\n[3] COMPETENCY MAPPING:")
    for comp in domain_prof.competencies:
        print(f"    - {comp:<30} (Prerequisites mapped in DAG)")

    # 4. Start Interview
    print_banner("BOARD ROOM INTERVIEW COMMENCES -- 7-STAGE PROGRESSION")
    start_res = orchestrator.start_interview(candidate=candidate, role=role)
    curr_q = start_res.openingQuestion
    state_dict = start_res.interviewState

    turn_count = 0
    decision_traces = []

    while curr_q and turn_count < 7:
        turn_count += 1
        print_stage_box(turn_count, curr_q.stage, curr_q.competency, curr_q.difficulty)

        print(f"\n[SELECTOR QUESTION]:")
        print(f"  \"{curr_q.text}\"")
        print(f"  Stage: {curr_q.stage} | Difficulty: {curr_q.difficulty}/5 | Competency: {curr_q.competency}")
        print(f"  Expected Concepts: {', '.join(curr_q.expectedConcepts)}")
        if curr_q.sources:
            print(f"  Grounding Sources:  {', '.join(curr_q.sources)}")
        print(f"  Question Relevance: {curr_q.relevanceScore:.1f}/100 (Alignment with Candidate & Post)")

        # Candidate provides expert answer tailored to question
        ans = generate_strong_candidate_answer(curr_q)

        print(f"\n[APPLICANT ANSWER]:")
        print(f"  \"{ans[:120]}... [total {len(ans.split())} words]\"")

        # Process Turn
        turn_res = orchestrator.process_turn(
            current_question=curr_q,
            candidate_answer=ans,
            interview_state=state_dict,
            candidate=candidate,
            role=role
        )

        eval_res = turn_res.evaluation
        trace = turn_res.trace
        state_dict = turn_res.updatedState
        decision_traces.append(trace)

        print(f"\n[EVALUATION RESULT]:")
        print(f"  Score:               {eval_res.score}/100")
        print(f"  Technical Correct:   {eval_res.technicalCorrectness}")
        print(f"  Completeness:        {eval_res.completeness}")
        print(f"  Relevance:           {eval_res.relevance}")
        print(f"  Depth:               {eval_res.depth}")
        print(f"  Covered Concepts:    {', '.join(eval_res.coveredConcepts)}")
        print(f"  Reasoning:           {eval_res.reasoning}")

        print(f"\n[ADAPTIVE DECISION TRACE]:")
        print(f"  Strategy:            {trace.strategy}")
        print(f"  Adaptive Reason:     {trace.reason}")
        print(f"  Next Difficulty:     {trace.nextDifficulty}/5")
        print(f"  Next Competency:     {trace.nextCompetency}")

        if turn_res.termination.shouldTerminate:
            print(f"\n[TERMINATION NOTICE]: {turn_res.termination.reason}")
            break

        curr_q = turn_res.nextQuestion

    # 5. Synthesize Final Scorecard
    print_banner("INTERVIEW CONCLUDED -- GENERATING FINAL EXPLAINABLE SCORECARD")
    final_state = InterviewState(**state_dict)
    scorecard = ScorecardEngine.generate_scorecard(
        state=final_state,
        candidate=candidate,
        role=role
    )

    print(f"\nCandidate:                {scorecard.candidate.name} ({scorecard.candidate.id})")
    print(f"Advertised Role:          {scorecard.role.title} ({scorecard.role.id})")
    print(f"Overall Subject Score:    {scorecard.overallScore:.1f}/100 (Evidence-Weighted)")
    print(f"Assessment Confidence:    {scorecard.overallConfidence * 100:.0f}%")
    print(f"Role Alignment Score:     {scorecard.roleAlignment.alignmentScore:.1f}/100")
    print(f"Evidence Coverage:        {scorecard.coverage.overallEvidenceCoverage * 100:.0f}%")

    print("\n--- COMPETENCY-LEVEL EVIDENCE BREAKDOWN ---")
    for comp in scorecard.competencies:
        print(f"  * {comp.competency:<30} | Score: {comp.score:>5.1f} | Status: {comp.status:<14} | Conf: {comp.confidence*100:.0f}%")
        print(f"    Concepts Demonstrated: {', '.join(comp.demonstratedConcepts[:3]) if comp.demonstratedConcepts else 'None'}")
        print(f"    Evidence Turns:        {comp.evidenceCount} turn(s)")

    print("\n--- KEY DEMONSTRATED STRENGTHS ---")
    for s in scorecard.strengths:
        print(f"  [+] {s.area} (Competency: {s.competency}, Conf: {s.confidence*100:.0f}%)")

    if scorecard.gaps:
        print("\n--- IDENTIFIED GAPS / UNTESTED AREAS ---")
        for g in scorecard.gaps:
            print(f"  [-] {g.area}: {g.evidence}")

    print("\n--- SELECTOR DECISION SUPPORT & GOVERNANCE ---")
    print(f"  Technical Evidence:     {scorecard.decisionSupport.technicalEvidence[:100]}...")
    print(f"  Managerial Evidence:    {scorecard.decisionSupport.managerialEvidence[:100]}...")
    print(f"\n  [LEGAL / REGULATORY GOVERNANCE NOTE]:")
    print(f"  \"{scorecard.decisionSupport.recommendationNote}\"")

    print_banner("SIMULATION COMPLETED SUCCESSFULLY (100% EVIDENCE TRACE PRESERVED)")
    return 0


if __name__ == "__main__":
    sys.exit(run_boardroom_simulation())
