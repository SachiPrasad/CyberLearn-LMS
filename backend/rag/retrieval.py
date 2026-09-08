import math
import logging
from typing import List, Dict, Any, Optional
from knowledge.ingestion import kb_pipeline, DocumentMetadata
from rag.query_processor import QueryProcessor

logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self):
        self.pipeline = kb_pipeline

    def _compute_semantic_score(self, query_tokens: List[str], doc_idx: int) -> float:
        """Computes cosine similarity between query TF-IDF vector and document vector."""
        if doc_idx >= len(self.pipeline.doc_vectors):
            return 0.0

        doc_vec = self.pipeline.doc_vectors[doc_idx]
        
        # Build query vector
        query_tf: Dict[str, float] = {}
        for t in query_tokens:
            query_tf[t] = query_tf.get(t, 0) + 1.0

        q_vec: Dict[str, float] = {}
        norm_sq = 0.0
        for term, count in query_tf.items():
            idf = self.pipeline.idf.get(term, 1.0)
            val = count * idf
            q_vec[term] = val
            norm_sq += val ** 2

        q_norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        unit_q_vec = {k: v / q_norm for k, v in q_vec.items()}

        # Dot product of unit vectors = cosine similarity (range [0.0, 1.0])
        score = 0.0
        for term, weight in unit_q_vec.items():
            if term in doc_vec:
                score += weight * doc_vec[term]

        return score

    def _compute_lexical_score(self, query: str, query_tokens: List[str], phrases: List[str], doc: Dict[str, Any]) -> float:
        """Calculates tiered lexical match score based on field weights and exact phrase matches."""
        score = 0.0
        q_lower = query.lower()

        title_lower = doc["title"].lower()
        course_lower = doc["course_name"].lower()
        module_lower = doc["module_name"].lower()
        content_lower = doc["content"].lower()
        keywords_lower = [k.lower() for k in doc.get("keywords", [])]

        # 1. Exact title or course match
        if course_lower in q_lower or title_lower in q_lower:
            score += 15.0

        # 2. Phrase matching (2-grams and 3-grams)
        for phrase in phrases:
            if len(phrase) > 4:
                if phrase in title_lower or phrase in module_lower:
                    score += 10.0
                elif phrase in content_lower:
                    score += 6.0
                elif any(phrase in kw for kw in keywords_lower):
                    score += 8.0

        # 3. Exact keyword match
        for kw in keywords_lower:
            if kw in q_lower:
                score += 5.0

        # 4. Token overlap
        matched_tokens = 0
        for token in query_tokens:
            if len(token) > 2:
                if token in title_lower or token in module_lower:
                    score += 3.0
                    matched_tokens += 1
                elif any(token in kw for kw in keywords_lower):
                    score += 2.0
                    matched_tokens += 1
                elif token in content_lower:
                    score += 1.0
                    matched_tokens += 1

        if matched_tokens > 0:
            score += (matched_tokens / max(len(query_tokens), 1)) * 4.0

        return score

    def retrieve(
        self,
        query: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
        top_k: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval combining lexical and semantic scores.
        Returns top candidate documents with detailed scoring metadata.
        """
        docs = self.pipeline.get_all_documents()
        if not docs:
            return []

        tokens, phrases = QueryProcessor.extract_keywords_and_phrases(query)
        candidates = []

        for idx, doc in enumerate(docs):
            # Apply metadata filters if specified
            if filter_metadata:
                if "course_id" in filter_metadata and doc.get("course_id") != filter_metadata["course_id"]:
                    continue
                if "document_type" in filter_metadata and doc.get("document_type") != filter_metadata["document_type"]:
                    continue

            lexical_score = self._compute_lexical_score(query, tokens, phrases, doc)
            semantic_score = self._compute_semantic_score(tokens, idx)

            # Hybrid Score Fusion: weighted combination of lexical (60%) and semantic cosine (40% scaled)
            hybrid_score = lexical_score + (semantic_score * 20.0)

            candidates.append({
                "document": doc,
                "lexical_score": lexical_score,
                "semantic_score": semantic_score,
                "hybrid_score": hybrid_score,
                "rank_score": hybrid_score
            })

        # Sort descending by hybrid rank score
        candidates.sort(key=lambda x: x["rank_score"], reverse=True)
        return candidates[:top_k]

# Global singleton
hybrid_retriever = HybridRetriever()
