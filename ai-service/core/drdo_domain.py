"""
DRDO / RAC Domain Profiles and Advertised Post Models for BoardRoom AI.
Conforms strictly to PSWB01 Section 4, 5, 8, 14, 19, and 20.
Defines official-grade, non-classified public scientific domain configurations
for Defence Research and Development Organisation (DRDO) / RAC Board Room Simulations.
"""

from typing import List, Dict, Optional, Tuple, Any
from pydantic import BaseModel, Field


class DRDODomainProfile(BaseModel):
    """
    Scientific and engineering domain configuration for DRDO/RAC interviews.
    Supports multi-domain architecture while strictly isolating domain retrieval boundaries.
    """
    domain_id: str
    display_name: str
    discipline: str
    role_ids: List[str] = Field(default_factory=list)
    competencies: List[str] = Field(default_factory=list)
    core_concepts: Dict[str, List[str]] = Field(default_factory=dict)
    prerequisite_graph: Dict[str, List[str]] = Field(default_factory=dict)
    difficulty_range: Tuple[int, int] = (1, 5)
    interview_stage_configuration: List[str] = Field(
        default_factory=lambda: [
            "ice_breaker",
            "expertise_validation",
            "core_technical",
            "deep_dive",
            "application_scenario",
            "system_engineering_design",
            "techno_managerial"
        ]
    )
    fallback_questions: Dict[str, List[str]] = Field(default_factory=dict)
    source_registry: List[Dict[str, str]] = Field(default_factory=list)
    prohibited_cross_domain_sources: List[str] = Field(default_factory=list)


class AdvertisedPostProfile(BaseModel):
    """
    Specifications of the official RAC Advertised Post against which candidate suitability is evaluated.
    """
    post_id: str = "DRDO-RAC-2026-ECE-001"
    title: str = "Scientist 'B' — Electronics & Communication Engineering (Radar & Embedded Systems)"
    organization_context: str = "Defence Research and Development Organisation (DRDO) / RAC Selection Board"
    domain: str = "electronics_radar"
    discipline: str = "Electronics & Communication Engineering"
    required_competencies: List[str] = Field(
        default_factory=lambda: [
            "embedded_realtime_systems",
            "digital_signal_processing"
        ]
    )
    preferred_competencies: List[str] = Field(
        default_factory=lambda: [
            "radar_rf_systems",
            "avionics_communication",
            "techno_managerial"
        ]
    )
    competency_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "embedded_realtime_systems": 0.30,
            "digital_signal_processing": 0.25,
            "radar_rf_systems": 0.20,
            "avionics_communication": 0.15,
            "techno_managerial": 0.10
        }
    )
    expected_level: int = 3
    advertised_responsibilities: List[str] = Field(
        default_factory=lambda: [
            "Design, implementation, and verification of real-time embedded software for radar signal processors",
            "Development of digital pulse compression, Doppler filtering, and spectral analysis algorithms",
            "Hardware-software integration across dual-redundant MIL-STD-1553B and ARINC-429 avionics architectures",
            "Execution of FMECA risk mitigation and DO-254 / DO-178C aerospace lifecycle compliance"
        ]
    )
    technical_requirements: List[str] = Field(
        default_factory=lambda: [
            "Firm grasp of Nyquist sampling, discrete Fourier transform (FFT), and FIR/IIR filter design",
            "Hands-on embedded C/C++, interrupt latency optimization, and RTOS priority preemption",
            "Understanding of radar range equation, pulse repetition frequency (PRF), and Doppler frequency shift",
            "Familiarity with bus arbitration, error detection (CRC), and triple modular redundancy"
        ]
    )
    managerial_requirements: List[str] = Field(
        default_factory=lambda: [
            "Technical risk mitigation in mission-critical defence systems",
            "Safety-critical lifecycle adherence and configuration control",
            "Cross-disciplinary technical coordination between RF, digital hardware, and software teams"
        ]
    )
    source_provenance: str = "RAC Recruitment Notification 2026 / Scientist 'B' Specification"


