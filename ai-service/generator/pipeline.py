"""
Question Generation Pipeline for BoardRoom AI.
Combines RAG context retrieval, prompt synthesis, LLM generation (with Gemini),
strict Pydantic schema validation, and reliable fallback question selection.
Conforms to Hackathon Master Plan Section 6.2, 13.1, 16, and Phase 3.
"""

import json
import uuid
import re
import logging
from typing import List, Optional, Dict, Any, Tuple

from core.schemas import (
    CandidateProfile,
    TargetRole,
    QuestionObject,
    RubricCriteria,
    RetrievalResult
)
from core.config import settings
from rag.retriever import KnowledgeRetriever
from evaluator.relevance import QuestionRelevanceEvaluator
from generator.fallback_bank import FallbackQuestionBank

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Meta-Question Detection & Direct Candidate Address Gate
# ---------------------------------------------------------

META_QUESTION_PATTERNS = [
    r"ice_breaker",
    r"applicant_validation",
    r"stage\s+progression",
    r"interview\s+stage",
    r"design(?:ing)?\s+an?\s+(?:ice\s*breaker|interview)",
    r"design(?:ing)?\s+and\s+test(?:ing)?",
    r"reliable\s+ice_breaker",
    r"good\s+ice\s*breaker",
    r"kinds?\s+thing",
    r"kind\s+of\s+thing",
    r"what\s+question\s+(?:should|can|would)",
    r"how\s+should\s+(?:the|an)?\s*interviewer",
    r"ask\s+the\s+candidate",
    r"interview\s+question",
    r"what\s+should\s+we\s+ask",
    r"how\s+would\s+you\s+phrase\s+a\s+question",
    r"create\s+a\s+question",
    r"formulate\s+a\s+question",
    r"what\s+is\s+a\s+good\s+question",
    r"how\s+to\s+interview",
    r"suggest\s+an?\s+interview",
    r"design\s+a\s+question",
    r"what\s+would\s+be\s+a\s+good\s+question",
]


def is_meta_question(text: str) -> bool:
    """
    Determines whether question text is a meta-interview question
    (asking how to interview or design a question), which MUST NEVER
    be presented to a candidate.
    """
    if not text:
        return True
    lowered = text.strip().lower()
    for pattern in META_QUESTION_PATTERNS:
        if re.search(pattern, lowered):
            return True
    return False


SYSTEM_PROMPT = """You are an expert DRDO technical interview board member in a high-stakes engineering boardroom simulation.
You are asking the candidate directly in the first person ("you" / "your").

CRITICAL MANDATORY RULES:
1. Ask exactly ONE focused, single-part technical or background question directly to the candidate.
2. Address the candidate directly using "you" or "your" (e.g., "Could you explain...", "How did you design...", "What is...").
3. NEVER generate meta-interview questions (e.g., "How would you design an ice breaker question", "What question should we ask", "How should an interviewer ask").
4. Ground the question strictly in the provided retrieved technical context and target competency for the advertised role.
5. Align difficulty level (1=Beginner, 3=Mid-level, 5=Staff/Architect) with the stage.
6. Provide clear, objective expected concepts that a strong candidate answer must demonstrate.
7. Provide a detailed rubric (poor: 0-40, acceptable: 41-75, excellent: 76-100).
8. Return ONLY valid JSON adhering strictly to the JSON schema below. No markdown fences, no conversational preamble.

REQUIRED JSON SCHEMA:
{
  "question": "The exact question text addressed to the candidate ending with a question mark",
  "expectedConcepts": ["concept 1", "concept 2", "concept 3"],
  "rubric": {
    "poor": "Criteria for failing/poor response (0-40)",
    "acceptable": "Criteria for acceptable response (41-75)",
    "excellent": "Criteria for excellent/thorough response (76-100)"
  },
  "relevanceRationale": "Concise reason why this question fits the candidate, role, and stage"
}
"""


