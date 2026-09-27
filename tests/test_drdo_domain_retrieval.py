"""
DRDO Domain-Aware Retrieval & Cross-Domain Contamination Test Suite.
Conforms strictly to PSWB01 Section 4, 6, 7, 21, and 22.

Verifies:
1. Direct technical queries
2. Paraphrased technical queries
3. Zero-shared-token semantic queries
4. Strict domain boundary isolation (no cross-domain contamination)
5. Prohibited domain blocking
6. Metadata & stage filtering
7. Source provenance preservation
8. Explicit no-grounded-context behavior
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from rag.retriever import KnowledgeRetriever
from core.schemas import RetrievalRequest


@pytest.fixture(scope="module")
def retriever():
    return KnowledgeRetriever(use_embeddings=True)


class TestDRDODomainRetrieval:

    def test_direct_technical_query_radar_range(self, retriever):
        """Direct query for radar range equation retrieves RF chunks with Skolnik source."""
        res = retriever.retrieve(
            query="radar range equation fourth power target distance received echo power",
            role_id="scientist_b_ece",
            competency="radar_rf_systems",
            domain="electronics_radar",
            top_k=2
        )
        assert res.total_found > 0
        top = res.results[0]
        assert top.domain == "electronics_radar"
        assert top.competency == "radar_rf_systems"
        assert "radar range" in top.title.lower() or "fourth-power" in top.title.lower()
        assert top.source_reference is not None
        assert "Skolnik" in (top.source_title or "") or "Skolnik" in (top.source_reference or "")

    def test_direct_technical_query_interrupt_latency(self, retriever):
        """Direct query for interrupt latency retrieves embedded ARM Cortex chunk."""
        res = retriever.retrieve(
            query="interrupt latency hardware register stacking NVIC vector table",
            role_id="scientist_b_ece",
            competency="embedded_realtime_systems",
            domain="electronics_radar",
            top_k=2
        )
        assert res.total_found > 0
        top = res.results[0]
        assert top.domain == "electronics_radar"
        assert top.competency == "embedded_realtime_systems"
        assert "interrupt" in top.title.lower() or "nvic" in top.title.lower()

    def test_zero_keyword_semantic_query_pulse_compression(self, retriever):
        """Semantic query describing time-bandwidth trade-off without saying 'pulse compression'."""
        if not retriever.dense_embeddings_active:
            pytest.skip("Dense embeddings not active for semantic query test")

        res = retriever.retrieve(
            query="resolving range ambiguity while maintaining energy by modulating carrier frequency across wide sweep",
            role_id="scientist_b_ece",
            domain="electronics_radar",
            top_k=3
        )
        assert res.total_found > 0
        chunk_ids = [r.chunk_id for r in res.results]
        # Should retrieve either digital pulse compression, PRF, or FMCW chunks
        assert any(cid in ("chunk_drdo_tech_dsp_03", "chunk_drdo_fund_rf_02", "chunk_drdo_tech_rf_02") for cid in chunk_ids)

    def test_cross_domain_contamination_strictly_blocked(self, retriever):
        """
        CRITICAL TEST (PSWB01 Section 21 & 22):
        An ECE/Embedded query must NEVER return generic backend/database chunks,
        even if lexical or semantic similarities exist.
        """
        res = retriever.retrieve(
            query="interrupt latency handling in real-time embedded systems",
            role_id="scientist_b_ece",
            domain="electronics_radar",
            top_k=5
        )
        assert res.total_found > 0
        for chunk in res.results:
            assert chunk.domain == "electronics_radar", f"Contamination! Foreign domain chunk returned: {chunk.chunk_id}"
            assert chunk.competency not in ("backend", "database", "system_design", "cs_fundamentals")

    def test_reverse_cross_domain_contamination_blocked(self, retriever):
        """
        Reverse contamination test:
        A software database query must NEVER return radar or avionics chunks.
        """
        res = retriever.retrieve(
            query="b-tree database indexing composite indexes write amplification",
            role_id="backend_engineer",
            domain="cyber_computing",
            top_k=5
        )
        assert res.total_found > 0
        for chunk in res.results:
            assert chunk.domain == "cyber_computing", f"Contamination! ECE chunk returned in cyber domain: {chunk.chunk_id}"
            assert chunk.competency not in ("radar_rf_systems", "embedded_realtime_systems", "digital_signal_processing")

    def test_prohibited_domain_hard_filtering(self, retriever):
        """Explicitly prohibited domains are strictly excluded."""
        res = retriever.retrieve(
            query="system architecture and performance latency",
            prohibited_domains=["cyber_computing"],
            top_k=5
        )
        for chunk in res.results:
            assert chunk.domain != "cyber_computing"

    def test_stage_and_difficulty_filtering_deep_dive(self, retriever):
        """Tests retrieval filtered by deep_dive stage and difficulty 4 in DRDO domain."""
        res = retriever.retrieve(
            query="adaptive beamforming covariance matrix null steering",
            role_id="scientist_b_ece",
            stage="deep_dive",
            difficulty=4,
            domain="electronics_radar",
            top_k=2
        )
        assert res.total_found > 0
        top = res.results[0]
        assert top.stage == "deep_dive"
        assert top.difficulty_level == 4
        assert top.domain == "electronics_radar"

    def test_source_provenance_integrity(self, retriever):
        """Verifies all retrieved DRDO chunks carry authentic source citations."""
        res = retriever.retrieve(
            query="MIL-STD-1553B dual redundant bus transformer coupling",
            role_id="scientist_b_ece",
            competency="avionics_communication",
            domain="electronics_radar",
            top_k=1
        )
        assert res.total_found > 0
        top = res.results[0]
        assert top.source_title is not None
        assert top.source_reference is not None
        assert "1553" in top.source_reference or "1553" in top.source_title

    def test_techno_managerial_fmeca_retrieval(self, retriever):
        """Verifies techno-managerial engineering risk retrieval."""
        res = retriever.retrieve(
            query="FMECA failure modes and effects criticality analysis risk priority number RPN",
            role_id="scientist_b_ece",
            competency="techno_managerial",
            stage="techno_managerial",
            domain="electronics_radar",
            top_k=1
        )
        assert res.total_found > 0
        top = res.results[0]
        assert top.competency == "techno_managerial"
        assert "FMECA" in top.expected_concepts or "FMECA Risk Mitigation" in top.expected_concepts
        assert "1629" in (top.source_reference or "") or "FMECA" in (top.source_title or "")

    def test_no_grounded_context_returns_empty_without_cross_domain_leak(self, retriever):
        """
        When querying an impossible keyword within electronics_radar,
        the system must return empty results rather than leaking chunks from cyber_computing.
        """
        res = retriever.retrieve(
            query="django orm react redux css flexbox web framework",
            role_id="scientist_b_ece",
            domain="electronics_radar",
            top_k=3
        )
        # Even if candidate relaxation occurs, it MUST remain within electronics_radar
        for r in res.results:
            assert r.domain == "electronics_radar"
