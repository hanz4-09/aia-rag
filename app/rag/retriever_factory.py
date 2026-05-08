from typing import Any, Dict

from app.rag.hybrid_retriever import HybridRetriever
from app.rag.retriever import VectorRetriever


def create_retriever(config: Dict[str, Any]):
    retrieval_mode = config["retrieval"].get("mode", "vector").lower()

    if retrieval_mode == "vector":
        return VectorRetriever(config)

    if retrieval_mode == "hybrid":
        return HybridRetriever(config)

    raise ValueError(f"Unsupported retrieval mode: {retrieval_mode}")