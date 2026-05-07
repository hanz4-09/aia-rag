import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import load_config
from app.core.logger import write_json_log
from app.rag.generator import ExtractiveGenerator
from app.rag.retriever import VectorRetriever
from app.schemas.request import ChatRequest
from app.schemas.response import ChatResponse
from app.rag.pii import redact_pii
from app.rag.safety import check_safety


router = APIRouter()

config: Dict[str, Any] = load_config()
retriever = VectorRetriever(config)
generator = ExtractiveGenerator()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    redacted_question = redact_pii(request.question)

    safety_result = check_safety(request.question)

    if not safety_result["safe"]:
        total_latency_ms = int((time.time() - start_time) * 1000)

        response = ChatResponse(
            answer=safety_result["message"],
            refused=True,
            refusal_reason=safety_result["reason"],
            sources=[],
            latency_ms=total_latency_ms,
        )

        log_record = {
            "request_id": request_id,
            "session_id": request.session_id,
            "query": redacted_question,
            "retrieval_mode": config["retrieval"]["mode"],
            "reranker_enabled": config["retrieval"].get("enable_reranker", False),
            "top_k": config["retrieval"].get("top_k", 5),
            "retrieved_chunk_ids": [],
            "retrieved_sources": [],
            "retrieval_distances": [],
            "retrieval_latency_ms": 0,
            "generation_latency_ms": 0,
            "total_latency_ms": total_latency_ms,
            "input_tokens": None,
            "output_tokens": None,
            "cache_hit": False,
            "refused": True,
            "refusal_reason": safety_result["reason"],
        }

        write_json_log(config["logging"]["path"], log_record)

        return response

    retrieval_start = time.time()
    # 检索时仍然用原始 question
    # 因为如果用户问题里包含邮箱或编号，有时可能会影响检索。
    retrieved_chunks = retriever.retrieve(request.question)
    retrieval_latency_ms = int((time.time() - retrieval_start) * 1000)

    generation_start = time.time()
    generation_result = generator.generate(
        question=request.question,
        retrieved_chunks=retrieved_chunks,
    )
    generation_latency_ms = int((time.time() - generation_start) * 1000)

    # Redact PII from the final answer as well.
    generation_result["answer"] = redact_pii(generation_result["answer"])

    total_latency_ms = int((time.time() - start_time) * 1000)

    response = ChatResponse(
        answer=generation_result["answer"],
        refused=generation_result["refused"],
        refusal_reason=generation_result["refusal_reason"],
        sources=generation_result["sources"],
        latency_ms=total_latency_ms,
    )

    log_record = {
        "request_id": request_id,
        "session_id": request.session_id,
        "query": redacted_question,  # 写日志时用
        "retrieval_mode": config["retrieval"]["mode"],
        "reranker_enabled": config["retrieval"].get("enable_reranker", False),
        "top_k": config["retrieval"].get("top_k", 5),
        "retrieved_chunk_ids": [
            chunk.get("chunk_id") for chunk in retrieved_chunks
        ],
        "retrieved_sources": [
            chunk.get("metadata", {}).get("filename") for chunk in retrieved_chunks
        ],
        "retrieval_distances": [
            chunk.get("distance") for chunk in retrieved_chunks
        ],
        "retrieval_latency_ms": retrieval_latency_ms,
        "generation_latency_ms": generation_latency_ms,
        "total_latency_ms": total_latency_ms,
        "input_tokens": None,
        "output_tokens": None,
        "cache_hit": False,
        "refused": generation_result["refused"],
        "refusal_reason": generation_result["refusal_reason"],
    }

    write_json_log(config["logging"]["path"], log_record)

    return response