class ApplicantExpertiseProfile(BaseModel):
    """
    Candidate's academic background, self-declared expertise, and observed competence tracking.
    Strictly distinguishes CLAIMED EXPERTISE from DEMONSTRATED EVIDENCE.
    """
    applicant_id: str = "app_drdo_001"
    name: str = "Vikram Sharma"
    education: str = "B.Tech in Electronics and Communication Engineering, M.Tech in Signal Processing"
    discipline: str = "Electronics & Communication Engineering"
    specialization: str = "Embedded Systems & Digital Signal Processing"
    claimed_expertise: List[str] = Field(
        default_factory=lambda: [
            "Embedded RTOS (FreeRTOS)",
            "DSP Filter Design (MATLAB/C)",
            "Interrupt Service Routines (ISRs)",
            "FPGA VHDL/Verilog",
            "Radar Doppler Processing"
        ]
    )
    projects: List[str] = Field(
        default_factory=lambda: [
            "FPGA-Based Pulse Doppler Radar Signal Processor Prototype",
            "Hard Real-Time Sensor Telemetry Acquisition Unit using FreeRTOS and CAN Bus"
        ]
    )
    publications: List[str] = Field(
        default_factory=lambda: [
            "Design of Low-Latency FIR Filter on Fixed-Point DSP (IEEE Student Conference)"
        ]
    )
    experience_years: float = 2.0
    tools_technologies: List[str] = Field(
        default_factory=lambda: ["Embedded C", "MATLAB", "Simulink", "FreeRTOS", "Vivado", "Logic Analyzers"]
    )
    self_declared_competencies: Dict[str, str] = Field(
        default_factory=lambda: {
            "digital_signal_processing": "expert",
            "embedded_realtime_systems": "expert",
            "radar_rf_systems": "intermediate",
            "avionics_communication": "familiar",
            "techno_managerial": "beginner"
        }
    )
    # Strictly populated by actual interview evidence:
    observed_competence: Dict[str, str] = Field(default_factory=dict)
    demonstrated_evidence_count: Dict[str, int] = Field(default_factory=dict)
    confidence_per_competency: Dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------
# DRDO Domain Registry (Multi-Domain Architecture)
# ---------------------------------------------------------

