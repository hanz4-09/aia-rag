import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.rag.retriever_factory import create_retriever


def main():
    config = load_config()
    retriever = create_retriever(config)

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "What is the annual leave policy?"

    results = retriever.retrieve(query)

    print(f"Query: {query}")
    print("=" * 80)

    if not results:
        print("No results found.")
        return

    for index, result in enumerate(results, start=1):
        metadata = result.get("metadata", {})
        filename = metadata.get("filename", "unknown")
        chunk_id = result.get("chunk_id", "unknown")
        distance = result.get("distance")
        retrieval_source = result.get("retrieval_source")
        keyword_score = result.get("keyword_score")
        hybrid_score = result.get("hybrid_score")
        reranker_score = result.get("reranker_score")
        vector_rank = result.get("vector_rank")
        keyword_rank = result.get("keyword_rank")
        text = result.get("text", "")

        print()
        print(f"Result #{index}")
        print(f"Chunk ID: {chunk_id}")
        print(f"Source: {filename}")
        print(f"Distance: {distance}")
        print(f"Retrieval Source: {retrieval_source}")
        print(f"Keyword Score: {keyword_score}")
        print(f"Hybrid Score: {hybrid_score}")
        print(f"Reranker Score: {reranker_score}")
        print(f"Vector Rank: {vector_rank}")
        print(f"Keyword Rank: {keyword_rank}")
        print("-" * 80)
        print(text[:1000])


if __name__ == "__main__":
    main()