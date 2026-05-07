# 负责把长文档切成小段
from typing import Dict, List

from langchain_text_splitters import RecursiveCharacterTextSplitter


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

        for index, chunk_text in enumerate(text_chunks):
            chunk_id = f"{doc['filename']}_chunk_{index}"

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "source": doc["source"],
                        "filename": doc["filename"],
                        "chunk_index": index,
                    },
                }
            )

    return chunks