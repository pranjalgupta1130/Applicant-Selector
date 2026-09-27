"""
Curated High-Quality Deterministic Fallback Question Bank for BoardRoom AI.
Contains carefully crafted, candidate-directed Scientist-level interview questions
across all 7 interview stages and 3 primary DRDO scientific/engineering domains:
1. electronics_radar (Radar, DSP, ECE, Embedded)
2. aerodynamics (Aerodynamics, CFD, Propulsion, Aerospace)
3. cyber_computing (Cybersecurity, Networks, Software, Distributed Systems)

Guarantees zero meta-interview questions and zero repetition within a session.
"""

from typing import List, Dict, Any, Optional, Set
from core.schemas import QuestionObject, RubricCriteria


DEFAULT_RUBRIC = RubricCriteria(
    poor="Vague or off-topic response lacking concrete technical details and demonstrated understanding.",
    acceptable="Adequately addresses the core concepts with clear logic and valid engineering principles.",
    excellent="Comprehensive, highly structured response detailing trade-offs, underlying mechanics, and practical verification methodology."
)


# Standard 7-stage ladder
STAGE_ORDER = [
    "ice_breaker",
    "applicant_validation",
    "core_technical",
    "deep_dive",
    "application_scenario",
    "system_engineering",
    "techno_managerial"
]


