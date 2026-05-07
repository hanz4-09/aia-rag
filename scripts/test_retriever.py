import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.rag.retriever import VectorRetriever


def main():
    config = load_config()
    retriever = VectorRetriever(config)

    query = "What is the annual leave policy?"

    print(f"Query: {query}")
    print("=" * 80)

    results = retriever.retrieve(query)

    if not results:
        print("No results found.")
        return

    for index, item in enumerate(results, start=1):
        print(f"\nResult #{index}")
        print(f"Chunk ID: {item['chunk_id']}")
        print(f"Distance: {item['distance']}")
        print(f"Source: {item['metadata'].get('filename')}")
        print("-" * 80)
        print(item["text"])


if __name__ == "__main__":
    main()