from typing import List, Optional

from pydantic import BaseModel


class Source(BaseModel):
    chunk_id: str
    filename: str
    source: Optional[str] = None

    # Vector retrieval field
    distance: Optional[float] = None

    # Hybrid retrieval explanation fields
    keyword_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    retrieval_source: Optional[str] = None
    vector_rank: Optional[int] = None
    keyword_rank: Optional[int] = None

    # Reranker field
    reranker_score: Optional[float] = None

    # Context assembly field
    used_in_context: Optional[bool] = None


class ChatResponse(BaseModel):
    answer: str
    refused: bool
    refusal_reason: Optional[str] = None
    sources: List[Source]
    latency_ms: int