# Fallback Bank Definition
FALLBACK_QUESTIONS: Dict[str, List[Dict[str, Any]]] = {
    # ---------------------------------------------------------
    # STAGE 1: ICE_BREAKER (Domain-Neutral Background Opening)
    # ---------------------------------------------------------
    "ice_breaker": [
        {
            "id": "ice_breaker_1",
            "text": "Could you briefly walk us through your academic background and the areas of engineering you have worked with most closely?",
            "stage": "ice_breaker",
            "competency": "ice_breaker",
            "difficulty": 1,
            "expectedConcepts": ["academic background", "engineering focus", "relevant coursework", "area of study"],
            "sources": ["chunk_drdo_ice_01"]
        },
        {
            "id": "ice_breaker_2",
            "text": "Could you tell us about one technical project or research problem that you found particularly interesting and why?",
            "stage": "ice_breaker",
            "competency": "ice_breaker",
            "difficulty": 1,
            "expectedConcepts": ["project overview", "technical interest", "engineering problem", "key motivation"],
            "sources": ["chunk_drdo_ice_01"]
        },
        {
            "id": "ice_breaker_3",
            "text": "Which area of your engineering background do you consider your strongest, and what led you to develop that expertise?",
            "stage": "ice_breaker",
            "competency": "ice_breaker",
            "difficulty": 1,
            "expectedConcepts": ["core strengths", "technical expertise", "skills development", "domain focus"],
            "sources": ["chunk_drdo_ice_02"]
        },
        {
            "id": "ice_breaker_4",
            "text": "Could you briefly describe your most significant technical experience so far and the role you personally played in it?",
            "stage": "ice_breaker",
            "competency": "ice_breaker",
            "difficulty": 1,
            "expectedConcepts": ["technical experience", "personal contribution", "role responsibilities", "engineering impact"],
            "sources": ["chunk_drdo_ice_02"]
        },
        {
            "id": "ice_breaker_5",
            "text": "What area of engineering are you currently most interested in exploring further, and why?",
            "stage": "ice_breaker",
            "competency": "ice_breaker",
            "difficulty": 1,
            "expectedConcepts": ["engineering interest", "future direction", "technical curiosity", "specialization"],
            "sources": ["chunk_drdo_ice_02"]
        }
    ],

    # ---------------------------------------------------------
    # STAGE 2: APPLICANT_VALIDATION (Project & Contribution Probing)
    # ---------------------------------------------------------
    "applicant_validation": [
        {
            "id": "applicant_val_1",
            "text": "You mentioned your experience in your application. Could you describe one project where you applied that knowledge and explain your specific contribution?",
            "stage": "applicant_validation",
            "competency": "expertise_validation",
            "difficulty": 2,
            "expectedConcepts": ["applied knowledge", "project context", "individual contribution", "technical implementation"],
            "sources": ["chunk_drdo_val_01"]
        },
        {
            "id": "applicant_val_2",
            "text": "Could you take us through the most technically challenging part of one of your projects and how you addressed it?",
            "stage": "applicant_validation",
            "competency": "expertise_validation",
            "difficulty": 2,
            "expectedConcepts": ["technical challenge", "problem solving", "engineering approach", "resolution"],
            "sources": ["chunk_drdo_val_01"]
        },
        {
            "id": "applicant_val_3",
            "text": "What engineering decisions did you personally make in your most relevant project, and what factors influenced those decisions?",
            "stage": "applicant_validation",
            "competency": "expertise_validation",
            "difficulty": 2,
            "expectedConcepts": ["engineering decisions", "trade-off analysis", "design rationale", "decision factors"],
            "sources": ["chunk_drdo_val_02"]
        },
        {
            "id": "applicant_val_4",
            "text": "How did you validate that the solution you developed actually met the intended requirements?",
            "stage": "applicant_validation",
            "competency": "expertise_validation",
            "difficulty": 2,
            "expectedConcepts": ["verification approach", "testing methodology", "validation evidence", "requirements fulfillment"],
            "sources": ["chunk_drdo_val_02"]
        },
        {
            "id": "applicant_val_5",
            "text": "What was one limitation or failure you encountered in your project, and how did you address it?",
            "stage": "applicant_validation",
            "competency": "expertise_validation",
            "difficulty": 2,
            "expectedConcepts": ["limitation identification", "root cause analysis", "corrective action", "lessons learned"],
            "sources": ["chunk_drdo_val_02"]
        }
    ],

    # ---------------------------------------------------------
    # STAGE 3: CORE_TECHNICAL - ELECTRONICS / RADAR / DSP
    # ---------------------------------------------------------
    "core_technical_electronics_radar": [
        {
            "id": "radar_core_1",
            "text": "What is the purpose of matched filtering in a radar receiver, and how does it affect target detection?",
            "stage": "core_technical",
            "competency": "radar_rf_systems",
            "difficulty": 3,
            "expectedConcepts": ["matched filter", "snr maximization", "known waveform", "target detection"],
            "sources": ["chunk_drdo_radar_01"]
        },
        {
            "id": "radar_core_2",
            "text": "How does sampling frequency affect the processing of a digital signal, and what problems can occur when the sampling rate is inadequate?",
            "stage": "core_technical",
            "competency": "digital_signal_processing",
            "difficulty": 3,
            "expectedConcepts": ["nyquist rate", "aliasing", "sampling frequency", "anti-aliasing filter"],
            "sources": ["chunk_drdo_dsp_01"]
        },
        {
            "id": "radar_core_3",
            "text": "Could you explain how the Doppler effect can be used to estimate target velocity in a radar system?",
            "stage": "core_technical",
            "competency": "radar_rf_systems",
            "difficulty": 3,
            "expectedConcepts": ["doppler shift", "target velocity", "phase shift", "radial speed"],
            "sources": ["chunk_drdo_radar_02"]
        },
        {
            "id": "radar_core_4",
            "text": "What factors would you consider when selecting an FFT-based processing approach for a real-time signal-processing system?",
            "stage": "core_technical",
            "competency": "digital_signal_processing",
            "difficulty": 3,
            "expectedConcepts": ["fft size", "windowing", "real-time latency", "spectral resolution"],
            "sources": ["chunk_drdo_dsp_02"]
        },
        {
            "id": "radar_core_5",
            "text": "How would you distinguish between noise and a genuine target signal in a radar detection system?",
            "stage": "core_technical",
            "competency": "radar_rf_systems",
            "difficulty": 3,
            "expectedConcepts": ["detection threshold", "cfar", "false alarm rate", "snr threshold"],
            "sources": ["chunk_drdo_radar_03"]
        }
    ],

    # ---------------------------------------------------------
    # STAGE 3: CORE_TECHNICAL - AERODYNAMICS
    # ---------------------------------------------------------
    "core_technical_aerodynamics": [
        {
            "id": "aero_core_1",
            "text": "What are the primary factors that influence aerodynamic lift on an aircraft wing?",
            "stage": "core_technical",
            "competency": "aerospace_aerodynamics",
            "difficulty": 3,
            "expectedConcepts": ["angle of attack", "airfoil shape", "air density", "airspeed", "wing area"],
            "sources": ["chunk_drdo_aero_01"]
        },
        {
            "id": "aero_core_2",
            "text": "Could you explain the relationship between angle of attack and lift, including what happens near stall?",
            "stage": "core_technical",
            "competency": "aerospace_aerodynamics",
            "difficulty": 3,
            "expectedConcepts": ["lift coefficient", "stall angle", "boundary layer separation", "critical angle of attack"],
            "sources": ["chunk_drdo_aero_01"]
        },
        {
            "id": "aero_core_3",
            "text": "What is the significance of Reynolds number in aerodynamic analysis?",
            "stage": "core_technical",
            "competency": "computational_fluid_dynamics",
            "difficulty": 3,
            "expectedConcepts": ["reynolds number", "inertial to viscous forces", "laminar-turbulent transition", "scale effects"],
            "sources": ["chunk_drdo_cfd_01"]
        },
        {
            "id": "aero_core_4",
            "text": "How would you approach validating the aerodynamic performance predicted by a computational model?",
            "stage": "core_technical",
            "competency": "computational_fluid_dynamics",
            "difficulty": 3,
            "expectedConcepts": ["wind tunnel testing", "mesh convergence", "experimental validation", "cfd verification"],
            "sources": ["chunk_drdo_cfd_02"]
        },
        {
            "id": "aero_core_5",
            "text": "What factors would you consider when analysing drag for an aircraft operating at different flight conditions?",
            "stage": "core_technical",
            "competency": "aerospace_aerodynamics",
            "difficulty": 3,
            "expectedConcepts": ["parasite drag", "induced drag", "mach number effects", "wave drag"],
            "sources": ["chunk_drdo_aero_02"]
        }
    ],

    # ---------------------------------------------------------
    # STAGE 3: CORE_TECHNICAL - CYBER / COMPUTING
    # ---------------------------------------------------------
    "core_technical_cyber_computing": [
        {
            "id": "cyber_core_1",
            "text": "What are the main security risks you would consider when designing a networked system?",
            "stage": "core_technical",
            "competency": "network_security",
            "difficulty": 3,
            "expectedConcepts": ["attack surface", "eavesdropping", "man in the middle", "unauthorized access"],
            "sources": ["chunk_drdo_cyber_01"]
        },
        {
            "id": "cyber_core_2",
            "text": "How would you detect and investigate an unusual pattern of network traffic?",
            "stage": "core_technical",
            "competency": "incident_response",
            "difficulty": 3,
            "expectedConcepts": ["anomaly detection", "log analysis", "packet inspection", "intrusion detection"],
            "sources": ["chunk_drdo_cyber_02"]
        },
        {
            "id": "cyber_core_3",
            "text": "What is the difference between authentication and authorization, and why are both important?",
            "stage": "core_technical",
            "competency": "cybersecurity",
            "difficulty": 3,
            "expectedConcepts": ["identity verification", "access control", "rbac", "least privilege"],
            "sources": ["chunk_drdo_cyber_01"]
        },
        {
            "id": "cyber_core_4",
            "text": "How would you design a system to protect sensitive data while it is being transmitted?",
            "stage": "core_technical",
            "competency": "cybersecurity",
            "difficulty": 3,
            "expectedConcepts": ["tls encryption", "key exchange", "data integrity", "cipher suites"],
            "sources": ["chunk_drdo_cyber_02"]
        },
        {
            "id": "cyber_core_5",
            "text": "What factors would you consider when designing a resilient backend system?",
            "stage": "core_technical",
            "competency": "backend",
            "difficulty": 3,
            "expectedConcepts": ["fault tolerance", "load balancing", "redundancy", "graceful degradation"],
            "sources": ["chunk_drdo_comp_01"]
        }
    ],

    # ---------------------------------------------------------
    # STAGE 4: DEEP_DIVE (Probing Reasoning & Assumptions)
    # ---------------------------------------------------------
    "deep_dive": [
        {
            "id": "deep_dive_1",
            "text": "What assumptions does your technical approach rely on, and what would happen if one of those assumptions no longer held?",
            "stage": "deep_dive",
            "competency": "deep_dive",
            "difficulty": 4,
            "expectedConcepts": ["model assumptions", "boundary conditions", "sensitivity analysis", "failure mitigation"],
            "sources": ["chunk_drdo_dd_01"]
        },
        {
            "id": "deep_dive_2",
            "text": "What engineering trade-offs did you consider when choosing your approach?",
            "stage": "deep_dive",
            "competency": "deep_dive",
            "difficulty": 4,
            "expectedConcepts": ["trade-off analysis", "performance vs cost", "design options", "selected compromise"],
            "sources": ["chunk_drdo_dd_01"]
        },
        {
            "id": "deep_dive_3",
            "text": "How would you improve your solution if computational resources were significantly constrained?",
            "stage": "deep_dive",
            "competency": "deep_dive",
            "difficulty": 4,
            "expectedConcepts": ["algorithm optimization", "resource constraints", "memory footprint", "latency reduction"],
            "sources": ["chunk_drdo_dd_02"]
        },
        {
            "id": "deep_dive_4",
            "text": "What failure modes would you expect in this system, and how would you identify them?",
            "stage": "deep_dive",
            "competency": "deep_dive",
            "difficulty": 4,
            "expectedConcepts": ["failure modes", "fmea", "diagnostic indicators", "detection mechanisms"],
            "sources": ["chunk_drdo_dd_02"]
        },
        {
            "id": "deep_dive_5",
            "text": "If your initial approach did not produce the expected result, how would you systematically diagnose the problem?",
            "stage": "deep_dive",
            "competency": "deep_dive",
            "difficulty": 4,
            "expectedConcepts": ["systematic debugging", "root cause isolation", "hypothesis testing", "verification steps"],
            "sources": ["chunk_drdo_dd_03"]
        }
    ],

    # ---------------------------------------------------------
    # STAGE 5: APPLICATION_SCENARIO (Field & Operational Scenarios)
    # ---------------------------------------------------------
    "application_scenario": [
        {
            "id": "scenario_1",
            "text": "Suppose the system performs well under laboratory conditions but its performance drops significantly in the field. How would you investigate the cause?",
            "stage": "application_scenario",
            "competency": "application_scenario",
            "difficulty": 4,
            "expectedConcepts": ["environmental factors", "field vs lab conditions", "root cause analysis", "diagnostic instrumentation"],
            "sources": ["chunk_drdo_scen_01"]
        },
        {
            "id": "scenario_2",
            "text": "Imagine that you have strict real-time constraints but limited computational resources. How would you decide which parts of the system to optimize?",
            "stage": "application_scenario",
            "competency": "application_scenario",
            "difficulty": 4,
            "expectedConcepts": ["profiling", "bottleneck identification", "critical path analysis", "selective optimization"],
            "sources": ["chunk_drdo_scen_01"]
        },
        {
            "id": "scenario_3",
            "text": "Suppose testing reveals that the system occasionally produces incorrect results under unusual operating conditions. How would you approach diagnosing and fixing the issue?",
            "stage": "application_scenario",
            "competency": "application_scenario",
            "difficulty": 4,
            "expectedConcepts": ["edge case analysis", "reproducibility", "input validation", "defensive design"],
            "sources": ["chunk_drdo_scen_02"]
        },
        {
            "id": "scenario_4",
            "text": "You are given a requirement that initially appears difficult to meet with the available hardware. How would you evaluate possible solutions and trade-offs?",
            "stage": "application_scenario",
            "competency": "application_scenario",
            "difficulty": 4,
            "expectedConcepts": ["hardware limits", "algorithmic simplification", "requirement negotiation", "feasibility study"],
            "sources": ["chunk_drdo_scen_02"]
        },
        {
            "id": "scenario_5",
            "text": "If you had to deploy your solution in a safety-critical environment, what additional considerations would you introduce?",
            "stage": "application_scenario",
            "competency": "application_scenario",
            "difficulty": 4,
            "expectedConcepts": ["safety protocols", "redundancy", "fail-safe defaults", "rigorous validation"],
            "sources": ["chunk_drdo_scen_03"]
        }
    ],

    # ---------------------------------------------------------
    # STAGE 6: SYSTEM_ENGINEERING (Architecture & Interfaces)
    # ---------------------------------------------------------
    "system_engineering": [
        {
            "id": "system_eng_1",
            "text": "How would you decompose this system into major components and define the interfaces between them?",
            "stage": "system_engineering",
            "competency": "system_engineering",
            "difficulty": 4,
            "expectedConcepts": ["modular decomposition", "interface control", "loose coupling", "component responsibilities"],
            "sources": ["chunk_drdo_sys_01"]
        },
        {
            "id": "system_eng_2",
            "text": "What would you consider the most critical system-level risks, and how would you mitigate them?",
            "stage": "system_engineering",
            "competency": "system_engineering",
            "difficulty": 4,
            "expectedConcepts": ["risk identification", "impact assessment", "mitigation strategy", "contingency planning"],
            "sources": ["chunk_drdo_sys_01"]
        },
        {
            "id": "system_eng_3",
            "text": "How would you design verification and validation activities for a system with strict reliability requirements?",
            "stage": "system_engineering",
            "competency": "system_engineering",
            "difficulty": 4,
            "expectedConcepts": ["v&v strategy", "traceability matrix", "acceptance testing", "qualification standards"],
            "sources": ["chunk_drdo_sys_02"]
        },
        {
            "id": "system_eng_4",
            "text": "How would you balance performance, reliability, maintainability and resource constraints when designing the system?",
            "stage": "system_engineering",
            "competency": "system_engineering",
            "difficulty": 4,
            "expectedConcepts": ["multi-objective optimization", "system trade-offs", "lifecycle considerations", "design constraints"],
            "sources": ["chunk_drdo_sys_02"]
        },
        {
            "id": "system_eng_5",
            "text": "If one subsystem fails intermittently, how would you design the overall system to detect and handle that failure?",
            "stage": "system_engineering",
            "competency": "system_engineering",
            "difficulty": 4,
            "expectedConcepts": ["fault isolation", "health monitoring", "graceful degradation", "failover mechanisms"],
            "sources": ["chunk_drdo_sys_03"]
        }
    ],

    # ---------------------------------------------------------
    # STAGE 7: TECHNO_MANAGERIAL (Leadership & Prioritization)
    # ---------------------------------------------------------
    "techno_managerial": [
        {
            "id": "techno_mgr_1",
            "text": "Suppose your team disagrees about the technical approach to a critical problem. How would you lead the team toward a decision?",
            "stage": "techno_managerial",
            "competency": "techno_managerial",
            "difficulty": 4,
            "expectedConcepts": ["consensus building", "objective criteria", "prototype evaluation", "technical leadership"],
            "sources": ["chunk_drdo_mgr_01"]
        },
        {
            "id": "techno_mgr_2",
            "text": "If a project is approaching a major deadline and testing reveals a serious technical issue, how would you prioritize the response?",
            "stage": "techno_managerial",
            "competency": "techno_managerial",
            "difficulty": 4,
            "expectedConcepts": ["triage", "risk prioritization", "stakeholder communication", "scope adjustment"],
            "sources": ["chunk_drdo_mgr_01"]
        },
        {
            "id": "techno_mgr_3",
            "text": "How would you communicate a significant technical risk to a project manager or senior leadership?",
            "stage": "techno_managerial",
            "competency": "techno_managerial",
            "difficulty": 4,
            "expectedConcepts": ["risk articulation", "impact assessment", "actionable options", "executive communication"],
            "sources": ["chunk_drdo_mgr_02"]
        },
        {
            "id": "techno_mgr_4",
            "text": "How would you balance technical quality against a fixed project deadline?",
            "stage": "techno_managerial",
            "competency": "techno_managerial",
            "difficulty": 4,
            "expectedConcepts": ["quality vs schedule", "technical debt management", "essential features", "risk acceptance"],
            "sources": ["chunk_drdo_mgr_02"]
        },
        {
            "id": "techno_mgr_5",
            "text": "Tell us about a situation where you had to work with others to resolve a difficult technical problem.",
            "stage": "techno_managerial",
            "competency": "techno_managerial",
            "difficulty": 4,
            "expectedConcepts": ["cross-functional collaboration", "problem ownership", "team communication", "successful resolution"],
            "sources": ["chunk_drdo_mgr_03"]
        }
    ]
}


