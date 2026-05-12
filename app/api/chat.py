import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter

from app.core.cache import InMemoryCache, build_cache_key
from app.core.config import load_config
from app.core.logger import write_json_log
from app.core.session_memory import create_session_memory
from app.rag.generator import create_generator
from app.rag.pii import redact_pii
from app.rag.query_rewriter import build_history_aware_retrieval_query
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
session_memory = create_session_memory(config)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())
    trace_id = request_id
    root_span_id = uuid.uuid4().hex[:16]
    memory_span_id = uuid.uuid4().hex[:16]
    retrieval_span_id = uuid.uuid4().hex[:16]
    rerank_span_id = uuid.uuid4().hex[:16]
    generation_span_id = uuid.uuid4().hex[:16]
    trace_schema_version = "otel-lite-v1"
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
            retrieval_query=redacted_question,
            memory_turns_used=0,
            memory_rewrite_applied=False,
            memory_rewrite_strategy="safety_refusal",
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
        trace_id=trace_id,
        root_span_id=root_span_id,
        memory_span_id=memory_span_id,
        retrieval_span_id=retrieval_span_id,
        rerank_span_id=rerank_span_id,
        generation_span_id=generation_span_id,
        trace_schema_version=trace_schema_version,
        )

        write_json_log(config["logging"]["path"], log_record)

        return response

    conversation_history = session_memory.get_history(request.session_id)

    rewrite_result = {
        "retrieval_query": redacted_question,
        "memory_rewrite_applied": False,
        "rewrite_strategy": "disabled",
    }

    if memory_config.get("enable_query_rewrite", False):
        rewrite_result = build_history_aware_retrieval_query(
            question=redacted_question,
            conversation_history=conversation_history,
        )

    retrieval_query = str(rewrite_result["retrieval_query"])
    memory_rewrite_applied = bool(rewrite_result["memory_rewrite_applied"])
    memory_rewrite_strategy = str(rewrite_result["rewrite_strategy"])
    memory_turns_used = len(conversation_history)

    cache_hit = False
    cache_key = build_cache_key(
        question=retrieval_query,
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

            if not cached_response["refused"]:
                session_memory.add_turn(
                    session_id=request.session_id,
                    question=redacted_question,
                    answer=cached_response["answer"],
                )

            log_record = _build_log_record_from_sources(
                request_id=request_id,
                session_id=request.session_id,
                query=redacted_question,
                retrieval_query=retrieval_query,
                memory_turns_used=memory_turns_used,
                memory_rewrite_applied=memory_rewrite_applied,
                memory_rewrite_strategy=memory_rewrite_strategy,
                sources=cached_response["sources"],
                generation_result=cached_response,
                total_latency_ms=total_latency_ms,
                cache_hit=cache_hit,
                trace_id=trace_id,
                root_span_id=root_span_id,
                memory_span_id=memory_span_id,
                retrieval_span_id=retrieval_span_id,
                rerank_span_id=rerank_span_id,
                generation_span_id=generation_span_id,
                trace_schema_version=trace_schema_version,
            )

            write_json_log(config["logging"]["path"], log_record)

            return response

    retrieval_start = time.time()
    try:
        retrieved_chunks = retriever.retrieve(retrieval_query)
        retrieval_latency_ms = int((time.time() - retrieval_start) * 1000)
    except Exception as exc:
        retrieval_latency_ms = int((time.time() - retrieval_start) * 1000)
        total_latency_ms = int((time.time() - start_time) * 1000)

        error_message = str(exc)[:500]
        generation_result = {
            "answer": (
                "I cannot complete the request because the retrieval stage failed. "
                "Please try again later or contact the system owner if the issue persists."
            ),
            "sources": [],
            "refused": True,
            "refusal_reason": "SYSTEM_ERROR",
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "model_name": config.get("llm", {}).get("model"),
            "generator_type": config.get("generator", {}).get("type"),
            "context_chunks_used": 0,
            "error_stage": "retrieval",
            "error_type": type(exc).__name__,
            "error_message": error_message,
            "error_handled": True,
        }

        response = ChatResponse(
            answer=generation_result["answer"],
            refused=True,
            refusal_reason="SYSTEM_ERROR",
            sources=[],
            latency_ms=total_latency_ms,
        )

        log_record = _build_log_record(
            request_id=request_id,
            session_id=request.session_id,
            query=redacted_question,
            retrieval_query=retrieval_query,
            memory_turns_used=memory_turns_used,
            memory_rewrite_applied=memory_rewrite_applied,
            memory_rewrite_strategy=memory_rewrite_strategy,
            retrieved_chunks=[],
            generation_result=generation_result,
            retrieval_latency_ms=retrieval_latency_ms,
            generation_latency_ms=0,
            total_latency_ms=total_latency_ms,
            cache_hit=cache_hit,
            trace_id=trace_id,
            root_span_id=root_span_id,
            memory_span_id=memory_span_id,
            retrieval_span_id=retrieval_span_id,
            rerank_span_id=rerank_span_id,
            generation_span_id=generation_span_id,
            trace_schema_version=trace_schema_version,
        )

        write_json_log(config["logging"]["path"], log_record)
        return response

    generation_start = time.time()
    try:
        generation_result = generator.generate(
            question=redacted_question,
            retrieved_chunks=retrieved_chunks,
            conversation_history=conversation_history,
        )
        generation_latency_ms = int((time.time() - generation_start) * 1000)
    except Exception as exc:
        generation_latency_ms = int((time.time() - generation_start) * 1000)
        total_latency_ms = int((time.time() - start_time) * 1000)

        error_message = str(exc)[:500]
        generation_result = {
            "answer": (
                "I cannot complete the request because the generation stage failed. "
                "Please try again later or contact the system owner if the issue persists."
            ),
            "sources": [],
            "refused": True,
            "refusal_reason": "SYSTEM_ERROR",
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "model_name": config.get("llm", {}).get("model"),
            "generator_type": config.get("generator", {}).get("type"),
            "context_chunks_used": 0,
            "error_stage": "generation",
            "error_type": type(exc).__name__,
            "error_message": error_message,
            "error_handled": True,
        }

        response = ChatResponse(
            answer=generation_result["answer"],
            refused=True,
            refusal_reason="SYSTEM_ERROR",
            sources=[],
            latency_ms=total_latency_ms,
        )

        log_record = _build_log_record(
            request_id=request_id,
            session_id=request.session_id,
            query=redacted_question,
            retrieval_query=retrieval_query,
            memory_turns_used=memory_turns_used,
            memory_rewrite_applied=memory_rewrite_applied,
            memory_rewrite_strategy=memory_rewrite_strategy,
            retrieved_chunks=retrieved_chunks,
            generation_result=generation_result,
            retrieval_latency_ms=retrieval_latency_ms,
            generation_latency_ms=generation_latency_ms,
            total_latency_ms=total_latency_ms,
            cache_hit=cache_hit,
            trace_id=trace_id,
            root_span_id=root_span_id,
            memory_span_id=memory_span_id,
            retrieval_span_id=retrieval_span_id,
            rerank_span_id=rerank_span_id,
            generation_span_id=generation_span_id,
            trace_schema_version=trace_schema_version,
        )

        write_json_log(config["logging"]["path"], log_record)
        return response

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
                "context_chunks_used": generation_result.get("context_chunks_used"),
            },
        )

    log_record = _build_log_record(
        request_id=request_id,
        session_id=request.session_id,
        query=redacted_question,
        retrieval_query=retrieval_query,
        memory_turns_used=memory_turns_used,
        memory_rewrite_applied=memory_rewrite_applied,
        memory_rewrite_strategy=memory_rewrite_strategy,
        retrieved_chunks=retrieved_chunks,
        generation_result=generation_result,
        retrieval_latency_ms=retrieval_latency_ms,
        generation_latency_ms=generation_latency_ms,
        total_latency_ms=total_latency_ms,
        cache_hit=cache_hit,
        trace_id=trace_id,
        root_span_id=root_span_id,
        memory_span_id=memory_span_id,
        retrieval_span_id=retrieval_span_id,
        rerank_span_id=rerank_span_id,
        generation_span_id=generation_span_id,
        trace_schema_version=trace_schema_version,
    )

    write_json_log(config["logging"]["path"], log_record)

    return response


