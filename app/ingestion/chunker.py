import json
import re
from typing import Any, Dict, List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter


CHUNKING_STRATEGY = "heading_aware_recursive"


def _sanitize_metadata_value(value: Any) -> Any:
    """
    Chroma metadata supports only primitive values or simple primitive lists.

    Nested dict/list metadata such as page-level OCR results must be converted
    to JSON strings before writing to Chroma.
    """
    if value is None:
        return ""

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, list):
        if all(isinstance(item, str) for item in value):
            return value
        if all(isinstance(item, int) for item in value):
            return value
        if all(isinstance(item, float) for item in value):
            return value
        if all(isinstance(item, bool) for item in value):
            return value

        return json.dumps(value, ensure_ascii=False)

    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: _sanitize_metadata_value(value)
        for key, value in metadata.items()
    }


def _is_markdown_heading(line: str) -> bool:
    return bool(re.match(r"^\s{0,3}#{1,6}\s+\S+", line))


def _is_numbered_heading(line: str) -> bool:
    """
    Match only explicit chapter-style headings.

    Avoid treating normal numbered list items such as
    "1. xxx", "2、xxx", or "1.1 xxx" as section headings,
    because policy documents often use numbered lists for
    required fields, procedures, and examples.
    """
    stripped = line.strip()

    patterns = [
        r"^第[一二三四五六七八九十\d]+[章节条]\s*\S+",
    ]

    return any(re.match(pattern, stripped) for pattern in patterns)


def _is_heading(line: str) -> bool:
    stripped = line.strip()

    if not stripped:
        return False

    if len(stripped) > 120:
        return False

    return _is_markdown_heading(stripped) or _is_numbered_heading(stripped)


def _normalize_heading(line: str) -> str:
    heading = line.strip()

    # Markdown heading: "## Title" -> "Title"
    heading = re.sub(r"^\s{0,3}#{1,6}\s+", "", heading)

    return heading.strip()


def _split_by_headings(text: str) -> List[Dict[str, Any]]:
    """
    Split text into heading-aware sections.

    Each section keeps its nearest heading as section_title. If the document
    does not contain headings, the full document is returned as a single section.
    """
    lines = text.splitlines()

    sections: List[Dict[str, Any]] = []
    current_title = ""
    current_lines: List[str] = []
    section_index = 0

    def flush_section() -> None:
        nonlocal section_index, current_lines, current_title

        section_text = "\n".join(current_lines).strip()
        if not section_text:
            current_lines = []
            return

        sections.append(
            {
                "section_index": section_index,
                "section_title": current_title,
                "text": section_text,
            }
        )
        section_index += 1
        current_lines = []

    for line in lines:
        if _is_heading(line):
            flush_section()
            current_title = _normalize_heading(line)
            current_lines = [line]
        else:
            current_lines.append(line)

    flush_section()

    if not sections and text.strip():
        sections.append(
            {
                "section_index": 0,
                "section_title": "",
                "text": text.strip(),
            }
        )

    return sections


def _create_recursive_splitter(
    chunk_size: int,
    chunk_overlap: int,
) -> RecursiveCharacterTextSplitter:
    """
    Recursive splitter with separators ordered from stronger semantic boundaries
    to weaker fallback boundaries.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            "。",   # Chinese sentence boundary
            "！",
            "？",
            ". ",
            "! ",
            "? ",
            "; ",
            "；",
            "，",
            ", ",
            " ",
            "",
        ],
    )


def _split_section_text(
    section_text: str,
    splitter: RecursiveCharacterTextSplitter,
) -> List[str]:
    """
    Split a section into chunks. The recursive splitter still handles oversized
    sections, but heading boundaries are preserved before this step.
    """
    text = section_text.strip()
    if not text:
        return []

    return [
        chunk.strip()
        for chunk in splitter.split_text(text)
        if chunk and chunk.strip()
    ]


def _build_chunk_id(filename: str, chunk_index: int) -> str:
    return f"{filename}_chunk_{chunk_index}"


def split_documents(
    documents: List[Dict],
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> List[Dict]:
    """
    Split loaded documents into chunks using heading-aware recursive chunking.

    Strategy:
    1. Split documents by headings when headings are available.
    2. Split each section with RecursiveCharacterTextSplitter.
    3. Preserve document and section metadata for retrieval and source tracing.

    This keeps the existing output contract:
    [
        {
            "chunk_id": "...",
            "text": "...",
            "metadata": {...}
        }
    ]
    """
    splitter = _create_recursive_splitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks: List[Dict[str, Any]] = []

    for doc in documents:
        text = doc.get("text", "")
        if not text or not text.strip():
            continue

        filename = doc["filename"]
        source = doc["source"]
        document_metadata = doc.get("metadata", {})

        sections = _split_by_headings(text)
        chunk_index = 0

        for section in sections:
            section_index = section["section_index"]
            section_title = section.get("section_title", "")
            section_text = section["text"]

            text_chunks = _split_section_text(section_text, splitter)

            for section_chunk_index, chunk_text in enumerate(text_chunks):
                if section_title and section_title not in chunk_text[:120]:
                    chunk_text = f"{section_title}\n{chunk_text}"

                chunk_id = _build_chunk_id(filename, chunk_index)

                metadata = {
                    "source": source,
                    "filename": filename,
                    "chunk_index": chunk_index,
                    "section_index": section_index,
                    "section_chunk_index": section_chunk_index,
                    "section_title": section_title,
                    "chunking_strategy": CHUNKING_STRATEGY,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                }

                metadata.update(document_metadata)
                metadata = _sanitize_metadata(metadata)

                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "text": chunk_text,
                        "metadata": metadata,
                    }
                )

                chunk_index += 1

    return chunks