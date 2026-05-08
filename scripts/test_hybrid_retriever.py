import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.rag.hybrid_retriever import HybridRetriever


def main():
    config = load_config()
    retriever = HybridRetriever(config)

    test_queries = [
        "What is the annual leave policy?",
        "员工病假需要提供什么材料？",
        "What are the audit logging requirements?",
        "API Key 泄露后应该怎么处理？",
        "What endpoints does the AKP Platform provide?",
        "AKP Platform 的核心模块有哪些？",
    ]

    for query in test_queries:
        print("\n" + "=" * 100)
        print(f"Query: {query}")
        print("=" * 100)

        results = retriever.retrieve(query)

        if not results:
            print("No hybrid results found.")
            continue

        for index, item in enumerate(results, start=1):
            print(f"\nResult #{index}")
            print(f"Chunk ID: {item.get('chunk_id')}")
            print(f"Source: {item.get('metadata', {}).get('filename')}")
            print(f"Retrieval Source: {item.get('retrieval_source')}")
            print(f"Vector Rank: {item.get('vector_rank')}")
            print(f"Keyword Rank: {item.get('keyword_rank')}")
            print(f"Hybrid Score: {item.get('hybrid_score')}")
            print(f"Distance: {item.get('distance')}")
            print("-" * 80)
            print(item.get("text", "")[:600])


if __name__ == "__main__":
    main()