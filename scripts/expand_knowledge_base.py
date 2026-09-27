"""
Script to expand and enrich knowledge base for sustained 6-8 turn adaptive interviews.
Enriches existing chunks with complementary sample questions and adds 6 targeted chunks
for previously thin areas (backend fundamentals, system design technical, cs fundamentals).
"""

import json
from pathlib import Path

def main():
    kb_file = Path(__file__).resolve().parent.parent / "data" / "knowledge_base" / "seed_knowledge.json"
    with open(kb_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # 1. Enrich sample questions for key chunks
    enrichment_map = {
        "chunk_ice_01": [
            "What motivated you to specialize in backend development, and what is your favorite architectural problem to solve?",
            "Can you describe your role and contributions to the architecture of your most recent production system?"
        ],
        "chunk_ice_02": [
            "How do you evaluate whether to adopt a new library or framework in an existing backend codebase?",
            "Tell us about a recent technical tool, language feature, or database pattern you learned and applied."
        ],
        "chunk_fund_rest_01": [
            "What makes an HTTP endpoint truly idempotent, and why are PUT and DELETE considered idempotent while POST is not?",
            "How do you design RESTful URL hierarchies and query parameters for filtering and pagination in a production API?"
        ],
        "chunk_fund_oop_01": [
            "How does dependency inversion help maintain loose coupling between business logic and database access layers?",
            "Can you give an example of how you used composition over inheritance to solve a backend refactoring challenge?"
        ],
        "chunk_fund_db_01": [
            "What is the difference between repeatable read and serializable isolation levels in a relational database?",
            "How does a write-ahead log (WAL) guarantee durability during unexpected database server crashes?"
        ],
        "chunk_tech_jwt_01": [
            "How do you implement immediate token revocation in a stateless JWT architecture if a user account is compromised?",
            "What are the security implications of storing JWTs in browser local storage versus HTTP-only Secure SameSite cookies?"
        ],
        "chunk_tech_redis_01": [
            "How do you handle a cache stampede or thundering herd problem when a popular cache key expires?",
            "What are the trade-offs between cache-aside, write-through, and write-back caching strategies?"
        ],
        "chunk_tech_ratelimit_01": [
            "How does the sliding window log algorithm compare with the token bucket algorithm in terms of memory and precision?",
            "How would you implement distributed rate limiting across multiple stateless API server instances using Redis?"
        ],
        "chunk_tech_idx_01": [
            "Why does a composite index on columns (A, B) not speed up queries filtering only on column B?",
            "What is a covering index, and how does it prevent secondary lookup into the clustered index table?"
        ],
        "chunk_deep_deadlock_01": [
            "What are the four Coffman conditions required for a deadlock to occur in a concurrent system?",
            "How can consistent lock ordering and timeouts be used to detect and prevent deadlocks in distributed transactions?"
        ]
    }

    for c in chunks:
        cid = c["id"]
        if cid in enrichment_map:
            current_qs = c.get("sample_questions", [])
            for new_q in enrichment_map[cid]:
                if new_q not in current_qs:
                    current_qs.append(new_q)
            c["sample_questions"] = current_qs

    # 2. Add 6 targeted chunks for thin areas
    new_chunks = [
        {
            "id": "chunk_be_fund_http",
            "role_id": "backend_engineer",
            "competency": "backend",
            "stage": "fundamentals",
            "difficulty_level": 2,
            "title": "HTTP Request Lifecycle, Headers, and Status Code Semantics",
            "content": "Core protocol knowledge for backend engineers. Understanding the end-to-end HTTP request lifecycle: DNS lookup, TCP handshake, TLS negotiation, HTTP request line, headers (Content-Type, Authorization, Accept), payload parsing, status codes (2xx, 3xx, 4xx, 5xx), and connection keep-alive.",
            "expected_concepts": ["http lifecycle", "status codes", "request headers", "tcp handshake", "stateless protocol"],
            "sample_questions": [
                "Can you trace what happens under the hood when a client sends an HTTP request to a backend server, including DNS, TCP, and header processing?",
                "What is the difference between 401 Unauthorized and 403 Forbidden status codes, and when should each be returned?",
                "How do HTTP keep-alive connections improve throughput in high-volume microservice communication?"
            ],
            "rubric": {
                "poor": "Cannot explain basic HTTP status codes or confuses client and server errors.",
                "acceptable": "Correctly explains request/response flow, header roles, and distinguishes key 2xx, 4xx, and 5xx codes.",
                "excellent": "Deep explanation covering transport handshakes, header parsing, connection multiplexing, and precise error handling semantics."
            },
            "source": "RFC-7231-HTTP-Semantics"
        },
        {
            "id": "chunk_be_fund_middleware",
            "role_id": "backend_engineer",
            "competency": "backend",
            "stage": "fundamentals",
            "difficulty_level": 2,
            "title": "Backend Middleware Architecture and Request Interception",
            "content": "Fundamental software architecture pattern in web frameworks (Express, FastAPI, Django, Gin). Middleware forms an onion or pipeline model intercepting incoming requests and outgoing responses. Used for authentication, request logging, tracing context injection, CORS enforcement, rate limiting, and global exception handling.",
            "expected_concepts": ["middleware pipeline", "request interception", "cors handling", "global error handler", "context propagation"],
            "sample_questions": [
                "How does the middleware pipeline work in a web framework, and how does request/response flow through multiple middleware layers?",
                "How would you design a custom middleware to inject a unique request correlation ID for distributed log tracing?",
                "What are the consequences if an unhandled exception occurs inside a middleware, and how should it be caught?"
            ],
            "rubric": {
                "poor": "Unfamiliar with the concept of middleware or unable to explain how it processes requests.",
                "acceptable": "Explains request interception, execution ordering, and common use cases like auth or logging.",
                "excellent": "Mastery of pipeline execution, error propagation, non-blocking asynchronous middleware, and request context lifecycle."
            },
            "source": "Web-Framework-Architecture-Guide"
        },
        {
            "id": "chunk_cs_tech_concurrency",
            "role_id": "backend_engineer",
            "competency": "cs_fundamentals",
            "stage": "role_technical",
            "difficulty_level": 3,
            "title": "Thread Safety, Mutexes, and Race Condition Mitigation",
            "content": "Critical concurrency concepts in multi-threaded backend applications. When multiple worker threads access shared mutable state without synchronization, race conditions and data corruption occur. Key primitives include mutual exclusion locks (mutexes), read-write locks, atomic operations, and lock-free data structures.",
            "expected_concepts": ["thread safety", "race conditions", "mutex locks", "atomic operations", "shared mutable state"],
            "sample_questions": [
                "What causes a race condition in a multi-threaded web application, and how do mutexes or read-write locks prevent it?",
                "Explain the difference between a mutex lock and atomic operations when incrementing a shared counter in memory.",
                "How does a deadlock occur when two threads acquire multiple locks in different orders, and how can it be avoided?"
            ],
            "rubric": {
                "poor": "Fails to understand race conditions or believes multi-threading is always safe.",
                "acceptable": "Explains race conditions clearly and describes how mutex locks enforce critical sections.",
                "excellent": "In-depth breakdown of lock contention, atomic CAS instructions, read-write lock trade-offs, and deadlock prevention hierarchies."
            },
            "source": "Operating-Systems-Concurrency-Patterns"
        },
        {
            "id": "chunk_cs_deep_memory",
            "role_id": "backend_engineer",
            "competency": "cs_fundamentals",
            "stage": "deep_dive",
            "difficulty_level": 4,
            "title": "Memory Management, Garbage Collection Cycles, and Heap Optimization",
            "content": "Advanced computer science fundamentals regarding runtime memory execution. Contrasts stack vs heap allocation. Details garbage collection mechanisms (mark-and-sweep, generational GC, reference counting) and the performance implications of stop-the-world pauses, memory leaks in long-running services, and CPU cache locality.",
            "expected_concepts": ["stack vs heap", "garbage collection", "stop the world pause", "memory leak", "reference counting"],
            "sample_questions": [
                "How do garbage collectors like generational mark-and-sweep impact low-latency backend services during major collection cycles?",
                "What is the difference between stack and heap allocation, and what leads to a memory leak in a managed runtime like Node.js or Python?",
                "How does CPU cache line utilization and memory access patterns affect throughput in data-intensive backend algorithms?"
            ],
            "rubric": {
                "poor": "Does not know the difference between stack and heap or assumes managed runtimes cannot leak memory.",
                "acceptable": "Explains stack vs heap, basic garbage collection passes, and how lingering references cause memory leaks.",
                "excellent": "Comprehensive analysis of GC pause latency, generational heuristics, allocation escapes, and cache-conscious data structures."
            },
            "source": "Systems-Programming-Memory-Models"
        },
        {
            "id": "chunk_sd_tech_gateway",
            "role_id": "backend_engineer",
            "competency": "system_design",
            "stage": "role_technical",
            "difficulty_level": 3,
            "title": "API Gateway Architecture, Reverse Proxies, and Edge Routing",
            "content": "Core architectural component in distributed systems. An API Gateway sits between external clients and internal backend microservices. Provides reverse proxy routing, SSL termination, centralized authentication token validation, rate limiting, and response aggregation, protecting internal topologies.",
            "expected_concepts": ["api gateway", "reverse proxy", "ssl termination", "centralized auth", "edge routing"],
            "sample_questions": [
                "What role does an API Gateway play in microservices architecture compared to a standard reverse proxy like NGINX?",
                "How would you implement rate limiting at the API Gateway level to protect downstream services from cascading failure?",
                "What are the trade-offs of performing authentication token verification at the API Gateway versus inside each individual microservice?"
            ],
            "rubric": {
                "poor": "Cannot explain why an API Gateway is used or confuses it with a relational database.",
                "acceptable": "Explains routing, SSL termination, and centralized authentication as core gateway responsibilities.",
                "excellent": "Thorough system design detailing circuit breaking, backpressure, distributed rate limiting, and zero-trust internal auth tokens."
            },
            "source": "Cloud-Native-Microservice-Patterns"
        },
        {
            "id": "chunk_sd_tech_queues",
            "role_id": "backend_engineer",
            "competency": "system_design",
            "stage": "role_technical",
            "difficulty_level": 3,
            "title": "Asynchronous Message Queues, Worker Pools, and Pub/Sub Backpressure",
            "content": "Core pattern for decoupling ingestion from processing in scalable backend systems. Utilizes message brokers (e.g. RabbitMQ, Kafka, SQS) to buffer bursts of requests. Contrasts point-to-point queues with publish-subscribe topics. Explains consumer worker pool scaling, acknowledgment semantics, dead-letter queues, and backpressure handling.",
            "expected_concepts": ["message queues", "pub sub", "dead letter queue", "consumer worker pool", "backpressure"],
            "sample_questions": [
                "When would you choose an asynchronous message queue over a synchronous HTTP REST call between backend services?",
                "How do you handle consumer failures and poison-pill messages using dead-letter queues and message acknowledgments?",
                "Explain how backpressure mechanisms protect worker pools when message producers publish faster than consumers can process."
            ],
            "rubric": {
                "poor": "Cannot differentiate synchronous REST from asynchronous queue processing.",
                "acceptable": "Describes queue decoupling, worker pools, and why asynchronous buffering prevents request drops.",
                "excellent": "Mastery of consumer scaling, at-least-once vs exactly-once semantics, idempotency, dead-letter queues, and reactive backpressure."
            },
            "source": "Enterprise-Integration-Patterns"
        }
    ]

    existing_ids = {c["id"] for c in chunks}
    for nc in new_chunks:
        if nc["id"] not in existing_ids:
            chunks.append(nc)

    with open(kb_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    total_qs = sum(len(c.get("sample_questions", [])) for c in chunks)
    print(f"Successfully updated KB.")
    print(f"Total chunks: {len(chunks)}")
    print(f"Total usable sample questions: {total_qs}")

if __name__ == "__main__":
    main()
