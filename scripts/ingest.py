import json
import sys
from pathlib import Path
from typing import Any, Dict

from chromadb import PersistentClient
from langchain_huggingface import HuggingFaceEmbeddings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.ingestion.chunker import split_documents
from app.ingestion.loader import load_documents_from_directory


def write_scanned_pdf_detection_report(report: Dict[str, Any]) -> None:
    report_dir = PROJECT_ROOT / "reports" / "ingestion"
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / "scanned_pdf_detection_report.json"
    md_path = report_dir / "scanned_pdf_detection_report.md"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    pdf_results = report.get("pdf_detection_results", [])
    scanned_candidates = [
        item for item in pdf_results if item.get("scanned_pdf_candidate")
    ]
    partial_candidates = [
        item for item in pdf_results if item.get("partial_scanned_pdf_candidate")
    ]

    lines = [
        "# Scanned PDF Detection Report",
        "",
        "Project: AIA RAG Case Study Service",
        "Report Type: Ingestion Diagnostics",
        "",
        "## Summary",
        "",
        f"- Supported files seen: {report.get('supported_files_seen', 0)}",
        f"- Loaded documents: {report.get('loaded_documents', 0)}",
        f"- Skipped empty documents: {report.get('skipped_empty_documents', 0)}",
        f"- PDF files checked: {len(pdf_results)}",
        f"- Scanned PDF candidates: {len(scanned_candidates)}",
        f"- Partial scanned PDF candidates: {len(partial_candidates)}",
        "",
        "## Notes",
        "",
        "- OCR is not performed in the current implementation.",
        "- Text-based PDFs are loaded using pypdf text extraction.",
        "- PDFs with no extractable text are detected and skipped gracefully.",
        "- PDFs with some low-text pages are loaded with a warning.",
        "",
        "## PDF Details",
        "",
    ]

    if not pdf_results:
        lines.append("No PDF files were found during ingestion.")
    else:
        for item in pdf_results:
            lines.extend(
                [
                    f"### {item.get('filename')}",
                    "",
                    f"- Status: {item.get('status')}",
                    f"- Total pages: {item.get('total_pages')}",
                    f"- Pages with text: {item.get('pages_with_text')}",
                    f"- Pages without text: {item.get('pages_without_text')}",
                    f"- Extracted characters: {item.get('extracted_chars')}",
                    f"- Scanned PDF candidate: {item.get('scanned_pdf_candidate')}",
                    "- OCR performed: False",
                    "",
                ]
            )

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Scanned PDF detection JSON report: {json_path}")
    print(f"Scanned PDF detection Markdown report: {md_path}")


def main():
    config = load_config()

    raw_dir = PROJECT_ROOT / "data" / "raw"

    print("Loading documents...")
    documents, ingestion_report = load_documents_from_directory(
        str(raw_dir),
        return_report=True,
    )

    write_scanned_pdf_detection_report(ingestion_report)

    print(f"Loaded documents: {len(documents)}")

    if not documents:
        print("No documents found.")
        print("Please put .txt, .docx, or text-based .pdf files into data/raw.")
        return

    print("Splitting documents into chunks...")
    chunks = split_documents(documents)
    print(f"Generated chunks: {len(chunks)}")

    vector_store_config = config["vector_store"]

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
