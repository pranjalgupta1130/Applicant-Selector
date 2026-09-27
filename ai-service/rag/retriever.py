"""
RAG Retrieval Engine for BoardRoom AI.
Upgraded to dense semantic embeddings (SentenceTransformer) with local cosine similarity
and deterministic TF-IDF lexical fallback.
Conforms to Hackathon Master Plan Section 6.2 and Post-Audit Priority 1.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as tfidf_cosine_similarity

from core.schemas import KnowledgeChunk, RetrievalResult, RetrievalResponse, RubricCriteria

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """
    Two-Tier Retrieval Engine:
      Primary: Dense Semantic Embeddings (all-MiniLM-L6-v2) + Metadata Filtering + Cosine Similarity
      Fallback: Sublinear TF-IDF + N-Grams Lexical Matcher
    All vector indexing is kept in-process for speed, determinism, and zero external DB overhead.
    """

    def __init__(self, knowledge_path: Optional[str] = None, use_embeddings: bool = True):
        if knowledge_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.knowledge_path = base_dir / "data" / "knowledge_base" / "seed_knowledge.json"
        else:
            self.knowledge_path = Path(knowledge_path)

        self.use_embeddings = use_embeddings
        self.chunks: List[KnowledgeChunk] = []
        self.corpus_texts: List[str] = []

        # Dense Embedding Index
        self.embed_model = None
        self.dense_embeddings: Optional[np.ndarray] = None
        self.dense_available: bool = False

        # Lexical TF-IDF Fallback Index
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_vectors = None

        self._load_and_index()

    def _load_and_index(self):
        """Loads knowledge base JSON and builds both dense and lexical indices."""
        if not self.knowledge_path.exists():
            raise FileNotFoundError(f"Knowledge base file not found at: {self.knowledge_path}")

        with open(self.knowledge_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.chunks = [KnowledgeChunk(**item) for item in raw_data]

        # Prepare rich text representations for indexing
        self.corpus_texts = []
        for c in self.chunks:
            doc_text = (
                f"{c.title}. Domain: {getattr(c, 'domain', 'cyber_computing')}. "
                f"Role: {c.role_id}. Competency: {c.competency}. Stage: {c.stage}. Difficulty: {c.difficulty_level}. "
                f"{c.content} "
                f"Key concepts: {' '.join(c.expected_concepts)}. "
                f"Questions: {' '.join(c.sample_questions)}"
            )
            self.corpus_texts.append(doc_text)

        # 1. Build Lexical TF-IDF Fallback Index
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
            lowercase=True
        )
        self.tfidf_vectors = self.tfidf_vectorizer.fit_transform(self.corpus_texts)

        # 2. Build Dense Embedding Index
        if self.use_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                # Try cached local model first, fallback to standard load if not locally cached
                try:
                    self.embed_model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
                except Exception:
                    self.embed_model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=False)

                # Compute and normalize dense chunk embeddings
                self.dense_embeddings = self.embed_model.encode(
                    self.corpus_texts,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                self.dense_available = True
                logger.info(f"Initialized Dense Embedding Index with {len(self.chunks)} chunks.")
            except Exception as e:
                logger.warning(f"Dense embedding initialization skipped or failed: {e}. Defaulting to lexical fallback.")
                self.dense_available = False
        else:
            self.dense_available = False

        # Loud Startup Diagnostic
        status_banner = self.get_status_banner()
        logger.info("\n" + status_banner)

    def get_status_banner(self) -> str:
        """Returns the formatted, loud RAG status diagnostic banner."""
        mode_str = "DENSE" if self.dense_embeddings_active else "TF-IDF FALLBACK"
        dense_str = "ACTIVE" if self.dense_embeddings_active else "INACTIVE"
        model_str = "all-MiniLM-L6-v2" if self.dense_embeddings_active else "unavailable"
        return (
            "========================================\n"
            "RAG STATUS\n"
            f"Embedding model: {model_str}\n"
            f"Mode: {mode_str}\n"
            f"Dense retrieval: {dense_str}\n"
            f"KB chunks: {len(self.chunks)}\n"
            "========================================"
        )

    def get_status_dict(self) -> Dict[str, Any]:
        """Returns structured diagnostic status dictionary."""
        return {
            "embedding_model": "all-MiniLM-L6-v2" if self.dense_embeddings_active else "unavailable",
            "retrieval_mode": self.retrieval_mode,
            "mode_display": "DENSE" if self.dense_embeddings_active else "TF-IDF FALLBACK",
            "dense_embeddings_active": self.dense_embeddings_active,
            "kb_chunks": len(self.chunks)
        }

    @property
    def dense_embeddings_active(self) -> bool:
        """Returns True if local dense SentenceTransformer embeddings are active and loaded."""
        return bool(self.dense_available and self.dense_embeddings is not None)

    @property
    def retrieval_mode(self) -> str:
        """Returns 'dense' if SentenceTransformer embeddings are active, otherwise 'tfidf'."""
        return "dense" if self.dense_embeddings_active else "tfidf"

    def retrieve(
        self,
        query: str,
        role_id: Optional[str] = None,
        competency: Optional[str] = None,
        stage: Optional[str] = None,
        difficulty: Optional[int] = None,
        top_k: int = 3,
        force_fallback: bool = False,
        domain: Optional[str] = None,
        prohibited_domains: Optional[List[str]] = None
    ) -> RetrievalResponse:
        """
        Executes query retrieval:
        1. Strict domain boundary resolution and metadata pre-filtering with domain-confined relaxation
        2. Semantic similarity scoring (Dense embeddings primary, TF-IDF fallback)
        3. Cosine similarity ranking + difficulty/stage proximity adjustments
        4. Ranked top-k results with full metadata, domain tags, expected concepts, and rubrics
        """
        if not self.chunks:
            return RetrievalResponse(query=query, total_found=0, results=[])

        # Step 0: Resolve domain boundary
        resolved_domain = domain
        if not resolved_domain:
            if role_id and any(token in role_id.lower() for token in ("ece", "radar", "drdo", "scientist")):
                resolved_domain = "electronics_radar"
            elif role_id and any(token in role_id.lower() for token in ("backend", "fullstack", "software", "sde")):
                resolved_domain = "cyber_computing"
            elif competency and competency in ("embedded_realtime_systems", "digital_signal_processing", "radar_rf_systems", "avionics_communication"):
                resolved_domain = "electronics_radar"
            elif competency and competency in ("backend", "database", "system_design", "cs_fundamentals"):
                resolved_domain = "cyber_computing"

        # Step 1: Metadata Pre-Filtering within strict domain boundary
        candidate_indices, was_relaxed = self._filter_with_relaxation(
            role_id=role_id,
            competency=competency,
            stage=stage,
            difficulty=difficulty,
            domain=resolved_domain,
            prohibited_domains=prohibited_domains
        )

        if not candidate_indices:
            # Explicit no-grounded-context condition: strictly prevent cross-domain contamination
            return RetrievalResponse(query=query, total_found=0, results=[])

        query_clean = query.strip()
        if not query_clean:
            # Empty query: return candidate chunks in default order
            ranked_indices = candidate_indices[:top_k]
            scores = [1.0] * len(ranked_indices)
        else:
            # Step 2: Scoring (Dense vs Fallback)
            if self.dense_available and not force_fallback:
                ranked_indices, scores = self._rank_dense(query_clean, candidate_indices, stage, difficulty, top_k)
            else:
                ranked_indices, scores = self._rank_lexical(query_clean, candidate_indices, stage, difficulty, top_k)

        # Step 3: Format Retrieval Results
        results = []
        for idx, score in zip(ranked_indices, scores):
            c = self.chunks[idx]
            results.append(RetrievalResult(
                chunk_id=c.id,
                title=c.title,
                competency=c.competency,
                stage=c.stage,
                difficulty_level=c.difficulty_level,
                score=round(float(score), 4),
                content=c.content,
                expected_concepts=c.expected_concepts,
                rubric=c.rubric,
                source=c.source,
                domain=getattr(c, "domain", "cyber_computing"),
                source_title=getattr(c, "source_title", None),
                source_reference=getattr(c, "source_reference", None)
            ))

        return RetrievalResponse(
            query=query,
            total_found=len(results),
            results=results
        )

    def _rank_dense(
        self,
        query: str,
        candidate_indices: List[int],
        target_stage: Optional[str],
        target_difficulty: Optional[int],
        top_k: int
    ) -> Tuple[List[int], List[float]]:
        """Ranks candidate chunks using dense embedding dot product (cosine similarity)."""
        q_emb = self.embed_model.encode([query], normalize_embeddings=True)[0]
        sub_embs = self.dense_embeddings[candidate_indices]
        # Cosine similarity between normalized query and normalized candidates
        sims = np.dot(sub_embs, q_emb)

        paired = []
        for idx, score in zip(candidate_indices, sims):
            chunk = self.chunks[idx]
            boost = 0.0
            if target_difficulty and chunk.difficulty_level == target_difficulty:
                boost += 0.04
            if target_stage and chunk.stage == target_stage:
                boost += 0.04
            paired.append((idx, float(score) + boost))

        paired.sort(key=lambda x: x[1], reverse=True)
        top_pairs = paired[:top_k]
        return [p[0] for p in top_pairs], [p[1] for p in top_pairs]

    def _rank_lexical(
        self,
        query: str,
        candidate_indices: List[int],
        target_stage: Optional[str],
        target_difficulty: Optional[int],
        top_k: int
    ) -> Tuple[List[int], List[float]]:
        """Fallback ranking using TF-IDF vectorizer and cosine similarity."""
        q_vec = self.tfidf_vectorizer.transform([query])
        sub_vectors = self.tfidf_vectors[candidate_indices]
        sims = tfidf_cosine_similarity(q_vec, sub_vectors)[0]

        paired = []
        for idx, score in zip(candidate_indices, sims):
            chunk = self.chunks[idx]
            boost = 0.0
            if target_difficulty and chunk.difficulty_level == target_difficulty:
                boost += 0.04
            if target_stage and chunk.stage == target_stage:
                boost += 0.04
            paired.append((idx, float(score) + boost))

        paired.sort(key=lambda x: x[1], reverse=True)
        top_pairs = paired[:top_k]
        return [p[0] for p in top_pairs], [p[1] for p in top_pairs]

    def _filter_with_relaxation(
        self,
        role_id: Optional[str],
        competency: Optional[str],
        stage: Optional[str],
        difficulty: Optional[int],
        domain: Optional[str] = None,
        prohibited_domains: Optional[List[str]] = None
    ) -> Tuple[List[int], bool]:
        """
        Filters indices with domain boundary isolation.
        Progressively relaxes constraints (difficulty -> stage -> competency -> role)
        strictly INSIDE the target domain. Never contaminates cross-domain.
        """
        # 1. Exact match across all supplied metadata
        exact = self._filter_indices(role_id, competency, stage, difficulty, domain, prohibited_domains)
        if exact:
            return exact, False

        # 2. Relax difficulty (match role, competency, stage)
        rel_diff = self._filter_indices(role_id, competency, stage, None, domain, prohibited_domains)
        if rel_diff:
            return rel_diff, True

        # 3. Relax stage (match role, competency)
        rel_stage = self._filter_indices(role_id, competency, None, None, domain, prohibited_domains)
        if rel_stage:
            return rel_stage, True

        # 4. Relax competency (match role)
        rel_role = self._filter_indices(role_id, None, None, None, domain, prohibited_domains)
        if rel_role:
            return rel_role, True

        # 5. Domain-only relaxation (if domain specified, stay strictly within domain)
        if domain:
            rel_domain = self._filter_indices(None, None, None, None, domain, prohibited_domains)
            if rel_domain:
                return rel_domain, True
            return [], True

        # 6. Global fallback only if NO domain constraint exists
        allowed_all = []
        for i, c in enumerate(self.chunks):
            c_domain = getattr(c, "domain", "cyber_computing")
            if prohibited_domains and c_domain in prohibited_domains:
                continue
            allowed_all.append(i)
        return allowed_all, True

    def _filter_indices(
        self,
        role_id: Optional[str],
        competency: Optional[str],
        stage: Optional[str],
        difficulty: Optional[int],
        domain: Optional[str] = None,
        prohibited_domains: Optional[List[str]] = None
    ) -> List[int]:
        """Applies strict metadata and domain boundary matching."""
        matches = []
        for i, c in enumerate(self.chunks):
            c_domain = getattr(c, "domain", "cyber_computing")
            if prohibited_domains and c_domain in prohibited_domains:
                continue
            if domain and c_domain != domain:
                continue
            if role_id and c.role_id != role_id:
                continue
            if competency:
                comp_norm = competency.lower().replace("-", "_").replace(" ", "_")
                chunk_comp_norm = c.competency.lower().replace("-", "_").replace(" ", "_")
                if comp_norm not in chunk_comp_norm and chunk_comp_norm not in comp_norm:
                    continue
            if stage and c.stage != stage:
                continue
            if difficulty is not None and c.difficulty_level != difficulty:
                continue
            matches.append(i)
        return matches

    def get_chunk_by_id(self, chunk_id: str) -> Optional[KnowledgeChunk]:
        """Direct lookup by chunk id."""
        for c in self.chunks:
            if c.id == chunk_id:
                return c
        return None
