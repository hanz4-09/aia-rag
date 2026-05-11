from pathlib import Path
from typing import Any, Dict, List, Tuple

from docx import Document
from pypdf import PdfReader


MIN_EXTRACTED_CHARS_PER_PAGE = 20


def load_txt(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="ignore")


def load_docx(file_path: Path) -> str:
    doc = Document(str(file_path))
    paragraphs = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def load_pdf_with_detection(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    """
    Load text from a PDF and detect pages that may be scanned images.

    This function does not perform OCR. It uses pypdf text extraction and
    records detection metadata so scanned PDFs can be handled gracefully.
    """
    reader = PdfReader(str(file_path))

    pages = []
    pages_with_text = 0
    pages_without_text = 0

    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()

        if len(text) >= MIN_EXTRACTED_CHARS_PER_PAGE:
            pages.append(text)
            pages_with_text += 1
        else:
            pages_without_text += 1

    total_pages = len(reader.pages)
    extracted_text = "\n".join(pages).strip()
    extracted_chars = len(extracted_text)

    scanned_candidate = total_pages > 0 and pages_with_text == 0
    partial_scanned_candidate = total_pages > 0 and pages_without_text > 0

    metadata = {
        "file_type": "pdf",
        "total_pages": total_pages,
        "pages_with_text": pages_with_text,
        "pages_without_text": pages_without_text,
        "extracted_chars": extracted_chars,
        "scanned_pdf_candidate": scanned_candidate,
        "partial_scanned_pdf_candidate": partial_scanned_candidate,
        "ocr_performed": False,
    }

    return extracted_text, metadata


def load_document(file_path: Path) -> Tuple[str, Dict[str, Any]]:
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return load_txt(file_path), {"file_type": "txt"}

    if suffix == ".docx":
        return load_docx(file_path), {"file_type": "docx"}

    if suffix == ".pdf":
        return load_pdf_with_detection(file_path)

    raise ValueError(f"Unsupported file type: {file_path}")


def load_documents_from_directory(
    raw_dir: str = "data/raw",
    return_report: bool = False,
):
    raw_path = Path(raw_dir)

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_path}")

    supported_suffixes = {".txt", ".docx", ".pdf"}
    documents = []

    report: Dict[str, Any] = {
        "raw_dir": str(raw_path),
        "supported_files_seen": 0,
        "loaded_documents": 0,
        "skipped_empty_documents": 0,
        "pdf_detection_results": [],
    }

    for file_path in raw_path.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in supported_suffixes:
            continue

        report["supported_files_seen"] += 1

        text, metadata = load_document(file_path)
        metadata = dict(metadata)
        metadata["source"] = str(file_path)
        metadata["filename"] = file_path.name

        if file_path.suffix.lower() == ".pdf":
            status = "loaded"

            if metadata.get("scanned_pdf_candidate"):
                status = "skipped_no_extractable_text"
            elif metadata.get("partial_scanned_pdf_candidate"):
                status = "loaded_with_scanned_page_warning"

            pdf_result = {
                "filename": file_path.name,
                "source": str(file_path),
                "status": status,
                "total_pages": metadata.get("total_pages"),
                "pages_with_text": metadata.get("pages_with_text"),
                "pages_without_text": metadata.get("pages_without_text"),
                "extracted_chars": metadata.get("extracted_chars"),
                "scanned_pdf_candidate": metadata.get("scanned_pdf_candidate"),
                "partial_scanned_pdf_candidate": metadata.get(
                    "partial_scanned_pdf_candidate"
                ),
                "ocr_performed": False,
            }
            report["pdf_detection_results"].append(pdf_result)

        if text.strip():
            documents.append(
                {
                    "source": str(file_path),
                    "filename": file_path.name,
                    "text": text,
                    "metadata": metadata,
                }
            )
            report["loaded_documents"] += 1
        else:
            report["skipped_empty_documents"] += 1

    if return_report:
        return documents, report

    return documents
