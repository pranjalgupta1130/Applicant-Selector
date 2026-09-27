"""
Role-Aware Competency Matrix for BoardRoom AI (Phase D).
Defines expected competencies, configurable weights, and expected concept pools
across target engineering roles (Backend Developer, Full Stack Developer, Software Engineer).
"""

from typing import Dict, List, Optional, Any
from core.concepts import COMPETENCY_CORE_CONCEPTS





ROLE_COMPETENCY_PROFILES: Dict[str, Dict[str, Any]] = {
    "backend_engineer": {
        "title": "Backend / Server-Side Engineer",
        "weights": {
            "backend": 0.35,
            "database": 0.25,
            "system_design": 0.25,
            "cs_fundamentals": 0.15
        },
        "min_evidence_target": {
            "backend": 2,
            "database": 1,
            "system_design": 1,
            "cs_fundamentals": 1
        }
    },
    "fullstack_engineer": {
        "title": "Full-Stack Software Engineer",
        "weights": {
            "backend": 0.30,
            "database": 0.25,
            "system_design": 0.25,
            "cs_fundamentals": 0.20
        },
        "min_evidence_target": {
            "backend": 2,
            "database": 1,
            "system_design": 1,
            "cs_fundamentals": 1
        }
    },
    "software_engineer": {
        "title": "General Software Engineer",
        "weights": {
            "cs_fundamentals": 0.30,
            "backend": 0.30,
            "database": 0.20,
            "system_design": 0.20
        },
        "min_evidence_target": {
            "cs_fundamentals": 2,
            "backend": 1,
            "database": 1,
            "system_design": 1
        }
    },
    "scientist_b_ece": {
        "title": "Scientist 'B' — Electronics & Communication Engineering",
        "domain": "electronics_radar",
        "weights": {
            "embedded_realtime_systems": 0.30,
            "digital_signal_processing": 0.25,
            "radar_rf_systems": 0.20,
            "avionics_communication": 0.15,
            "techno_managerial": 0.10
        },
        "min_evidence_target": {
            "embedded_realtime_systems": 2,
            "digital_signal_processing": 1,
            "radar_rf_systems": 1,
            "avionics_communication": 1,
            "techno_managerial": 1
        }
    },
    "scientist_b_radar_embedded": {
        "title": "Scientist 'B' — Radar & Embedded Systems",
        "domain": "electronics_radar",
        "weights": {
            "radar_rf_systems": 0.30,
            "embedded_realtime_systems": 0.30,
            "digital_signal_processing": 0.20,
            "avionics_communication": 0.10,
            "techno_managerial": 0.10
        },
        "min_evidence_target": {
            "radar_rf_systems": 2,
            "embedded_realtime_systems": 2,
            "digital_signal_processing": 1,
            "avionics_communication": 1,
            "techno_managerial": 1
        }
    },
    "drdo_scientist_radar": {
        "title": "Scientist C — Radar Signal Processing",
        "domain": "electronics_radar",
        "weights": {
            "radar_rf_systems": 0.25,
            "digital_signal_processing": 0.25,
            "embedded_realtime_systems": 0.20,
            "system_engineering": 0.15,
            "techno_managerial": 0.15
        },
        "min_evidence_target": {
            "radar_rf_systems": 1,
            "digital_signal_processing": 1,
            "embedded_realtime_systems": 1,
            "system_engineering": 1,
            "techno_managerial": 1
        }
    },
    "drdo_scientist_aerospace": {
        "title": "Scientist B — Aerodynamics",
        "domain": "aerospace_aerodynamics",
        "weights": {
            "aerodynamics_fundamentals": 0.25,
            "fluid_mechanics_cfd": 0.25,
            "aerodynamic_analysis": 0.20,
            "system_engineering": 0.15,
            "techno_managerial": 0.15
        },
        "min_evidence_target": {
            "aerodynamics_fundamentals": 1,
            "fluid_mechanics_cfd": 1,
            "aerodynamic_analysis": 1,
            "system_engineering": 1,
            "techno_managerial": 1
        }
    },
    "drdo_scientist_cyber": {
        "title": "Scientist B — Cybersecurity",
        "domain": "cyber_computing",
        "weights": {
            "cybersecurity_fundamentals": 0.25,
            "network_security": 0.25,
            "system_resilience": 0.20,
            "system_engineering": 0.15,
            "techno_managerial": 0.15
        },
        "min_evidence_target": {
            "cybersecurity_fundamentals": 1,
            "network_security": 1,
            "system_resilience": 1,
            "system_engineering": 1,
            "techno_managerial": 1
        }
    }
}