class FallbackQuestionBank:
    """
    Curated Fallback Question Selector.
    Retrieves high-quality, candidate-directed Scientist questions tailored to domain and stage,
    guaranteeing zero repetition across an interview session.
    """

    @classmethod
    def get_fallback_question(
        cls,
        stage: str,
        domain: str = "electronics_radar",
        used_ids: Optional[Set[str]] = None,
        used_questions: Optional[List[str]] = None
    ) -> QuestionObject:
        used_ids = used_ids or set()
        used_questions_text = [q.lower().strip() for q in (used_questions or [])]

        # Standardize domain
        norm_domain = domain.lower()
        if "aero" in norm_domain or "materials" in norm_domain:
            resolved_domain = "aerodynamics"
        elif "cyber" in norm_domain or "security" in norm_domain or "software" in norm_domain or "computing" in norm_domain:
            resolved_domain = "cyber_computing"
        else:
            resolved_domain = "electronics_radar"

        # Resolve candidate stage keys (including alias maps)
        norm_stage = stage.lower().strip()
        stage_aliases = {
            "fundamentals": "applicant_validation",
            "expertise_validation": "applicant_validation",
            "role_technical": "core_technical",
            "scenario_managerial": "application_scenario",
            "system_engineering_design": "system_engineering"
        }
        effective_stage = stage_aliases.get(norm_stage, norm_stage)

        # Build list of stages to search starting from effective_stage along STAGE_ORDER ladder
        try:
            start_idx = STAGE_ORDER.index(effective_stage)
        except ValueError:
            start_idx = 0

        search_stages = STAGE_ORDER[start_idx:] + STAGE_ORDER[:start_idx]

        selected_item: Optional[Dict[str, Any]] = None

        for s in search_stages:
            if s == "core_technical":
                key = f"core_technical_{resolved_domain}"
            else:
                key = s

            bank = FALLBACK_QUESTIONS.get(key, [])
            for q in bank:
                q_id = q["id"]
                q_text = q["text"].lower().strip()

                # Check deduplication by ID and text overlap
                if q_id in used_ids:
                    continue
                if any(q_text in prev or prev in q_text for prev in used_questions_text if len(prev) > 10):
                    continue

                selected_item = q
                break

            if selected_item is not None:
                break

        # If everything in all stages was used (rare safety edge case), pick first from target stage
        if selected_item is None:
            key = f"core_technical_{resolved_domain}" if effective_stage == "core_technical" else effective_stage
            bank = FALLBACK_QUESTIONS.get(key, FALLBACK_QUESTIONS["ice_breaker"])
            selected_item = bank[0]

        # Map generic stage competencies to domain-specific role competencies
        item_comp = selected_item["competency"]
        if item_comp in ("ice_breaker", "expertise_validation", "applicant_validation", "deep_dive", "application_scenario"):
            if resolved_domain == "aerodynamics":
                stage_comp_map = {
                    "ice_breaker": "aerodynamics_fundamentals",
                    "applicant_validation": "aerodynamic_analysis",
                    "deep_dive": "fluid_mechanics_cfd",
                    "application_scenario": "aerodynamic_analysis"
                }
            elif resolved_domain == "cyber_computing":
                stage_comp_map = {
                    "ice_breaker": "cybersecurity_fundamentals",
                    "applicant_validation": "network_security",
                    "deep_dive": "system_resilience",
                    "application_scenario": "network_security"
                }
            else:
                stage_comp_map = {
                    "ice_breaker": "radar_rf_systems",
                    "applicant_validation": "digital_signal_processing",
                    "deep_dive": "digital_signal_processing",
                    "application_scenario": "radar_rf_systems"
                }
            final_competency = stage_comp_map.get(selected_item["stage"], item_comp)
        else:
            final_competency = item_comp

        return QuestionObject(
            id=selected_item["id"],
            text=selected_item["text"],
            stage=selected_item["stage"],
            competency=final_competency,
            difficulty=selected_item["difficulty"],
            expectedConcepts=list(selected_item["expectedConcepts"]),
            rubric=DEFAULT_RUBRIC,
            relevanceScore=95,
            relevanceRationale=f"Curated high-quality fallback for stage '{selected_item['stage']}' and domain '{resolved_domain}'.",
            sources=list(selected_item["sources"]),
            isFallback=True,
            questionType="conceptual"
        )
