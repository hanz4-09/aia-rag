from pathlib import Path
from typing import Any, Dict, List

from chromadb import PersistentClient
from langchain_huggingface import HuggingFaceEmbeddings


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class VectorRetriever:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

        vector_store_config = config["vector_store"]
        retrieval_config = config["retrieval"]

        self.persist_directory = PROJECT_ROOT / vector_store_config["persist_directory"]
        self.collection_name = vector_store_config["collection_name"]
        self.top_k = retrieval_config.get("top_k", 5)
        self.max_distance = retrieval_config.get("max_distance", None)

        embedding_config = config.get("embedding", {})

        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_config.get(
                "model",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            )
        )

        self.client = PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve top-k relevant chunks from Chroma.
        If max_distance is configured, filter out low-confidence results.
        """
        query_embedding = self.embeddings.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=self.top_k,
            include=["documents", "metadatas", "distances"],
        )

        retrieved_chunks = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]

        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances
        ):
            if self.max_distance is not None and distance > self.max_distance:
                continue

            retrieved_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": document,
                    "metadata": metadata,
                    "distance": distance,
                }
            )

        return retrieved_chunks
