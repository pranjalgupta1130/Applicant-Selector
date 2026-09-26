"""
Retrieval Golden Evaluation Suite for BoardRoom AI.
Covers all retrieval evaluation scenarios required by Post-Audit Priority 5:
- semantically similar query with different wording
- exact keyword query
- wrong competency
- wrong stage
- wrong difficulty
- metadata relaxation
- irrelevant query
- top-k ordering
- embedding fallback
- empty retrieval
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "ai-service"))

from rag.retriever import KnowledgeRetriever


@pytest.fixture(scope="module")
def retriever():
    return KnowledgeRetriever()


# -----------------------------------------------------------------
# Golden Retrieval Test Cases (Query -> Expected Target Chunk ID)
# -----------------------------------------------------------------

GOLDEN_RETRIEVAL_SET = [
    {
        "name": "Semantic Paraphrase: Idempotency Keys",
        "query": "preventing duplicate credit card transactions when mobile network connection times out",
        "competency": "backend",
        "expected_chunk": "chunk_tech_idempotency_01"
    },
    {
        "name": "Semantic Paraphrase: Snowflake IDs",
        "query": "generating time-sorted 64-bit unique identifiers across distributed clusters to avoid index fragmentation",
        "competency": "system_design",
        "expected_chunk": "chunk_deep_uid_01"
    },
    {
        "name": "Exact Keyword: B-Tree Indexing",
        "query": "B-Tree index lookup vs table scan EXPLAIN execution plan",
        "competency": "database",
        "expected_chunk": "chunk_tech_idx_01"
    },
    {
        "name": "Semantic Paraphrase: Rate Limiting",
        "query": "protecting backend endpoints from burst traffic using token bucket algorithm in Redis",
        "competency": "backend",
        "expected_chunk": "chunk_tech_ratelimit_01"
    },
    {
        "name": "Exact Keyword: Raft Consensus",
        "query": "Raft consensus leader election log replication split-brain",
        "competency": "database",
        "expected_chunk": "chunk_deep_consensus_01"
    },
    {
        "name": "Semantic Paraphrase: Zero-Downtime Migration",
        "query": "renaming database columns in production tables with expand contract pattern without table locks",
        "competency": "scenario_managerial",
        "expected_chunk": "chunk_scen_migration_01"
    }
]


def test_golden_retrieval_benchmark(retriever):
    """
    Evaluates Recall@3 on the Golden Retrieval Set.
    Asserts that the expected chunk appears in top-3 for all benchmark queries.
    """
    hits = 0
    total = len(GOLDEN_RETRIEVAL_SET)
    results_summary = []

    for item in GOLDEN_RETRIEVAL_SET:
        res = retriever.retrieve(
            query=item["query"],
            competency=item["competency"],
            top_k=3
        )
        retrieved_ids = [r.chunk_id for r in res.results]
        is_hit = item["expected_chunk"] in retrieved_ids
        if is_hit:
            hits += 1
            rank = retrieved_ids.index(item["expected_chunk"]) + 1
        else:
            rank = -1

        results_summary.append({
            "name": item["name"],
            "expected": item["expected_chunk"],
            "retrieved": retrieved_ids,
            "hit": is_hit,
            "rank": rank
        })

    recall_at_3 = hits / total
    print(f"\n--- Golden Retrieval Benchmark Results ---")
    print(f"Recall@3: {recall_at_3:.2%} ({hits}/{total})")
    for r in results_summary:
        status = f"HIT (Rank {r['rank']})" if r['hit'] else "MISS"
        print(f"  [{status}] {r['name']} -> {r['expected']}")

    assert recall_at_3 == 1.0, f"Expected 100% Recall@3 on golden set, got {recall_at_3:.2%}"


def test_exact_keyword_query(retriever):
    """Checks exact keyword matching gives strong top-1 ranking."""
    res = retriever.retrieve(
        query="TCP 3-Way Handshake SYN ACK TIME_WAIT",
        competency="cs_fundamentals",
        top_k=2
    )
    assert res.total_found > 0
    assert res.results[0].chunk_id == "chunk_fund_net_01"


def test_wrong_competency_filtering(retriever):
    """Checks that filtering by wrong competency strictly isolates or relaxes cleanly."""
    # Query about JWT authentication, but filter database competency
    res = retriever.retrieve(
        query="JWT access token authentication",
        competency="database",
        top_k=2
    )
    assert res.total_found > 0
    # Every returned chunk should belong to the requested database competency
    for r in res.results:
        assert r.competency == "database"


def test_wrong_stage_metadata_handling(retriever):
    """Checks that filtering by an unusual stage returns chunks matching requested stage if available."""
    res = retriever.retrieve(
        query="relational database indexing",
        competency="database",
        stage="fundamentals",
        top_k=2
    )
    assert res.total_found > 0
    assert all(r.stage == "fundamentals" for r in res.results)


def test_wrong_difficulty_proximity_scoring(retriever):
    """Checks that difficulty proximity boost applies when difficulty is specified."""
    res = retriever.retrieve(
        query="distributed systems caching and scaling",
        competency="system_design",
        difficulty=5,
        top_k=3
    )
    assert res.total_found > 0
    # Top result should favor difficulty 5 if available
    top = res.results[0]
    assert top.difficulty_level >= 4


def test_metadata_relaxation_impossible_combination(retriever):
    """Checks relaxation when requested combination does not exist."""
    # Request ice_breaker stage with difficulty 5 in database competency
    res = retriever.retrieve(
        query="database ACID transactions",
        competency="database",
        stage="ice_breaker",
        difficulty=5,
        top_k=2
    )
    assert res.total_found > 0
    # Relaxation should have returned database chunks
    assert any(r.competency == "database" for r in res.results)


def test_irrelevant_query_score_bounds(retriever):
    """Checks that completely unrelated query does not yield inflated similarity scores."""
    res = retriever.retrieve(
        query="how to prepare butter chicken curry and naan bread at home",
        role_id="backend_engineer",
        top_k=3
    )
    assert res.total_found > 0
    # Semantic similarity for totally disjoint domains should be low (< 0.35)
    for r in res.results:
        assert r.score < 0.35, f"Score unexpectedly high for baking query: {r.score}"


def test_top_k_ordering_descending(retriever):
    """Checks that all results are ordered strictly descending by score."""
    res = retriever.retrieve(
        query="REST APIs statelessness and HTTP idempotency verbs",
        competency="backend",
        top_k=4
    )
    scores = [r.score for r in res.results]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i+1], f"Results not sorted descending: {scores}"


def test_embedding_fallback_mode(retriever):
    """Checks that force_fallback=True uses TF-IDF index and still retrieves the relevant chunk."""
    res = retriever.retrieve(
        query="B-Tree index lookup vs table scan",
        competency="database",
        top_k=2,
        force_fallback=True
    )
    assert res.total_found > 0
    assert res.results[0].chunk_id == "chunk_tech_idx_01"


def test_empty_query_retrieval(retriever):
    """Checks that empty or whitespace query returns candidates gracefully without crashing."""
    res = retriever.retrieve(
        query="   ",
        competency="backend",
        stage="role_technical",
        top_k=2
    )
    assert res.total_found > 0
    assert all(r.competency == "backend" for r in res.results)
