# 负责读取 .txt .docx .pdf
# 暂不支持扫描pdf
from pathlib import Path
from typing import Dict, List

from docx import Document
from pypdf import PdfReader


def load_txt(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8", errors="ignore")


def load_docx(file_path: Path) -> str:
    doc = Document(str(file_path))
    paragraphs = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            paragraphs.append(text)

    return "\n".join(paragraphs)


def load_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())

    return "\n".join(pages)


def load_document(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return load_txt(file_path)

    if suffix == ".docx":
        return load_docx(file_path)

    if suffix == ".pdf":
        return load_pdf(file_path)

    raise ValueError(f"Unsupported file type: {file_path}")


def load_documents_from_directory(raw_dir: str = "data/raw") -> List[Dict]:
    raw_path = Path(raw_dir)

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_path}")

    supported_suffixes = {".txt", ".docx", ".pdf"}
    documents = []

    for file_path in raw_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in supported_suffixes:
            text = load_document(file_path)

            if text.strip():
                documents.append(
                    {
                        "source": str(file_path),
                        "filename": file_path.name,
                        "text": text,
                    }
                )

    return documents