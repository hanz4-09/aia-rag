from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Source(BaseModel):
    chunk_id: str
    filename: str
    source: Optional[str] = None
    distance: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    refused: bool
    refusal_reason: Optional[str] = None
    sources: List[Source]
    latency_ms: int