import logging
from typing import List, Dict, Any, Tuple
from config import config

logger = logging.getLogger(__name__)

class ReRanker:
    @staticmethod
    def rerank_and_threshold(
        candidates: List[Dict[str, Any]],
        top_k_context: int = config.TOP_K_CONTEXT,
        min_relevance_score: float = config.MIN_RELEVANCE_SCORE
    ) -> Tuple[List[Dict[str, Any]], float, bool]:
        """
        Filters and re-ranks retrieved candidates against relevance threshold.
        Returns:
            - selected_candidates: List of top documents
            - confidence: Normalized confidence score [0.0, 1.0]
            - has_relevant_context: Boolean flag indicating if threshold was met
        """
        if not candidates:
            return [], 0.0, False

        # Filter out candidates below relevance threshold
        filtered = [c for c in candidates if c["rank_score"] >= min_relevance_score]

        if not filtered:
            # Check if top candidate is close or purely low confidence
            top_score = candidates[0]["rank_score"]
            logger.info(f"Reranker: Top candidate score ({top_score:.2f}) is below min threshold ({min_relevance_score}).")
            return [], 0.0, False

        # Select top K context chunks
        selected = filtered[:top_k_context]
        top_score = selected[0]["rank_score"]

        # Normalize confidence to [0.0, 1.0] range (score 15+ maps to 0.95+)
        confidence = min(round(top_score / (top_score + 10.0) * 1.5, 2), 0.99)

        return selected, confidence, True

reranker = ReRanker()
