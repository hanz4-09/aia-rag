import time
from typing import Any, Dict, List

from app.rag.keyword_retriever import KeywordRetriever
from app.rag.retriever import VectorRetriever
from app.rag.reranker import ScoreBasedReranker


class HybridRetriever:
    """
    Hybrid retriever combining vector search and BM25 keyword search.

    Pipeline:
    1. Retrieve candidates from vector retriever.
    2. Retrieve candidates from keyword retriever.
    3. Merge results by chunk_id.
    4. Compute hybrid_score.
    5. Optionally apply reranker if enable_reranker = true.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        retrieval_config = config["retrieval"]

        self.top_k = retrieval_config.get("top_k", 5)
        self.vector_weight = retrieval_config.get("vector_weight", 0.6)
        self.keyword_weight = retrieval_config.get("keyword_weight", 0.4)
        self.enable_reranker = retrieval_config.get("enable_reranker", False)

        self.vector_retriever = VectorRetriever(config)
        self.keyword_retriever = KeywordRetriever(config)

        self.reranker = None
        if self.enable_reranker:
            self.reranker = ScoreBasedReranker(config)

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        vector_results = self.vector_retriever.retrieve(query)
        keyword_results = self.keyword_retriever.retrieve(query)

        merged_results: Dict[str, Dict[str, Any]] = {}

        # Add vector results.
        for rank, item in enumerate(vector_results, start=1):
            chunk_id = item["chunk_id"]

            vector_rank_score = 1.0 / rank

            merged_results[chunk_id] = {
                **item,
                "vector_rank": rank,
                "keyword_rank": None,
                "vector_score": vector_rank_score,
                "keyword_score": 0.0,
                "hybrid_score": self.vector_weight * vector_rank_score,
                "retrieval_source": "vector",
            }

        # Add or merge keyword results.
        for rank, item in enumerate(keyword_results, start=1):
            chunk_id = item["chunk_id"]

            keyword_rank_score = 1.0 / rank

            if chunk_id in merged_results:
                merged_results[chunk_id]["keyword_rank"] = rank
                merged_results[chunk_id]["keyword_score"] = keyword_rank_score
                merged_results[chunk_id]["hybrid_score"] += (
                    self.keyword_weight * keyword_rank_score
                )
                merged_results[chunk_id]["retrieval_source"] = "hybrid"
            else:
                merged_results[chunk_id] = {
                    **item,
                    "distance": None,
                    "vector_rank": None,
                    "keyword_rank": rank,
                    "vector_score": 0.0,
                    "keyword_score": keyword_rank_score,
                    "hybrid_score": self.keyword_weight * keyword_rank_score,
                    "retrieval_source": "keyword",
                }

        sorted_results = sorted(
            merged_results.values(),
            key=lambda item: item["hybrid_score"],
            reverse=True,
        )

        # Keep more candidates before reranking.
        candidate_results = sorted_results

        if self.enable_reranker and self.reranker:
            rerank_start = time.time()
            reranked_results = self.reranker.rerank(query, candidate_results)
            rerank_latency_ms = int((time.time() - rerank_start) * 1000)

            for item in reranked_results:
                item["rerank_latency_ms"] = rerank_latency_ms

            return reranked_results[: self.top_k]

        return candidate_results[: self.top_k]