"""
Canonical Source of Truth for Competency Concepts and Keywords in BoardRoom AI.
Provides unified, auditable concept definitions used consistently across:
1. Grounded RAG Retrieval (rag/retriever.py)
2. Question Relevance Evaluation (evaluator/relevance.py)
3. Target Concept Selection (adaptive/target_concept.py)
4. Competency Matrix & Evaluation (adaptive/competency_matrix.py, adaptive/competency_evaluator.py)
5. Final Scorecard Synthesis (adaptive/scorecard_engine.py)
"""

from typing import Dict, List


# Canonical competency core concepts
COMPETENCY_CORE_CONCEPTS: Dict[str, List[str]] = {
    "backend": [
        "REST APIs",
        "statelessness",
        "HTTP status codes",
        "idempotency",
        "JWT authentication",
        "refresh token rotation",
        "concurrency race conditions",
        "mutex synchronization"
    ],
    "database": [
        "B-Tree indexing",
        "composite indexing",
        "indexing trade-offs",
        "write amplification",
        "database transactions",
        "ACID guarantees",
        "database sharding",
        "cross-shard queries"
    ],
    "system_design": [
        "horizontal scaling",
        "load balancing",
        "stateless application tier",
        "read replicas",
        "caching strategies",
        "cache invalidation",
        "distributed locking",
        "two-phase commit"
    ],
    "cs_fundamentals": [
        "time complexity",
        "space complexity",
        "hash tables",
        "threads vs processes",
        "memory management"
    ],
    "scenario_managerial": [
        "incident triage",
        "post-mortem analysis",
        "technical debt management",
        "code review practices"
    ],
    "ice_breaker": [
        "software architecture overview",
        "recent technical project",
        "core engineering strengths"
    ]
}


# Lexical keywords for grounding and relevance evaluation
_BASE_COMPETENCY_KEYWORDS: Dict[str, List[str]] = {
    "cs_fundamentals": [
        "oop", "inheritance", "composition", "polymorphism", "encapsulation",
        "process", "thread", "concurrency", "stack", "heap", "memory",
        "garbage collection", "tcp", "handshake", "socket", "git", "os"
    ],
    "backend": [
        "rest", "api", "http", "verb", "idempotent", "stateless", "jwt",
        "auth", "token", "refresh", "session", "middleware", "rate limit",
        "cookie", "endpoint", "controller", "payload", "microservice"
    ],
    "database": [
        "sql", "nosql", "index", "b-tree", "acid", "transaction", "isolation",
        "read committed", "repeatable read", "phantom", "table scan",
        "migration", "schema", "connection pool", "wal", "foreign key"
    ],
    "system_design": [
        "cache", "redis", "cache-aside", "write-through", "ttl", "stampede",
        "load balancer", "layer 4", "layer 7", "sharding", "consistent hashing",
        "cap theorem", "pacelc", "message queue", "kafka", "cqrs", "event sourcing"
    ],
    "scenario_managerial": [
        "incident", "production", "outage", "timeout", "504", "cpu",
        "triage", "mitigate", "post-mortem", "technical debt", "stakeholder",
        "prioritize", "code review", "mentor", "velocity", "refactor"
    ],
    "ice_breaker": [
        "background", "project", "experience", "journey", "role", "introduction",
        "interest", "learning", "tech stack", "tools", "challenge"
    ]
}


def build_unified_competency_keyword_map() -> Dict[str, List[str]]:
    """
    Builds the unified competency keyword map by merging base keywords with canonical concepts.
    Uses exact phrases and words with len >= 4 to avoid false substring matches.
    """
    unified: Dict[str, List[str]] = {}
    for comp, kw_list in _BASE_COMPETENCY_KEYWORDS.items():
        words = list(kw_list)
        for concept in COMPETENCY_CORE_CONCEPTS.get(comp, []):
            concept_lower = concept.lower()
            if concept_lower not in words:
                words.append(concept_lower)
            for part in concept_lower.split():
                if len(part) >= 4 and part not in words and part not in ("with", "from", "into", "over", "read"):
                    words.append(part)
        unified[comp] = list(dict.fromkeys(words))
    return unified


def get_canonical_concepts_for_competency(competency: str) -> List[str]:
    """Returns canonical assessment concepts for a given competency."""
    return list(COMPETENCY_CORE_CONCEPTS.get(competency, []))


def get_all_canonical_concepts() -> Dict[str, List[str]]:
    """Returns dictionary of all canonical competency concept definitions."""
    return {k: list(v) for k, v in COMPETENCY_CORE_CONCEPTS.items()}
