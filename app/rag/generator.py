from typing import Any, Dict, List


class ExtractiveGenerator:
    """
    Temporary generator.

    This generator does not call an LLM.
    It simply formats retrieved chunks into a grounded answer.
    Later, we will replace it with an LLM-based generator.
    """

    def generate(self, question: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not retrieved_chunks:
            return {
                "answer": (
                    "I could not find enough relevant information in the internal "
                    "knowledge base to answer this question."
                ),
                "refused": True,
                "refusal_reason": "NO_RETRIEVED_CONTEXT",
                "sources": [],
            }

        context_parts = []
        sources = []

        for chunk in retrieved_chunks:
            metadata = chunk.get("metadata", {})
            filename = metadata.get("filename", "unknown")
            chunk_id = chunk.get("chunk_id", "unknown")

            context_parts.append(chunk["text"])
            sources.append(
                {
                    "chunk_id": chunk_id,
                    "filename": filename,
                    "source": metadata.get("source"),
                    "distance": chunk.get("distance"),
                    "keyword_score": chunk.get("keyword_score"),
                    "hybrid_score": chunk.get("hybrid_score"),
                    "retrieval_source": chunk.get("retrieval_source"),
                    "vector_rank": chunk.get("vector_rank"),
                    "keyword_rank": chunk.get("keyword_rank"),
                    "reranker_score": chunk.get("reranker_score"),
                }
            )

        answer = (
            "Based on the retrieved internal knowledge, here is the relevant information:\n\n"
            + "\n\n---\n\n".join(context_parts)
        )

        return {
            "answer": answer,
            "refused": False,
            "refusal_reason": None,
            "sources": sources,
        }