def _build_log_record(
    request_id: str,
    session_id: str | None,
    query: str,
    retrieval_query: str,
    memory_turns_used: int,
    memory_rewrite_applied: bool,
    memory_rewrite_strategy: str,
    retrieved_chunks: list[Dict[str, Any]],
    generation_result: Dict[str, Any],
    retrieval_latency_ms: int,
    generation_latency_ms: int,
    total_latency_ms: int,
    cache_hit: bool,
    trace_id: str,
    root_span_id: str,
    memory_span_id: str,
    retrieval_span_id: str,
    rerank_span_id: str,
    generation_span_id: str,
    trace_schema_version: str,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "trace_id": trace_id,
        "span_id": root_span_id,
        "parent_span_id": None,
        "memory_span_id": memory_span_id,
        "retrieval_span_id": retrieval_span_id,
        "rerank_span_id": rerank_span_id,
        "generation_span_id": generation_span_id,
        "trace_schema_version": trace_schema_version,
        "session_id": session_id,
        "query": query,
        "retrieval_query": retrieval_query,
        "memory_turns_used": memory_turns_used,
        "memory_rewrite_applied": memory_rewrite_applied,
        "memory_rewrite_strategy": memory_rewrite_strategy,
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
        "error_stage": generation_result.get("error_stage"),
        "error_type": generation_result.get("error_type"),
        "error_message": generation_result.get("error_message"),
        "error_handled": generation_result.get("error_handled", False),
        "fallback_applied": generation_result.get("fallback_applied", False),
        "fallback_reason": generation_result.get("fallback_reason"),
        "fallback_error_type": generation_result.get("fallback_error_type"),
        "fallback_error_message": generation_result.get("fallback_error_message"),
        "primary_model_name": generation_result.get("primary_model_name"),
        "primary_generator_type": generation_result.get("primary_generator_type"),
        "fallback_generator_type": generation_result.get("fallback_generator_type"),
        "final_generator_type": generation_result.get("final_generator_type"),
        "final_model_name": generation_result.get("final_model_name"),
    }