# Role aliases for resilient matching
ROLE_ALIASES: Dict[str, str] = {
    "backend": "backend_engineer",
    "backend developer": "backend_engineer",
    "backend engineer": "backend_engineer",
    "full stack": "fullstack_engineer",
    "full stack developer": "fullstack_engineer",
    "fullstack": "fullstack_engineer",
    "fullstack engineer": "fullstack_engineer",
    "software engineer": "software_engineer",
    "sde": "software_engineer",
    "general": "software_engineer",
    "drdo_scientist_aerospace": "drdo_scientist_aerospace",
    "drdo_scientist_radar": "drdo_scientist_radar",
    "drdo_scientist_cyber": "drdo_scientist_cyber",
    "scientist_b_ece": "scientist_b_ece",
    "radar": "drdo_scientist_radar",
    "radar engineer": "drdo_scientist_radar",
    "embedded engineer": "scientist_b_ece",
    "drdo-rac-2026-ece-001": "scientist_b_ece"
}


class RoleCompetencyMatrix:
    """
    Manages role competency configurations, expected concepts, and configurable scoring weights.
    """

    @classmethod
    def resolve_role_key(cls, role_id_or_title: Optional[str]) -> str:
        """Normalizes role ID or title into standard profile key."""
        if not role_id_or_title:
            return "backend_engineer"
        clean = role_id_or_title.strip().lower().replace("-", "_")

        # Prioritize explicit domain terms first
        if any(k in clean for k in ("aero", "cfd", "fluid", "aerodynamic", "drdo_scientist_aerospace")):
            return "drdo_scientist_aerospace"
        if any(k in clean for k in ("radar", "dsp", "signal", "rf", "drdo_scientist_radar")):
            return "drdo_scientist_radar"
        if any(k in clean for k in ("cyber", "security", "resilience", "drdo_scientist_cyber")):
            return "drdo_scientist_cyber"
        if any(k in clean for k in ("ece", "electronics")):
            return "scientist_b_ece"

        if clean in ROLE_COMPETENCY_PROFILES:
            return clean
        for alias, target in ROLE_ALIASES.items():
            if alias in clean or clean in alias:
                return target
        return "backend_engineer"

    @classmethod
    def get_role_competencies(cls, role_id: Optional[str]) -> List[str]:
        """Returns the list of core evaluated competencies for a given role."""
        key = cls.resolve_role_key(role_id)
        profile = ROLE_COMPETENCY_PROFILES.get(key, ROLE_COMPETENCY_PROFILES["backend_engineer"])
        return list(profile["weights"].keys())

    @classmethod
    def get_normalized_weights(
        cls,
        role_id: Optional[str],
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Returns normalized competency weights summing to 1.0.
        Allows callers (human selector / test harness) to override default engineering weights.
        """
        key = cls.resolve_role_key(role_id)
        default_weights = dict(ROLE_COMPETENCY_PROFILES[key]["weights"])

        if custom_weights:
            weights_to_normalize = dict(custom_weights)
        else:
            weights_to_normalize = default_weights

        total = sum(weights_to_normalize.values())
        if total <= 0:
            return default_weights

        return {comp: round(w / total, 4) for comp, w in weights_to_normalize.items()}

    @classmethod
    def get_expected_concepts(cls, competency: str) -> List[str]:
        """Returns the benchmark expected concepts pool for a competency."""
        return list(COMPETENCY_CORE_CONCEPTS.get(competency, []))

    @classmethod
    def get_min_evidence_target(cls, role_id: Optional[str], competency: str) -> int:
        """Returns minimum required evaluated turns to establish strong confidence."""
        key = cls.resolve_role_key(role_id)
        return ROLE_COMPETENCY_PROFILES[key]["min_evidence_target"].get(competency, 1)
