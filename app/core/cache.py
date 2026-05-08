import time
from typing import Any, Dict, Optional


class InMemoryCache:
    """
    Simple in-memory exact-match cache.

    This cache is for MVP/demo purpose only.
    It is not shared across processes and will be cleared when the service restarts.
    """

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.store: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        item = self.store.get(key)

        if not item:
            return None

        created_at = item.get("created_at", 0)
        now = time.time()

        if now - created_at > self.ttl_seconds:
            self.store.pop(key, None)
            return None

        return item.get("value")

    def set(self, key: str, value: Dict[str, Any]) -> None:
        self.store[key] = {
            "created_at": time.time(),
            "value": value,
        }


def build_cache_key(
    question: str,
    retrieval_mode: str,
    reranker_enabled: bool,
    top_k: int,
) -> str:
    normalized_question = question.strip().lower()

    return (
        f"question={normalized_question}|"
        f"mode={retrieval_mode}|"
        f"reranker={reranker_enabled}|"
        f"top_k={top_k}"
    )