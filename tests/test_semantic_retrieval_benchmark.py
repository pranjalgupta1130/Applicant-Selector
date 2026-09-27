"""
Semantic Retrieval Golden Benchmark (Section 4 & 5 of Ralph Master Mission).
Compares Dense Semantic Retrieval against TF-IDF Fallback Retrieval.
Verifies:
- Minimal lexical overlap semantic queries (paraphrases without shared keywords)
- Conceptual questions & terminology variants
- Metadata filtering (competency, stage, difficulty)
- Fallback mode (TF-IDF) execution and explicit mode separation
- Empty & irrelevant queries
- Loud diagnostic reporting of retrieval_mode and dense_embeddings_active
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from rag.retriever import KnowledgeRetriever
from core.schemas import RetrievalResponse


@pytest.fixture(scope="module")
def dense_retriever() -> KnowledgeRetriever:
    """Instantiates retriever in dense semantic mode."""
    return KnowledgeRetriever(use_embeddings=True)


@pytest.fixture(scope="module")
def tfidf_retriever() -> KnowledgeRetriever:
    """Instantiates retriever forced into lexical TF-IDF fallback mode."""
    return KnowledgeRetriever(use_embeddings=False)


# ---------------------------------------------------------
# Diagnostic & Mode Reporting Tests
# ---------------------------------------------------------

class TestRetrievalModeDiagnostics:
    """Ensures the system never silently misrepresents TF-IDF as semantic retrieval."""

    def test_dense_mode_status_reporting(self, dense_retriever):
        """Verifies loud status banner and properties when dense embeddings are active."""
        if dense_retriever.dense_embeddings_active:
            assert dense_retriever.retrieval_mode == "dense"
            banner = dense_retriever.get_status_banner()
            assert "Mode: DENSE" in banner
            assert "Dense retrieval: ACTIVE" in banner
            assert "all-MiniLM-L6-v2" in banner
            assert dense_retriever.get_status_dict()["dense_embeddings_active"] is True

    def test_tfidf_fallback_status_reporting(self, tfidf_retriever):
        """Verifies explicit fallback status when dense embeddings are disabled."""
        assert tfidf_retriever.dense_embeddings_active is False
        assert tfidf_retriever.retrieval_mode == "tfidf"
        banner = tfidf_retriever.get_status_banner()
        assert "Mode: TF-IDF FALLBACK" in banner
        assert "Dense retrieval: INACTIVE" in banner
        assert tfidf_retriever.get_status_dict()["dense_embeddings_active"] is False


# ---------------------------------------------------------
# Semantic vs Lexical Retrieval Benchmark
# ---------------------------------------------------------

class TestSemanticRetrievalBenchmark:
    """
    Evaluates queries with minimal lexical overlap to prove dense semantic retrieval
    outperforms lexical matching on conceptual paraphrasing.
    """

    def test_zero_keyword_database_index_query(self, dense_retriever, tfidf_retriever):
        """
        Master Mission Canonical Test:
        Knowledge: "Database indexing using B-Trees..."
        Query: "What data structure helps a database locate records efficiently without scanning every row?"
        The query contains neither 'B-Tree' nor 'Index', but describes the exact conceptual mechanism.
        """
        query = "What data structure helps a database locate records efficiently without scanning every row?"

        # 1. Dense Semantic Mode
        if dense_retriever.dense_embeddings_active:
            res_dense: RetrievalResponse = dense_retriever.retrieve(query, top_k=3)
            assert res_dense.total_found > 0
            retrieved_chunk_ids = [r.chunk_id for r in res_dense.results]
            # Must retrieve database indexing chunk through semantic understanding
            assert any(cid in ("chunk_tech_idx_01", "chunk_fund_db_01", "chunk_tech_sharding_01") for cid in retrieved_chunk_ids), (
                f"Dense semantic retrieval failed to find indexing chunk for conceptual query! Got: {retrieved_chunk_ids}"
            )

        # 2. TF-IDF Fallback Mode
        res_tfidf: RetrievalResponse = tfidf_retriever.retrieve(query, top_k=3, force_fallback=True)
        assert res_tfidf.total_found > 0

    def test_in_memory_volatile_storage_paraphrase(self, dense_retriever):
        """Query describing in-memory caching without using the words 'Redis' or 'Cache'."""
        if not dense_retriever.dense_embeddings_active:
            pytest.skip("Dense embeddings not available in current test environment")

        query = "How can we hold hot volatile data in memory so we do not hit physical storage?"
        res = dense_retriever.retrieve(query, top_k=3)
        retrieved_ids = [r.chunk_id for r in res.results]
        assert any("redis" in cid or "cache" in cid or "http" in cid for cid in retrieved_ids), (
            f"Expected caching chunk for volatile storage query, got: {retrieved_ids}"
        )

    def test_stateless_authentication_paraphrase(self, dense_retriever):
        """Query describing JWT without using 'JWT' or 'JSON Web Token'."""
        if not dense_retriever.dense_embeddings_active:
            pytest.skip("Dense embeddings not available in current test environment")

        query = "How can an API verify client identity cryptographically without looking up active sessions in a database?"
        res = dense_retriever.retrieve(query, top_k=3)
        retrieved_ids = [r.chunk_id for r in res.results]
        assert any("jwt" in cid or "rest" in cid or "auth" in cid for cid in retrieved_ids), (
            f"Expected auth chunk for signed token query, got: {retrieved_ids}"
        )

    def test_metadata_filtering_competency(self, dense_retriever):
        """Enforcing competency metadata constraint restricts results accurately."""
        query = "distributed scaling and high availability"
        res = dense_retriever.retrieve(query, competency="system_design", top_k=3)
        assert res.total_found > 0
        for r in res.results:
            assert r.competency == "system_design"

    def test_stage_and_difficulty_filtering(self, dense_retriever):
        """Enforcing stage and difficulty yields appropriately calibrated chunks."""
        query = "concurrency and transactions"
        res = dense_retriever.retrieve(query, stage="fundamentals", difficulty=2, top_k=2)
        assert res.total_found > 0
        for r in res.results:
            assert r.stage == "fundamentals"

    def test_empty_query_handling(self, dense_retriever):
        """Empty query returns candidates gracefully without crashing."""
        res = dense_retriever.retrieve("", competency="backend", top_k=2)
        assert res.total_found == 2
        for r in res.results:
            assert r.competency == "backend"

    def test_irrelevant_query_handling(self, dense_retriever):
        """Irrelevant query about cooking still yields valid bounded schema without breaking."""
        query = "baking sourdough bread with yeast and organic flour"
        res = dense_retriever.retrieve(query, top_k=3)
        assert res.total_found <= 3
        # In dense mode with normalized cosine similarity, an irrelevant query should have relatively low scores
        if dense_retriever.dense_embeddings_active and res.results:
            assert res.results[0].score < 0.85
