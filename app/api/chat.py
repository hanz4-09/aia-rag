import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter

from app.core.cache import InMemoryCache, build_cache_key
from app.core.config import load_config
from app.core.logger import write_json_log
from app.rag.generator import ExtractiveGenerator
from app.rag.pii import redact_pii
from app.rag.retriever_factory import create_retriever
from app.rag.safety import check_safety
from app.schemas.request import ChatRequest
from app.schemas.response import ChatResponse


router = APIRouter()

config: Dict[str, Any] = load_config()
retriever = create_retriever(config)
generator = ExtractiveGenerator()

cache_config = config.get("cache", {})
cache_enabled = cache_config.get("enabled", False)
cache = InMemoryCache(ttl_seconds=cache_config.get("ttl_seconds", 300))


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
            "retrieval_sources": [],
            "keyword_scores": [],
            "hybrid_scores": [],
            "vector_ranks": [],
            "keyword_ranks": [],
            "reranker_scores": [],
            "rerank_latency_ms": 0,
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

    cache_hit = False
    cache_key = build_cache_key(
        question=request.question,
        retrieval_mode=config["retrieval"]["mode"],
        reranker_enabled=config["retrieval"].get("enable_reranker", False),
        top_k=config["retrieval"].get("top_k", 5),
    )

    if cache_enabled:
        cached_response = cache.get(cache_key)

        if cached_response:
            total_latency_ms = int((time.time() - start_time) * 1000)
            cache_hit = True

            response = ChatResponse(
                answer=cached_response["answer"],
                refused=cached_response["refused"],
                refusal_reason=cached_response["refusal_reason"],
                sources=cached_response["sources"],
                latency_ms=total_latency_ms,
            )

            log_record = {
                "request_id": request_id,
                "session_id": request.session_id,
                "query": redacted_question,
                "retrieval_mode": config["retrieval"]["mode"],
                "reranker_enabled": config["retrieval"].get("enable_reranker", False),
                "top_k": config["retrieval"].get("top_k", 5),
                "retrieved_chunk_ids": [
                    source.get("chunk_id") for source in cached_response["sources"]
                ],
                "retrieved_sources": [
                    source.get("filename") for source in cached_response["sources"]
                ],
                "retrieval_distances": [
                    source.get("distance") for source in cached_response["sources"]
                ],
                "retrieval_sources": [
                    source.get("retrieval_source")
                    for source in cached_response["sources"]
                ],
                "keyword_scores": [
                    source.get("keyword_score") for source in cached_response["sources"]
                ],
                "hybrid_scores": [
                    source.get("hybrid_score") for source in cached_response["sources"]
                ],
                "vector_ranks": [
                    source.get("vector_rank") for source in cached_response["sources"]
                ],
                "keyword_ranks": [
                    source.get("keyword_rank") for source in cached_response["sources"]
                ],
                "reranker_scores": [
                    source.get("reranker_score")
                    for source in cached_response["sources"]
                ],
                "rerank_latency_ms": 0,
                "retrieval_latency_ms": 0,
                "generation_latency_ms": 0,
                "total_latency_ms": total_latency_ms,
                "input_tokens": None,
                "output_tokens": None,
                "cache_hit": cache_hit,
                "refused": cached_response["refused"],
                "refusal_reason": cached_response["refusal_reason"],
            }

            write_json_log(config["logging"]["path"], log_record)

            return response

    retrieval_start = time.time()
    retrieved_chunks = retriever.retrieve(request.question)
    retrieval_latency_ms = int((time.time() - retrieval_start) * 1000)

    generation_start = time.time()
    generation_result = generator.generate(
        question=request.question,
        retrieved_chunks=retrieved_chunks,
    )
    generation_latency_ms = int((time.time() - generation_start) * 1000)

    generation_result["answer"] = redact_pii(generation_result["answer"])

    total_latency_ms = int((time.time() - start_time) * 1000)

    response = ChatResponse(
        answer=generation_result["answer"],
        refused=generation_result["refused"],
        refusal_reason=generation_result["refusal_reason"],
        sources=generation_result["sources"],
        latency_ms=total_latency_ms,
    )

    if cache_enabled and not generation_result["refused"]:
        cache.set(
            cache_key,
            {
                "answer": generation_result["answer"],
                "refused": generation_result["refused"],
                "refusal_reason": generation_result["refusal_reason"],
                "sources": generation_result["sources"],
            },
        )

    log_record = {
        "request_id": request_id,
        "session_id": request.session_id,
        "query": redacted_question,
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
        "retrieval_sources": [
            chunk.get("retrieval_source") for chunk in retrieved_chunks
        ],
        "keyword_scores": [
            chunk.get("keyword_score") for chunk in retrieved_chunks
        ],
        "hybrid_scores": [
            chunk.get("hybrid_score") for chunk in retrieved_chunks
        ],
        "vector_ranks": [
            chunk.get("vector_rank") for chunk in retrieved_chunks
        ],
        "keyword_ranks": [
            chunk.get("keyword_rank") for chunk in retrieved_chunks
        ],
        "reranker_scores": [
            chunk.get("reranker_score") for chunk in retrieved_chunks
        ],
        "rerank_latency_ms": (
            retrieved_chunks[0].get("rerank_latency_ms")
            if retrieved_chunks and retrieved_chunks[0].get("rerank_latency_ms") is not None
            else 0
        ),
        "retrieval_latency_ms": retrieval_latency_ms,
        "generation_latency_ms": generation_latency_ms,
        "total_latency_ms": total_latency_ms,
        "input_tokens": None,
        "output_tokens": None,
        "cache_hit": cache_hit,
        "refused": generation_result["refused"],
        "refusal_reason": generation_result["refusal_reason"],
    }

    write_json_log(config["logging"]["path"], log_record)

    return response