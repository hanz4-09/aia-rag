import json
from typing import Any, Dict, List

from langchain_text_splitters import RecursiveCharacterTextSplitter


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


def split_documents(
    documents: List[Dict],
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> List[Dict]:
    """
    Split loaded documents into smaller chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )

    chunks = []

    for doc in documents:
        text_chunks = splitter.split_text(doc["text"])
        document_metadata = doc.get("metadata", {})

        for index, chunk_text in enumerate(text_chunks):
            chunk_id = f"{doc['filename']}_chunk_{index}"

            metadata = {
                "source": doc["source"],
                "filename": doc["filename"],
                "chunk_index": index,
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

    return chunks
