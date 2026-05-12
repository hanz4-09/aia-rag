import json
import sys
from pathlib import Path
from typing import Any, Dict

from chromadb import PersistentClient
from langchain_huggingface import HuggingFaceEmbeddings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.ingestion.secrets_scanner import scan_directory, write_scan_reports
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
    ocr_performed = [
        item for item in pdf_results if item.get("ocr_performed")
    ]
    ocr_succeeded = [
        item for item in pdf_results if item.get("ocr_succeeded")
    ]

    lines = [
        "# PDF Detection and OCR Report",
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
        f"- PDFs with OCR performed: {len(ocr_performed)}",
        f"- PDFs with OCR succeeded: {len(ocr_succeeded)}",
        "",
        "## Notes",
        "",
        "- Text-based PDFs are loaded using pypdf text extraction.",
        "- Scanned/no-text PDF pages can be rendered and processed by OCR when OCR is enabled and Tesseract is available.",
        "- OCR result availability depends on local Tesseract installation and configured language data.",
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
                    f"- OCR enabled: {item.get('ocr_enabled')}",
                    f"- OCR available: {item.get('ocr_available')}",
                    f"- OCR performed: {item.get('ocr_performed')}",
                    f"- OCR succeeded: {item.get('ocr_succeeded')}",
                    f"- Pages OCR attempted: {item.get('pages_ocr_attempted')}",
                    f"- Pages OCR succeeded: {item.get('pages_ocr_succeeded')}",
                    f"- OCR status: {item.get('ocr_status')}",
                    "",
                ]
            )

            page_results = item.get("page_results") or []
            if page_results:
                lines.append("Page-level results:")
                lines.append("")
                for page in page_results:
                    lines.append(
                        "- Page {page_index}: method={method}, "
                        "pypdf_chars={pypdf_chars}, "
                        "ocr_performed={ocr_performed}, "
                        "ocr_chars={ocr_chars}, "
                        "ocr_error={ocr_error}".format(
                            page_index=page.get("page_index"),
                            method=page.get("extraction_method"),
                            pypdf_chars=page.get("pypdf_chars"),
                            ocr_performed=page.get("ocr_performed"),
                            ocr_chars=page.get("ocr_chars"),
                            ocr_error=page.get("ocr_error"),
                        )
                    )
                lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"PDF detection/OCR JSON report: {json_path}")
    print(f"PDF detection/OCR Markdown report: {md_path}")



def run_secrets_scan(config: dict) -> dict:
    scan_config = config.get("secrets_scan", {})
    enabled = scan_config.get("enabled", True)

    raw_dir = config.get("data", {}).get("raw_dir", "data/raw")
    report_dir = Path("reports") / "ingestion"
    json_path = report_dir / "secrets_scan_report.json"
    markdown_path = report_dir / "secrets_scan_report.md"

    if not enabled:
        report = {
            "root_dir": raw_dir,
            "scanned_files": 0,
            "skipped_files": 0,
            "findings_count": 0,
            "high_severity_count": 0,
            "medium_severity_count": 0,
            "findings": [],
            "enabled": False,
        }
        write_scan_reports(report, json_path, markdown_path)
        return report

    supported_suffixes = scan_config.get("supported_suffixes")
    report = scan_directory(raw_dir, supported_suffixes=supported_suffixes)
    report["enabled"] = True

    write_scan_reports(report, json_path, markdown_path)

    print(f"Secrets scan JSON report: {json_path.resolve()}")
    print(f"Secrets scan Markdown report: {markdown_path.resolve()}")
    print(f"Secrets scan findings: {report['findings_count']}")

    if scan_config.get("fail_on_detected", False) and report["findings_count"] > 0:
        raise RuntimeError(
            "Secrets scan detected secret-like patterns before ingestion. "
            "Review reports/ingestion/secrets_scan_report.md."
        )

    return report


def main():
    config = load_config()

    run_secrets_scan(config)

    raw_dir = PROJECT_ROOT / "data" / "raw"

    print("Loading documents...")
    documents, ingestion_report = load_documents_from_directory(
        str(raw_dir),
        return_report=True,
        ocr_config=config.get("ocr", {}),
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
    embedding_config = config.get("embedding", {})

    embeddings = HuggingFaceEmbeddings(
        model_name=embedding_config.get(
            "model",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        )
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