DRDO_DOMAIN_REGISTRY: Dict[str, DRDODomainProfile] = {
    # 1. Flagship Demonstration Domain: ECE / Embedded & Radar
    "electronics_radar": DRDODomainProfile(
        domain_id="electronics_radar",
        display_name="Electronics & Radar Systems (Scientist 'B')",
        discipline="Electronics & Communication Engineering",
        role_ids=["scientist_b_ece", "scientist_b_radar_embedded"],
        competencies=[
            "embedded_realtime_systems",
            "digital_signal_processing",
            "radar_rf_systems",
            "avionics_communication",
            "techno_managerial",
            "ice_breaker"
        ],
        core_concepts={
            "embedded_realtime_systems": [
                "Interrupt Latency",
                "RTOS Priority Preemption",
                "Priority Inversion Mitigation",
                "Watchdog Timers",
                "DMA Scatter-Gather",
                "Bare-Metal vs RTOS"
            ],
            "digital_signal_processing": [
                "Nyquist-Shannon Sampling Theorem",
                "Discrete Fourier Transform",
                "FIR vs IIR Digital Filters",
                "Fixed-Point Quantization",
                "Digital Pulse Compression",
                "Adaptive Beamforming"
            ],
            "radar_rf_systems": [
                "Radar Range Equation",
                "Pulse Repetition Frequency",
                "Doppler Frequency Shift",
                "FMCW Radar Principles",
                "AESA Beamforming",
                "Receiver Dynamic Range"
            ],
            "avionics_communication": [
                "MIL-STD-1553B Dual-Redundant Bus",
                "ARINC-429 Serial Protocol",
                "Phase Locked Loops",
                "Digital Modulation BPSK/QPSK",
                "EMI/EMC Shielding & Grounding",
                "Triple Modular Redundancy"
            ],
            "techno_managerial": [
                "FMECA Risk Mitigation",
                "DO-254 / DO-178C Guidelines",
                "MTBF Reliability Prediction",
                "Obsolescence Management",
                "Multi-Disciplinary Engineering Leadership"
            ],
            "ice_breaker": [
                "Candidate Background and Motivation",
                "Academic Specialization Overview",
                "Claimed Expertise Walkthrough",
                "Laboratory and Toolchain Exposure"
            ]
        },
        prerequisite_graph={
            "Discrete Fourier Transform": ["Nyquist-Shannon Sampling Theorem"],
            "Digital Pulse Compression": ["Discrete Fourier Transform", "Nyquist-Shannon Sampling Theorem"],
            "Adaptive Beamforming": ["Digital Pulse Compression", "AESA Beamforming"],
            "RTOS Priority Preemption": ["Interrupt Latency"],
            "Priority Inversion Mitigation": ["RTOS Priority Preemption"],
            "Watchdog Timers": ["Interrupt Latency"],
            "Doppler Frequency Shift": ["Radar Range Equation", "Pulse Repetition Frequency"],
            "AESA Beamforming": ["Radar Range Equation"],
            "MIL-STD-1553B Dual-Redundant Bus": ["Digital Modulation BPSK/QPSK"],
            "Triple Modular Redundancy": ["MIL-STD-1553B Dual-Redundant Bus"]
        },
        source_registry=[
            {
                "title": "Introduction to Radar Systems (3rd Ed.)",
                "author": "Merrill I. Skolnik",
                "publisher": "McGraw-Hill",
                "type": "recognized_academic_textbook"
            },
            {
                "title": "Digital Signal Processing: Principles, Algorithms, and Applications",
                "author": "John G. Proakis & Dimitris G. Manolakis",
                "publisher": "Pearson",
                "type": "recognized_academic_textbook"
            },
            {
                "title": "Real-Time Systems Design and Analysis",
                "author": "Phillip A. Laplante",
                "publisher": "IEEE Computer Society / Wiley",
                "type": "recognized_academic_textbook"
            },
            {
                "title": "MIL-STD-1553B: Digital Time Division Command/Response Multiplex Data Bus",
                "author": "U.S. Department of Defense / Public Technical Standard",
                "publisher": "DoD",
                "type": "official_public_standard"
            },
            {
                "title": "IEEE Standard 686-2017 for Radar Definitions",
                "author": "IEEE Aerospace and Electronic Systems Society",
                "publisher": "IEEE",
                "type": "official_public_standard"
            }
        ],
        prohibited_cross_domain_sources=[
            "software_engineering",
            "web_development",
            "relational_databases",
            "cyber_computing"
        ]
    ),

    # 2. Secondary Domain: Computer Science & Cyber Systems (Scientist 'B')
    "cyber_computing": DRDODomainProfile(
        domain_id="cyber_computing",
        display_name="Computer Science & Cyber Systems (Scientist 'B')",
        discipline="Computer Science & Engineering",
        role_ids=["scientist_b_cse", "backend_engineer"],
        competencies=[
            "backend",
            "database",
            "system_design",
            "cs_fundamentals",
            "scenario_managerial",
            "ice_breaker"
        ],
        core_concepts={
            "cs_fundamentals": ["time complexity", "hash tables", "threads vs processes", "memory management"],
            "backend": ["REST APIs", "statelessness", "JWT authentication", "concurrency race conditions"],
            "database": ["B-Tree indexing", "ACID guarantees", "database sharding"],
            "system_design": ["horizontal scaling", "load balancing", "caching strategies"],
            "scenario_managerial": ["incident triage", "technical debt management"],
            "ice_breaker": ["software architecture overview", "engineering motivation"]
        },
        prerequisite_graph={
            "JWT authentication": ["REST APIs"],
            "database sharding": ["B-Tree indexing"],
            "horizontal scaling": ["load balancing"]
        },
        prohibited_cross_domain_sources=[
            "electronics_radar",
            "radar_rf_systems",
            "avionics_communication"
        ]
    )
}


def get_domain_profile(domain_id: Optional[str] = None) -> DRDODomainProfile:
    """Returns the requested domain profile, defaulting to the flagship 'electronics_radar' domain."""
    domain_key = domain_id or "electronics_radar"
    return DRDO_DOMAIN_REGISTRY.get(domain_key, DRDO_DOMAIN_REGISTRY["electronics_radar"])
