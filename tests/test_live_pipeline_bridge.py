"""Regression checks for the service path invoked by the live Node backend."""

import pytest

from core.config import settings
from core.schemas import CandidateProfile, TargetRole
from generator.pipeline import QuestionGeneratorPipeline
from rag.retriever import KnowledgeRetriever


@pytest.mark.parametrize(
    ("domain", "role_id", "competency", "skills", "source_id"),
    [
        ("electronics_radar", "drdo_scientist_radar", "digital_signal_processing", ["Radar Signal Processing", "DSP"], "chunk_drdo_fund_dsp_02"),
        ("aerospace_aerodynamics", "drdo_scientist_aerospace", "computational_fluid_dynamics", ["CFD", "Aerodynamics"], "chunk_aero_cfd_01"),
        ("cyber_computing", "drdo_scientist_cyber", "incident_response", ["Cybersecurity", "Network Security"], "chunk_cyber_incident_01"),
    ],
)
def test_live_generator_carries_domain_retrieval_into_grounded_fallback(monkeypatch, domain, role_id, competency, skills, source_id):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    retriever = KnowledgeRetriever()
    pipeline = QuestionGeneratorPipeline(retriever=retriever)
    candidate = CandidateProfile(id="candidate-test", name="Test Candidate", skills=skills, claimed_expertise=skills, domain=domain)
    role = TargetRole(id=role_id, title=role_id.replace("_", " "), required_skills=skills, technical_requirements=skills, domain=domain)

    question = pipeline.generate(candidate, role, "role_technical", competency, 3)

    trace = question.questionExplanation
    assert trace["retrieval_invoked"] is True
    assert trace["retrieval_count"] > 0
    assert trace["context_reached_generation"] is True
    assert any(source["domain"] == domain and source["score"] > 0 for source in trace["retrieved_sources"])
    assert any(source["id"] in question.sources for source in trace["retrieved_sources"])
    assert question.isFallback is True  # No Gemini credentials in this deterministic regression path.


def test_exhausted_domain_question_bank_uses_new_grounded_remediation_probe(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    retriever = KnowledgeRetriever()
    pipeline = QuestionGeneratorPipeline(retriever=retriever)
    candidate = CandidateProfile(id="candidate-cfd", name="Aero Candidate", skills=["CFD", "Aerodynamics"])
    role = TargetRole(id="drdo_scientist_aerospace", title="Scientist B — Aerodynamics", domain="aerospace_aerodynamics")
    prior = [
        question
        for chunk in retriever.chunks
        if chunk.competency == "computational_fluid_dynamics" and chunk.domain == "aerospace_aerodynamics"
        for question in chunk.sample_questions
    ]

    question = pipeline.generate(
        candidate, role, "expertise_validation", "computational_fluid_dynamics", 2,
        previous_questions=prior, previous_missing_concepts=["mesh independence"]
    )

    assert question.isFallback is True
    assert "mesh independence" in question.text
    assert "How would you apply" in question.text or "Which assumptions" in question.text or "what measurements" in question.text
    assert "chunk_aero_cfd_01" in question.sources

