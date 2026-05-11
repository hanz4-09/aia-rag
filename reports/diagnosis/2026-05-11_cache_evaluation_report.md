# Evaluation Report: Cache Behavior Evaluation

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: PRD Evaluation Report  
Evaluation Area: Cache Behavior / Operations Metrics  
Related Components: `scripts/evaluate_cache.py`, `app/core/cache.py`, `app/api/chat.py`, `scripts/run_all_evaluations.py`

---

## 1. Purpose

This report documents the formal evaluation of cache behavior.

The PRD requires caching support and a minimal operations report that includes cache hit rate. This evaluation verifies that repeated identical requests can produce cache hits and that cache behavior is observable through structured logs.

---

## 2. Evaluation Method

The evaluation sends the same question twice with the same `session_id`.

Expected behavior:

1. The first request should miss the cache.
2. The second identical request should hit the cache.
3. The second response should still be non-empty and compliant with expected keywords.
4. Structured logs should show `cache_hit=false` for the first request and `cache_hit=true` for the second request.
5. The second request should be faster than the first request.

---

## 3. Evaluation Cases

Two cache cases were evaluated:

1. `cache_audit_logging`
   - Question: What are the audit logging requirements?

2. `cache_api_key_leak`
   - Question: API Key 泄露后应该怎么处理？

---

## 4. Results

Final result:

    Total cases: 2
    Passing cases: 2
    Pass rate: 1.0
    First cache miss rate: 1.0
    Second cache hit rate: 1.0
    Latency improved rate: 1.0
    Avg keyword hit rate: 1.0
    PRD Status: PASS

Case-level latency evidence:

    cache_audit_logging:
      first request latency = 5161 ms
      second request latency = 6 ms

    cache_api_key_leak:
      first request latency = 2750 ms
      second request latency = 7 ms

---

## 5. Observations

The evaluation confirms that:

- cache miss behavior works for first-time requests
- cache hit behavior works for repeated requests
- cache hit status is emitted to structured logs
- repeated requests avoid full generation latency
- cache behavior can be quantified in evaluation reports

---

## 6. Limitations

Current cache behavior is MVP-level.

Known limitations:

- cache is in-memory
- cache is not persistent
- cache is not shared across multiple service instances
- cache key depends on exact normalized question/session behavior
- cache is primarily used for local/demo evaluation

---

## 7. Future Work

Future cache improvements may include:

- distributed cache backend
- semantic cache
- cache invalidation policy
- cache metrics dashboard
- integration with production observability systems

---

## 8. Conclusion

Cache behavior evaluation is completed.

Final status:

    PASS

The project now has reproducible evidence that cache miss/hit behavior works and is visible through structured logs.