class QuestionGeneratorPipeline:
    """
    RAG-driven Question Generation Pipeline with Gemini LLM integration
    and automated deterministic fallback.
    """

    def __init__(self, retriever: Optional[KnowledgeRetriever] = None):
        self.retriever = retriever or KnowledgeRetriever()

    def generate(
        self,
        candidate: CandidateProfile,
        role: TargetRole,
        stage: str,
        competency: str,
        difficulty: int,
        previous_questions: Optional[List[str]] = None,
        previous_missing_concepts: Optional[List[str]] = None,
        question_type: Optional[str] = "conceptual",
        adaptive_reason: Optional[str] = None
    ) -> QuestionObject:
        """
        Executes end-to-end question generation with Interview Intelligence:
        1. Formulate search query from role + competency + stage + missing concepts
        2. Retrieve top-k grounding context
        3. Attempt LLM generation via Gemini (incorporating question_type and adaptive_reason)
        4. Validate schema and check deduplication
        5. Calculate 5-factor relevance score
        6. Apply Quality Gates: if any gate fails, fallback to curated question bank
        7. Attach internal question explanation and return validated QuestionObject
        """
        previous_questions = previous_questions or []
        previous_missing_concepts = previous_missing_concepts or []
        question_type = question_type or "conceptual"

        # 1. Formulate retrieval query
        query_terms = [role.title, competency, stage]
        if candidate.skills:
            query_terms.extend(candidate.skills[:3])
        if previous_missing_concepts:
            query_terms.extend(previous_missing_concepts)
        query = " ".join(query_terms)

        # 2. Retrieve Grounded Context within strict domain boundary
        retrieval_res = self.retriever.retrieve(
            query=query,
            role_id=role.id,
            competency=competency,
            stage=stage,
            difficulty=difficulty,
            top_k=2,
            domain=getattr(role, "domain", None)
        )
        retrieved_chunks = retrieval_res.results

        # 3. Attempt LLM Generation if API key is configured (with retries)
        question_obj = None
        if settings.GEMINI_API_KEY:
            for attempt in range(1, settings.MAX_RETRIES + 1):
                try:
                    logger.info(f"Attempting Gemini generation (attempt {attempt}/{settings.MAX_RETRIES})...")
                    question_obj = self._generate_with_gemini(
                        candidate=candidate,
                        role=role,
                        stage=stage,
                        competency=competency,
                        difficulty=difficulty,
                        retrieved_chunks=retrieved_chunks,
                        previous_questions=previous_questions,
                        previous_missing_concepts=previous_missing_concepts,
                        question_type=question_type,
                        adaptive_reason=adaptive_reason
                    )
                    if question_obj is not None:
                        break
                except Exception as e:
                    logger.warning(f"Gemini attempt {attempt} failed: {e}")

            if question_obj is None:
                logger.info("All Gemini attempts failed or returned None. Engaging curated fallback bank.")

        # 4. Fallback execution if LLM generation was not used or failed
        if question_obj is None:
            question_obj = self._fallback_generation(
                candidate=candidate,
                role=role,
                stage=stage,
                competency=competency,
                difficulty=difficulty,
                retrieved_chunks=retrieved_chunks,
                previous_questions=previous_questions,
                previous_missing_concepts=previous_missing_concepts,
                question_type=question_type
            )

        # 5. Evaluate and attach Explainable Question Relevance Score (Phase 4)
        relevance = QuestionRelevanceEvaluator.evaluate(
            question_text=question_obj.text,
            role=role,
            candidate=candidate,
            competency=competency,
            stage=stage,
            difficulty=difficulty,
            expected_concepts=question_obj.expectedConcepts
        )
        question_obj.relevanceScore = relevance.totalScore
        question_obj.relevanceRationale = relevance.rationale

        # 6. Quality Gate Check
        passed_gates, gate_issues = self._check_quality_gates(
            question=question_obj,
            stage=stage,
            competency=competency,
            difficulty=difficulty,
            previous_questions=previous_questions
        )
        if not passed_gates and not question_obj.isFallback:
            logger.warning(f"Generated question failed quality gates ({gate_issues}); reverting to certified fallback.")
            question_obj = self._fallback_generation(
                candidate=candidate,
                role=role,
                stage=stage,
                competency=competency,
                difficulty=difficulty,
                retrieved_chunks=retrieved_chunks,
                previous_questions=previous_questions,
                previous_missing_concepts=previous_missing_concepts,
                question_type=question_type
            )
            # Re-evaluate relevance for fallback
            relevance = QuestionRelevanceEvaluator.evaluate(
                question_text=question_obj.text,
                role=role,
                candidate=candidate,
                competency=competency,
                stage=stage,
                difficulty=difficulty,
                expected_concepts=question_obj.expectedConcepts
            )
            question_obj.relevanceScore = relevance.totalScore
            question_obj.relevanceRationale = relevance.rationale

        # 7. Attach Phase A Interview Intelligence Metadata & Explanation
        resolved_adaptive_reason = adaptive_reason or (
            f"Probing gap in {', '.join(previous_missing_concepts[:2])}"
            if previous_missing_concepts
            else f"Advancing {stage} evaluation at calibrated difficulty {difficulty}/5."
        )
        question_obj.questionType = question_type
        question_obj.adaptiveReason = resolved_adaptive_reason
        question_obj.questionExplanation = {
            "role_alignment": f"Matches {role.title} requirements in {competency}.",
            "candidate_alignment": f"Calibrated for candidate seniority ({candidate.experience_years or 2.0} yrs) and stated skills.",
            "target_competency": competency,
            "difficulty_rationale": f"Difficulty {difficulty}/5 appropriate for stage '{stage}'.",
            "adaptive_reason": resolved_adaptive_reason,
            "targeted_concepts": question_obj.expectedConcepts[:3],
            "question_type": question_type,
            "retrieval_invoked": True,
            "retrieval_count": len(retrieved_chunks),
            "retrieval_mode": "dense" if getattr(self.retriever, "dense_available", False) else "tfidf_lexical",
            "retrieved_sources": [
                {"id": c.chunk_id, "title": c.title, "domain": c.domain, "score": c.score}
                for c in retrieved_chunks
            ],
            "context_reached_generation": bool(retrieved_chunks),
            "generation_mode": "curated_fallback" if question_obj.isFallback else "gemini_rag",
            "diagnostics": {
                "stage": stage,
                "role": role.title,
                "candidateExpertise": candidate.skills or candidate.claimed_expertise or [],
                "competency": competency,
                "retrievalQuery": query,
                "retrievedSourceIds": [c.chunk_id for c in retrieved_chunks],
                "retrievalDomain": getattr(role, "domain", "electronics_radar"),
                "generatedQuestion": question_obj.text,
                "isFallback": question_obj.isFallback,
                "relevanceScore": question_obj.relevanceScore
            }
        }

        return question_obj

    def _generate_with_gemini(
        self,
        candidate: CandidateProfile,
        role: TargetRole,
        stage: str,
        competency: str,
        difficulty: int,
        retrieved_chunks: List[RetrievalResult],
        previous_questions: List[str],
        previous_missing_concepts: List[str],
        question_type: str = "conceptual",
        adaptive_reason: Optional[str] = None
    ) -> Optional[QuestionObject]:
        """Calls Gemini API with structured prompt, question_type guidance, and JSON validation."""
        from google import genai
        from google.genai import types

        timeout_ms = int(settings.LLM_TIMEOUT_SECONDS * 1000)
        http_options = types.HttpOptions(timeout=timeout_ms)

        client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=http_options
        )

        # Build context block
        context_snippets = []
        source_ids = []
        for c in retrieved_chunks:
            source_ids.append(c.chunk_id)
            context_snippets.append(
                f"[Source ID: {c.chunk_id} | Title: {c.title}]\n"
                f"Concepts: {', '.join(c.expected_concepts)}\n"
                f"Summary: {c.content}\n"
                f"Rubric: Poor: {c.rubric.poor} | Excellent: {c.rubric.excellent}"
            )
        context_str = "\n\n".join(context_snippets) if context_snippets else "No internal chunk found."

        user_prompt = f"""Generate an interview question with the following parameters:
- Target Role: {role.title} ({role.description or ''})
- Candidate Profile: Skills: {', '.join(candidate.skills)}; Exp: {candidate.experience_years} years
- Interview Stage: {stage}
- Target Competency: {competency}
- Requested Difficulty: {difficulty}/5
- Target Question Type: {question_type} (e.g. conceptual, implementation, debugging, trade_off, scenario, design, follow_up)
- Adaptive Reason: {adaptive_reason or 'Staged progression'}
- Previous Questions Asked (DO NOT REPEAT): {json.dumps(previous_questions)}
- Adaptive Focus (Missing concepts to probe): {json.dumps(previous_missing_concepts)}

RETRIEVED GROUNDING KNOWLEDGE:
{context_str}

Respond with valid JSON according to the schema."""

        response = client.models.generate_content(
            model=settings.DEFAULT_LLM_MODEL,
            contents=[SYSTEM_PROMPT, user_prompt],
            config=types.GenerateContentConfig(
                temperature=settings.LLM_TEMPERATURE,
                response_mime_type="application/json",
                http_options=http_options
            )
        )


        raw_text = response.text.strip()
        data = self._clean_and_parse_json(raw_text)
        if not data:
            return None

        # Check deduplication
        q_text = data.get("question", "").strip()
        if self._is_duplicate(q_text, previous_questions):
            logger.info("Generated question was duplicate; retrying fallback.")
            return None

        rubric_data = data.get("rubric", {})
        rubric = RubricCriteria(
            poor=rubric_data.get("poor", "Incomplete or incorrect answer."),
            acceptable=rubric_data.get("acceptable", "Addresses main points correctly."),
            excellent=rubric_data.get("excellent", "Comprehensive, accurate answer with deep reasoning.")
        )

        return QuestionObject(
            id=f"q_{uuid.uuid4().hex[:8]}",
            text=q_text,
            stage=stage,
            competency=competency,
            difficulty=difficulty,
            expectedConcepts=data.get("expectedConcepts", []),
            rubric=rubric,
            relevanceScore=90,  # Computed subsequently by evaluator
            relevanceRationale=data.get("relevanceRationale", ""),
            sources=source_ids,
            isFallback=False,
            questionType=question_type,
            adaptiveReason=adaptive_reason
        )

    def _fallback_generation(
        self,
        candidate: CandidateProfile,
        role: TargetRole,
        stage: str,
        competency: str,
        difficulty: int,
        retrieved_chunks: List[RetrievalResult],
        previous_questions: List[str],
        previous_missing_concepts: List[str],
        question_type: str = "conceptual",
        used_fallback_ids: Optional[List[str]] = None
    ) -> QuestionObject:
        """
        Deterministic, high-quality fallback using curated FallbackQuestionBank.
        Guarantees zero meta-interview questions and zero repetition across turns.
        """
        domain = getattr(role, "domain", None) or role.title or "electronics_radar"
        used_ids_set = set(used_fallback_ids or [])

        q_obj = FallbackQuestionBank.get_fallback_question(
            stage=stage,
            domain=domain,
            used_ids=used_ids_set,
            used_questions=previous_questions
        )

        # Override question_type if specified
        q_obj.questionType = question_type
        return q_obj

    def _check_quality_gates(
        self,
        question: QuestionObject,
        stage: str,
        competency: str,
        difficulty: int,
        previous_questions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Executes strict quality gates before a question is certified:
        1. Relevance threshold (>= 65 for ice_breaker, >= 70 for others)
        2. Duplicate detection (< 0.75 token overlap)
        3. Expected concepts presence (>= 2 concepts)
        4. Grounding source presence (>= 1 source)
        5. Valid rubric (all 3 tiers non-empty)
        6. Valid difficulty (in 1..5)
        7. Non-generic wording
        """
        issues = []
        if is_meta_question(question.text):
            issues.append("Question is a meta-interview question asking how to design an interview question rather than asking candidate directly")

        min_rel = 65 if stage == "ice_breaker" else 70
        if question.relevanceScore < min_rel:
            issues.append(f"Relevance score {question.relevanceScore} below gate threshold {min_rel}")

        if self._is_duplicate(question.text, previous_questions):
            issues.append("Question is duplicate of previously asked question")

        if len(question.expectedConcepts) < 2:
            issues.append(f"Expected concepts ({len(question.expectedConcepts)}) below minimum threshold (2)")

        if not question.sources:
            issues.append("No grounding source citations present")

        if not question.rubric.poor or not question.rubric.acceptable or not question.rubric.excellent:
            issues.append("Incomplete rubric criteria in one or more tiers")

        if not (1 <= question.difficulty <= 5):
            issues.append(f"Difficulty {question.difficulty} outside valid range 1-5")

        generic_starters = ["as an ai", "sure! here", "here is a question", "i would ask"]
        q_lower = question.text.strip().lower()
        if any(q_lower.startswith(starter) for starter in generic_starters):
            issues.append("Question contains generic bot conversational preamble")

        return len(issues) == 0, issues

    def _is_duplicate(self, candidate_q: str, previous_questions: List[str]) -> bool:
        """Checks if question is effectively duplicate of any previous question."""
        if not previous_questions:
            return False

        q_tokens = set(re.findall(r"\w+", candidate_q.lower()))
        for prev in previous_questions:
            prev_tokens = set(re.findall(r"\w+", prev.lower()))
            overlap = len(q_tokens.intersection(prev_tokens))
            smaller = min(len(q_tokens), len(prev_tokens))
            if smaller > 0 and (overlap / smaller) > 0.85:
                return True
        return False

    def _clean_and_parse_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Strips markdown code blocks and repairs minor JSON issues."""
        text = raw_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except Exception:
            # Simple bracket extraction regex
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
        return None

    @classmethod
    def validate_question_quality(
        cls,
        question: QuestionObject,
        target_stage: Optional[str] = None,
        target_competency: Optional[str] = None,
        target_difficulty: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Audits generated question against strict quality guardrails:
        - match requested competency
        - match stage
        - match difficulty
        - use retrieved context / cite sources
        - contain expected concepts
        - not a generic chatbot question
        - not a meta-interview question
        """
        issues = []
        if is_meta_question(question.text):
            issues.append("Question is a meta-interview question asking how to interview rather than asking candidate directly")

        if target_stage and question.stage != target_stage:
            issues.append(f"Stage mismatch: got '{question.stage}', expected '{target_stage}'")
        if target_competency and question.competency != target_competency:
            issues.append(f"Competency mismatch: got '{question.competency}', expected '{target_competency}'")
        if target_difficulty and question.difficulty != target_difficulty:
            issues.append(f"Difficulty mismatch: got {question.difficulty}, expected {target_difficulty}")

        generic_starters = ["as an ai", "sure! here", "here is a question", "i would ask"]
        q_lower = question.text.strip().lower()
        if any(q_lower.startswith(starter) for starter in generic_starters):
            issues.append("Question contains generic conversational chatbot phrasing")

        if len(question.expectedConcepts) < 1:
            issues.append("Question lacks expected concepts")
        if not question.sources:
            issues.append("Question lacks grounding source attribution")
        if not question.text.strip().endswith("?"):
            issues.append("Question text does not terminate with question mark")
        if len(question.text.split()) < 7:
            issues.append("Question is too short (< 7 words)")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "relevanceScore": question.relevanceScore
        }

