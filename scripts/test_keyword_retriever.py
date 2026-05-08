import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.rag.keyword_retriever import KeywordRetriever


def main():
    config = load_config()
    retriever = KeywordRetriever(config)

    test_queries = [
        "API Key",
        "request_id",
        "audit logging requirements",
        "What endpoints does the AKP Platform provide?",
        "员工病假需要提供什么材料？",
    ]

    for query in test_queries:
        print("\n" + "=" * 100)
        print(f"Query: {query}")
        print("=" * 100)

        results = retriever.retrieve(query)

        if not results:
            print("No keyword results found.")
            continue

        for index, item in enumerate(results, start=1):
            print(f"\nResult #{index}")
            print(f"Chunk ID: {item['chunk_id']}")
            print(f"Keyword Score: {item['keyword_score']}")
            print(f"Source: {item['metadata'].get('filename')}")
            print("-" * 80)
            print(item["text"][:600])


if __name__ == "__main__":
    main()