from typing import Any, Dict, List


class ScoreBasedReranker:
    """
    Lightweight MVP reranker.

    This reranker does not call a cross-encoder model yet.
    It reorders retrieved chunks using existing retrieval signals:
    - hybrid_score
    - keyword_score
    - vector_rank

    Later, this can be replaced by a real cross-encoder reranker.
    """

    def __init__(self, config: Dict[str, Any]):
        retrieval_config = config["retrieval"]

        self.top_k = retrieval_config.get("top_k", 5)

        self.hybrid_score_weight = retrieval_config.get(
            "rerank_hybrid_score_weight", 0.7
        )
        self.keyword_score_weight = retrieval_config.get(
            "rerank_keyword_score_weight", 0.2
        )
        self.vector_rank_weight = retrieval_config.get(
            "rerank_vector_rank_weight", 0.1
        )

    def rerank(self, query: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        reranked_chunks = []

        for chunk in chunks:
            hybrid_score = chunk.get("hybrid_score") or 0.0
            keyword_score = chunk.get("keyword_score") or 0.0
            vector_rank = chunk.get("vector_rank")

            vector_rank_score = 0.0
            if vector_rank:
                vector_rank_score = 1.0 / vector_rank

            reranker_score = (
                self.hybrid_score_weight * hybrid_score
                + self.keyword_score_weight * keyword_score
                + self.vector_rank_weight * vector_rank_score
            )

            updated_chunk = {
                **chunk,
                "reranker_score": reranker_score,
            }

            reranked_chunks.append(updated_chunk)

        reranked_chunks = sorted(
            reranked_chunks,
            key=lambda item: item.get("reranker_score", 0.0),
            reverse=True,
        )

        return reranked_chunks[: self.top_k]