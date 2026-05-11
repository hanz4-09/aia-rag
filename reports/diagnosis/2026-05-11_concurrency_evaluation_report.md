# Evaluation Report: Concurrency Evaluation

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: PRD Metric Evaluation Summary  
Evaluation Area: Concurrency / Performance  
Related Components: `scripts/evaluate_concurrency.py`, `eval/answer_eval_set.jsonl`, `reports/evaluations/2026-05-11_concurrency_eval.csv`

---

## 1. Purpose

This report documents the concurrency evaluation performed during Phase 3.

The goal was to verify whether a single local service instance can support at least 5 concurrent requests, as required by the PRD.

---

## 2. Initial Observation

The first version of the concurrency evaluation produced failing latency results because each worker initialized its own retriever and generator inside the measured request path.

This caused model loading and component initialization time to be counted as per-request latency.

Initial symptom:

- average request latency was around 18 seconds
- average generation latency was only around 1.6 seconds
- the gap was caused by startup/component initialization cost

This indicated that the test methodology was incorrect, not necessarily that the runtime request path was slow.

---

## 3. Evaluation Method

The concurrency script was updated to separate startup cost from request processing cost.

The updated script:

1. Prebuilds one retriever/generator pair per worker.
2. Excludes prebuild time from the measured request latency.
3. Runs 5 requests concurrently using `ThreadPoolExecutor`.
4. Records success rate, within-10-second rate, latency percentiles, and wall-clock latency.

This better represents a running service where retriever and generator components are initialized before serving requests.

---

## 4. PRD Target

PRD requirement:

    A single instance should support at least 5 concurrent requests.

Additional acceptance criteria used in this evaluation:

    success_rate >= 1.0
    within_10s_rate >= 0.90

---

## 5. Evaluation Result

Final result:

| Metric | Value |
|---|---:|
| Total Requests | 5 |
| Concurrency Level | 5 |
| Successful Requests | 5 |
| Failed Requests | 0 |
| Success Rate | 1.0 |
| Within 10s Count | 5 |
| Within 10s Rate | 1.0 |
| Avg Latency ms | 2400 |
| P50 Latency ms | 1930.0 |
| P90 Latency ms | 3784.4 |
| P95 Latency ms | 3795.2 |
| Max Latency ms | 3806 |
| Wall-clock Latency ms | 3811 |
| Prebuild Latency ms | 43600 |
| Avg Retrieval Latency ms | 219.6 |
| Avg Generation Latency ms | 2179.4 |
| Required Success Rate | 1.0 |
| Required Within 10s Rate | 0.90 |
| PRD Status | PASS |

---

## 6. Interpretation

The service satisfies the PRD concurrency requirement.

All 5 concurrent requests completed successfully and within 10 seconds.

The measured concurrent wall-clock latency was approximately 3.8 seconds.

The prebuild latency is recorded separately as startup cost and is not counted as per-request latency.

---

## 7. Caveats

This evaluation uses an in-process concurrency model with `ThreadPoolExecutor`.

It validates local pipeline concurrency behavior, but it is not a full HTTP-level load test through Uvicorn/FastAPI.

A future enhancement could add an HTTP-based concurrency test using `httpx.AsyncClient` against the running FastAPI service.

---

## 8. Conclusion

Concurrency Evaluation passed the PRD target.

Final measured value:

    concurrency_level = 5
    success_rate = 1.0
    within_10s_rate = 1.0

PRD status:

    PASS
