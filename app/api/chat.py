import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter

from app.core.cache import InMemoryCache, build_cache_key
from app.core.config import load_config
from app.core.logger import write_json_log
from app.core.session_memory import InMemorySessionMemory
from app.rag.generator import create_generator
from app.rag.pii import redact_pii
from app.rag.retriever_factory import create_retriever
from app.rag.safety import check_safety
from app.schemas.request import ChatRequest
from app.schemas.response import ChatResponse


router = APIRouter()

config: Dict[str, Any] = load_config()
retriever = create_retriever(config)
generator = create_generator(config)

cache_config = config.get("cache", {})
cache_enabled = cache_config.get("enabled", False)
cache = InMemoryCache(ttl_seconds=cache_config.get("ttl_seconds", 300))
memory_config = config.get("memory", {})
session_memory = InMemorySessionMemory(
    max_turns=memory_config.get("max_turns", 3)
)


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

        log_record = _build_log_record(
            request_id=request_id,
            session_id=request.session_id,
            query=redacted_question,
            retrieved_chunks=[],
            generation_result={
                "refused": True,
                "refusal_reason": safety_result["reason"],
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "model_name": config.get("llm", {}).get("model"),
                "generator_type": config.get("generator", {}).get("type"),
            },
            retrieval_latency_ms=0,
            generation_latency_ms=0,
            total_latency_ms=total_latency_ms,
            cache_hit=False,
        )

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

            log_record = _build_log_record_from_sources(
                request_id=request_id,
                session_id=request.session_id,
                query=redacted_question,
                sources=cached_response["sources"],
                generation_result=cached_response,
                total_latency_ms=total_latency_ms,
                cache_hit=cache_hit,
            )

            write_json_log(config["logging"]["path"], log_record)

            return response

    retrieval_start = time.time()
    retrieved_chunks = retriever.retrieve(request.question)
    retrieval_latency_ms = int((time.time() - retrieval_start) * 1000)

    conversation_history = session_memory.get_history(request.session_id)

    generation_start = time.time()
    generation_result = generator.generate(
        question=request.question,
        retrieved_chunks=retrieved_chunks,
        conversation_history=conversation_history,
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

    if not generation_result["refused"]:
        session_memory.add_turn(
            session_id=request.session_id,
            question=redacted_question,
            answer=generation_result["answer"],
        )

    if cache_enabled and not generation_result["refused"]:
        cache.set(
            cache_key,
            {
                "answer": generation_result["answer"],
                "refused": generation_result["refused"],
                "refusal_reason": generation_result["refusal_reason"],
                "sources": generation_result["sources"],
                "input_tokens": generation_result.get("input_tokens"),
                "output_tokens": generation_result.get("output_tokens"),
                "total_tokens": generation_result.get("total_tokens"),
                "model_name": generation_result.get("model_name"),
                "generator_type": generation_result.get("generator_type"),
            },
        )

    log_record = _build_log_record(
        request_id=request_id,
        session_id=request.session_id,
        query=redacted_question,
        retrieved_chunks=retrieved_chunks,
        generation_result=generation_result,
        retrieval_latency_ms=retrieval_latency_ms,
        generation_latency_ms=generation_latency_ms,
        total_latency_ms=total_latency_ms,
        cache_hit=cache_hit,
    )

    write_json_log(config["logging"]["path"], log_record)

    return response


def _build_log_record(
    request_id: str,
    session_id: str | None,
    query: str,
    retrieved_chunks: list[Dict[str, Any]],
    generation_result: Dict[str, Any],
    retrieval_latency_ms: int,
    generation_latency_ms: int,
    total_latency_ms: int,
    cache_hit: bool,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "session_id": session_id,
        "query": query,
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
        "input_tokens": generation_result.get("input_tokens"),
        "output_tokens": generation_result.get("output_tokens"),
        "total_tokens": generation_result.get("total_tokens"),
        "model_name": generation_result.get("model_name"),
        "generator_type": generation_result.get("generator_type"),
        "context_chunks_used": generation_result.get("context_chunks_used"),
        "cache_hit": cache_hit,
        "refused": generation_result["refused"],
        "refusal_reason": generation_result["refusal_reason"],
    }


def _build_log_record_from_sources(
    request_id: str,
    session_id: str | None,
    query: str,
    sources: list[Dict[str, Any]],
    generation_result: Dict[str, Any],
    total_latency_ms: int,
    cache_hit: bool,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "session_id": session_id,
        "query": query,
        "retrieval_mode": config["retrieval"]["mode"],
        "reranker_enabled": config["retrieval"].get("enable_reranker", False),
        "top_k": config["retrieval"].get("top_k", 5),
        "retrieved_chunk_ids": [
            source.get("chunk_id") for source in sources
        ],
        "retrieved_sources": [
            source.get("filename") for source in sources
        ],
        "retrieval_distances": [
            source.get("distance") for source in sources
        ],
        "retrieval_sources": [
            source.get("retrieval_source") for source in sources
        ],
        "keyword_scores": [
            source.get("keyword_score") for source in sources
        ],
        "hybrid_scores": [
            source.get("hybrid_score") for source in sources
        ],
        "vector_ranks": [
            source.get("vector_rank") for source in sources
        ],
        "keyword_ranks": [
            source.get("keyword_rank") for source in sources
        ],
        "reranker_scores": [
            source.get("reranker_score") for source in sources
        ],
        "rerank_latency_ms": 0,
        "retrieval_latency_ms": 0,
        "generation_latency_ms": 0,
        "total_latency_ms": total_latency_ms,
        "input_tokens": generation_result.get("input_tokens"),
        "output_tokens": generation_result.get("output_tokens"),
        "total_tokens": generation_result.get("total_tokens"),
        "model_name": generation_result.get("model_name"),
        "generator_type": generation_result.get("generator_type"),
        "context_chunks_used": generation_result.get("context_chunks_used"),
        "cache_hit": cache_hit,
        "refused": generation_result["refused"],
        "refusal_reason": generation_result["refusal_reason"],
    }