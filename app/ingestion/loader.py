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


def _configure_tesseract(ocr_config: Dict[str, Any]) -> None:
    tesseract_cmd = ocr_config.get("tesseract_cmd")

    if not tesseract_cmd:
        return

    try:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    except Exception:
        return


def _is_ocr_available(ocr_config: Dict[str, Any]) -> Tuple[bool, str | None]:
    if not ocr_config.get("enabled", False):
        return False, "OCR disabled by config."

    try:
        import fitz  # PyMuPDF  # noqa: F401
        import pytesseract
        from PIL import Image  # noqa: F401
    except Exception as exc:
        return False, f"OCR Python dependencies unavailable: {exc}"

    _configure_tesseract(ocr_config)

    try:
        version = pytesseract.get_tesseract_version()
        return True, f"Tesseract available: {version}"
    except Exception as exc:
        return False, f"Tesseract executable unavailable: {exc}"


def _ocr_pdf_page(
    file_path: Path,
    page_index: int,
    ocr_config: Dict[str, Any],
) -> str:
    import fitz
    import pytesseract
    from PIL import Image

    render_dpi = int(ocr_config.get("render_dpi", 220))
    language = ocr_config.get("language", "eng")

    zoom = render_dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    with fitz.open(str(file_path)) as doc:
        page = doc.load_page(page_index)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)

    image = Image.frombytes(
        "RGB",
        [pixmap.width, pixmap.height],
        pixmap.samples,
    )

    text = pytesseract.image_to_string(image, lang=language) or ""
    return text.strip()


def load_pdf_with_detection(
    file_path: Path,
    ocr_config: Dict[str, Any] | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Load text from PDF.

    Behavior:
    - First use pypdf text extraction.
    - If a page has no/low extractable text and OCR is enabled,
      render the page and run Tesseract OCR.
    - Record page-level detection and OCR metadata.
    """
    ocr_config = ocr_config or {}
    reader = PdfReader(str(file_path))

    ocr_available, ocr_status = _is_ocr_available(ocr_config)

    pages = []
    page_results = []

    pages_with_text = 0
    pages_without_text = 0
    pages_ocr_attempted = 0
    pages_ocr_succeeded = 0

    min_ocr_chars = int(ocr_config.get("min_ocr_chars", 10))

    for page_index, page in enumerate(reader.pages):
        extracted_text = (page.extract_text() or "").strip()
        extraction_method = "pypdf"
        ocr_text = ""
        ocr_error = None
        ocr_performed = False

        has_text_layer = len(extracted_text) >= MIN_EXTRACTED_CHARS_PER_PAGE

        if has_text_layer:
            pages.append(extracted_text)
            pages_with_text += 1
        else:
            pages_without_text += 1

            if ocr_available:
                pages_ocr_attempted += 1
                ocr_performed = True

                try:
                    ocr_text = _ocr_pdf_page(
                        file_path=file_path,
                        page_index=page_index,
                        ocr_config=ocr_config,
                    )
                except Exception as exc:
                    ocr_error = str(exc)
                    ocr_text = ""

                if len(ocr_text.strip()) >= min_ocr_chars:
                    extraction_method = "ocr"
                    pages.append(ocr_text.strip())
                    pages_ocr_succeeded += 1

        page_results.append(
            {
                "page_index": page_index,
                "has_text_layer": has_text_layer,
                "pypdf_chars": len(extracted_text),
                "ocr_performed": ocr_performed,
                "ocr_chars": len(ocr_text.strip()),
                "ocr_error": ocr_error,
                "extraction_method": extraction_method,
            }
        )

    total_pages = len(reader.pages)
    extracted_text = "\n".join(pages).strip()
    extracted_chars = len(extracted_text)

    scanned_candidate = total_pages > 0 and pages_with_text == 0
    partial_scanned_candidate = total_pages > 0 and pages_without_text > 0
    ocr_performed_any = pages_ocr_attempted > 0
    ocr_succeeded = pages_ocr_succeeded > 0

    metadata = {
        "file_type": "pdf",
        "total_pages": total_pages,
        "pages_with_text": pages_with_text,
        "pages_without_text": pages_without_text,
        "extracted_chars": extracted_chars,
        "scanned_pdf_candidate": scanned_candidate,
        "partial_scanned_pdf_candidate": partial_scanned_candidate,
        "ocr_enabled": bool(ocr_config.get("enabled", False)),
        "ocr_available": ocr_available,
        "ocr_status": ocr_status,
        "ocr_performed": ocr_performed_any,
        "ocr_succeeded": ocr_succeeded,
        "pages_ocr_attempted": pages_ocr_attempted,
        "pages_ocr_succeeded": pages_ocr_succeeded,
        "page_results": page_results,
    }

    return extracted_text, metadata


def load_document(
    file_path: Path,
    ocr_config: Dict[str, Any] | None = None,
) -> Tuple[str, Dict[str, Any]]:
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return load_txt(file_path), {"file_type": "txt"}

    if suffix == ".docx":
        return load_docx(file_path), {"file_type": "docx"}

    if suffix == ".pdf":
        return load_pdf_with_detection(file_path, ocr_config=ocr_config)

    raise ValueError(f"Unsupported file type: {file_path}")


def load_documents_from_directory(
    raw_dir: str = "data/raw",
    return_report: bool = False,
    ocr_config: Dict[str, Any] | None = None,
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

        text, metadata = load_document(file_path, ocr_config=ocr_config)
        metadata = dict(metadata)
        metadata["source"] = str(file_path)
        metadata["filename"] = file_path.name

        if file_path.suffix.lower() == ".pdf":
            status = "loaded"

            if metadata.get("ocr_succeeded"):
                status = "loaded_with_ocr"
            elif metadata.get("scanned_pdf_candidate") and not text.strip():
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
                "ocr_enabled": metadata.get("ocr_enabled"),
                "ocr_available": metadata.get("ocr_available"),
                "ocr_status": metadata.get("ocr_status"),
                "ocr_performed": metadata.get("ocr_performed"),
                "ocr_succeeded": metadata.get("ocr_succeeded"),
                "pages_ocr_attempted": metadata.get("pages_ocr_attempted"),
                "pages_ocr_succeeded": metadata.get("pages_ocr_succeeded"),
                "page_results": metadata.get("page_results"),
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