def _build_log_record_from_sources(
    request_id: str,
    session_id: str | None,
    query: str,
    retrieval_query: str,
    memory_turns_used: int,
    memory_rewrite_applied: bool,
    memory_rewrite_strategy: str,
    sources: list[Dict[str, Any]],
    generation_result: Dict[str, Any],
    total_latency_ms: int,
    cache_hit: bool,
    trace_id: str,
    root_span_id: str,
    memory_span_id: str,
    retrieval_span_id: str,
    rerank_span_id: str,
    generation_span_id: str,
    trace_schema_version: str,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "session_id": session_id,
        "query": query,
        "retrieval_query": retrieval_query,
        "memory_turns_used": memory_turns_used,
        "memory_rewrite_applied": memory_rewrite_applied,
        "memory_rewrite_strategy": memory_rewrite_strategy,
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
        "error_stage": generation_result.get("error_stage"),
        "error_type": generation_result.get("error_type"),
        "error_message": generation_result.get("error_message"),
        "error_handled": generation_result.get("error_handled", False),
        "fallback_applied": generation_result.get("fallback_applied", False),
        "fallback_reason": generation_result.get("fallback_reason"),
        "fallback_error_type": generation_result.get("fallback_error_type"),
        "fallback_error_message": generation_result.get("fallback_error_message"),
        "primary_model_name": generation_result.get("primary_model_name"),
        "primary_generator_type": generation_result.get("primary_generator_type"),
        "fallback_generator_type": generation_result.get("fallback_generator_type"),
        "final_generator_type": generation_result.get("final_generator_type"),
        "final_model_name": generation_result.get("final_model_name"),
    }
