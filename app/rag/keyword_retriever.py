import re
from pathlib import Path
from typing import Any, Dict, List

from chromadb import PersistentClient
from rank_bm25 import BM25Okapi


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def tokenize(text: str) -> List[str]:
    """
    Simple tokenizer for English + technical keywords + basic Chinese characters.

    This is a lightweight MVP tokenizer.
    Later we can improve it with jieba or a production search engine.
    """
    if not text:
        return []

    text = text.lower()

    # Keep English words, numbers, technical tokens, and Chinese characters.
    tokens = re.findall(r"[a-zA-Z0-9_/\.-]+|[\u4e00-\u9fff]", text)

    return tokens


class KeywordRetriever:
    """
    BM25-based keyword retriever.

    It loads all chunks from Chroma and builds an in-memory BM25 index.
    This is suitable for the MVP / case study scale.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        vector_store_config = config["vector_store"]
        retrieval_config = config["retrieval"]

        self.persist_directory = PROJECT_ROOT / vector_store_config["persist_directory"]
        self.collection_name = vector_store_config["collection_name"]
        self.top_k = retrieval_config.get("top_k", 5)

        self.client = PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )

        self.chunk_ids: List[str] = []
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self.bm25 = None

        self._build_index()

    def _build_index(self) -> None:
        """
        Load all chunks from Chroma and build BM25 index.
        """
        total_count = self.collection.count()

        if total_count == 0:
            self.bm25 = BM25Okapi([[]])
            return

        results = self.collection.get(
            include=["documents", "metadatas"]
        )

        self.chunk_ids = results.get("ids", [])
        self.documents = results.get("documents", [])
        self.metadatas = results.get("metadatas", [])

        tokenized_documents = [tokenize(doc) for doc in self.documents]

        self.bm25 = BM25Okapi(tokenized_documents)

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve top-k chunks using BM25 keyword search.
        """
        if not self.documents or self.bm25 is None:
            return []

        query_tokens = tokenize(query)

        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )

        retrieved_chunks = []

        for index in ranked_indices[: self.top_k]:
            score = float(scores[index])

            if score <= 0:
                continue

            retrieved_chunks.append(
                {
                    "chunk_id": self.chunk_ids[index],
                    "text": self.documents[index],
                    "metadata": self.metadatas[index],
                    "keyword_score": score,
                }
            )

        return retrieved_chunks