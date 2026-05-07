import sys
from pathlib import Path

from chromadb import PersistentClient
# from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.ingestion.loader import load_documents_from_directory
from app.ingestion.chunker import split_documents


def main():
    config = load_config()

    raw_dir = PROJECT_ROOT / "data" / "raw"

    print("Loading documents...")
    documents = load_documents_from_directory(str(raw_dir))
    print(f"Loaded documents: {len(documents)}")

    if not documents:
        print("No documents found. Please put .txt, .docx, or .pdf files into data/raw.")
        return

    print("Splitting documents into chunks...")
    chunks = split_documents(documents)
    print(f"Generated chunks: {len(chunks)}")

    embedding_config = config["embedding"]
    vector_store_config = config["vector_store"]

    # embeddings = OpenAIEmbeddings(
    #     model=embedding_config["model"],
    #     api_key=config["openai_api_key"],
    # )

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    persist_directory = PROJECT_ROOT / vector_store_config["persist_directory"]
    collection_name = vector_store_config["collection_name"]

    client = PersistentClient(path=str(persist_directory))
    collection = client.get_or_create_collection(name=collection_name)

    print("Generating embeddings and writing to Chroma...")

    ids = []
    texts = []
    metadatas = []
    vectors = []

    for chunk in chunks:
        ids.append(chunk["chunk_id"])
        texts.append(chunk["text"])
        metadatas.append(chunk["metadata"])

    vectors = embeddings.embed_documents(texts)

    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=vectors,
    )

    print("Ingestion completed.")
    print(f"Persist directory: {persist_directory}")
    print(f"Collection name: {collection_name}")
    print(f"Total chunks stored: {collection.count()}")


if __name__ == "__main__":
    main()