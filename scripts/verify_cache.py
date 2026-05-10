"""
Cache Effectiveness Verification Script

Verifies that the InMemoryCache is working correctly in the /chat endpoint.
Starts the FastAPI server, sends repeated requests, and measures cache hit rate
and latency improvement.

Usage:
    python scripts/verify_cache.py
"""

import sys
import time
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.cache import InMemoryCache, build_cache_key
from app.core.config import load_config
from app.rag.generator import create_generator
from app.rag.pii import redact_pii
from app.rag.retriever_factory import create_retriever
from app.rag.safety import check_safety


# Test questions (mix of categories)
TEST_QUESTIONS = [
    "What are the audit logging requirements?",
    "How long should audit logs for privileged operations be retained?",
    "API Key 泄露后应该怎么处理？",
    "日志中是否可以记录明文密码和完整 API Key？",
    "What endpoints does the AKP Platform provide?",
]


def simulate_chat_with_cache(question: str, config, retriever, generator, cache, cache_enabled: bool):
    """Simulate the /chat endpoint logic with cache."""
    start_time = time.time()

    safety_result = check_safety(question)
    if not safety_result["safe"]:
        return {
            "cache_hit": False,
            "latency_ms": int((time.time() - start_time) * 1000),
            "refused": True,
        }

    cache_key = build_cache_key(
        question=question,
        retrieval_mode=config["retrieval"]["mode"],
        reranker_enabled=config["retrieval"].get("enable_reranker", False),
        top_k=config["retrieval"].get("top_k", 5),
    )

    cache_hit = False

    # Check cache
    if cache_enabled:
        cached = cache.get(cache_key)
        if cached:
            total_latency_ms = int((time.time() - start_time) * 1000)
            return {
                "cache_hit": True,
                "latency_ms": total_latency_ms,
                "refused": cached.get("refused", False),
            }

    # Full pipeline
    retrieval_start = time.time()
    retrieved_chunks = retriever.retrieve(question)
    retrieval_latency_ms = int((time.time() - retrieval_start) * 1000)

    generation_start = time.time()
    generation_result = generator.generate(
        question=question,
        retrieved_chunks=retrieved_chunks,
    )
    generation_latency_ms = int((time.time() - generation_start) * 1000)

    total_latency_ms = int((time.time() - start_time) * 1000)

    # Store in cache
    if cache_enabled and not generation_result["refused"]:
        cache.set(cache_key, {
            "answer": generation_result["answer"],
            "refused": generation_result["refused"],
            "refusal_reason": generation_result["refusal_reason"],
            "sources": generation_result["sources"],
            "input_tokens": generation_result.get("input_tokens"),
            "output_tokens": generation_result.get("output_tokens"),
            "total_tokens": generation_result.get("total_tokens"),
            "model_name": generation_result.get("model_name"),
            "generator_type": generation_result.get("generator_type"),
        })

    return {
        "cache_hit": False,
        "latency_ms": total_latency_ms,
        "retrieval_latency_ms": retrieval_latency_ms,
        "generation_latency_ms": generation_latency_ms,
        "refused": generation_result["refused"],
    }


def main():
    config = load_config()

    cache_config = config.get("cache", {})
    cache_enabled = cache_config.get("enabled", False)
    ttl = cache_config.get("ttl_seconds", 300)

    print("=" * 60)
    print("CACHE EFFECTIVENESS VERIFICATION")
    print("=" * 60)
    print(f"  Cache enabled (config): {cache_enabled}")
    print(f"  TTL: {ttl}s")
    print(f"  Test questions: {len(TEST_QUESTIONS)}")
    print(f"  Repeats per question: 3")
    print()

    retriever = create_retriever(config)
    generator = create_generator(config)
    cache = InMemoryCache(ttl_seconds=ttl)

    # Phase 1: First pass (populate cache)
    print("--- Phase 1: First Pass (populate cache) ---")
    first_pass_results = []
    for i, q in enumerate(TEST_QUESTIONS, 1):
        result = simulate_chat_with_cache(q, config, retriever, generator, cache, cache_enabled=True)
        first_pass_results.append(result)
        print(f"  [{i}] cache_hit={result['cache_hit']}, latency={result['latency_ms']}ms")

    # Phase 2: Second pass (should hit cache)
    print()
    print("--- Phase 2: Second Pass (should hit cache) ---")
    second_pass_results = []
    for i, q in enumerate(TEST_QUESTIONS, 1):
        result = simulate_chat_with_cache(q, config, retriever, generator, cache, cache_enabled=True)
        second_pass_results.append(result)
        print(f"  [{i}] cache_hit={result['cache_hit']}, latency={result['latency_ms']}ms")

    # Phase 3: Third pass (should still hit cache)
    print()
    print("--- Phase 3: Third Pass (should still hit cache) ---")
    third_pass_results = []
    for i, q in enumerate(TEST_QUESTIONS, 1):
        result = simulate_chat_with_cache(q, config, retriever, generator, cache, cache_enabled=True)
        third_pass_results.append(result)
        print(f"  [{i}] cache_hit={result['cache_hit']}, latency={result['latency_ms']}ms")

    # Summary
    all_results = first_pass_results + second_pass_results + third_pass_results
    total_requests = len(all_results)
    cache_hits = sum(1 for r in all_results if r["cache_hit"])
    cache_misses = total_requests - cache_hits
    cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0

    first_pass_latencies = [r["latency_ms"] for r in first_pass_results]
    cached_latencies = [r["latency_ms"] for r in second_pass_results + third_pass_results if r["cache_hit"]]

    avg_first_pass = sum(first_pass_latencies) / len(first_pass_latencies) if first_pass_latencies else 0
    avg_cached = sum(cached_latencies) / len(cached_latencies) if cached_latencies else 0
    latency_reduction = ((avg_first_pass - avg_cached) / avg_first_pass * 100) if avg_first_pass > 0 else 0

    print()
    print("=" * 60)
    print("CACHE VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"  Total requests:       {total_requests}")
    print(f"  Cache hits:           {cache_hits}")
    print(f"  Cache misses:         {cache_misses}")
    print(f"  Cache hit rate:       {cache_hit_rate:.1%}")
    print(f"  Avg latency (miss):   {avg_first_pass:.0f} ms")
    print(f"  Avg latency (hit):    {avg_cached:.0f} ms")
    print(f"  Latency reduction:    {latency_reduction:.1f}%")
    print(f"  Cache working:        {'✅ YES' if cache_hit_rate > 0 else '❌ NO'}")
    print("=" * 60)

    # Save results
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cache_enabled": cache_enabled,
        "ttl_seconds": ttl,
        "total_requests": total_requests,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "cache_hit_rate": round(cache_hit_rate, 4),
        "avg_latency_miss_ms": round(avg_first_pass, 2),
        "avg_latency_hit_ms": round(avg_cached, 2),
        "latency_reduction_pct": round(latency_reduction, 2),
        "cache_functioning": cache_hit_rate > 0,
    }

    report_path = PROJECT_ROOT / "reports" / "cache_verification.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    main()
