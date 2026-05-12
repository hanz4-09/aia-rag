# Evaluation Report: HTTP-level Load Test

Date: 2026-05-12  
Project: AIA RAG Case Study Service  
Report Type: Performance Enhancement Evaluation  
Evaluation Area: HTTP API Load / Concurrency  
Related Components: `scripts/evaluate_http_load.py`, FastAPI `/chat` endpoint

---

## 1. Purpose

This report documents an HTTP-level load evaluation for the RAG QA service.

The existing latency and concurrency evaluations validate the internal pipeline. This HTTP-level test complements those evaluations by sending concurrent HTTP POST requests to the FastAPI `/chat` endpoint.

---

## 2. Evaluation Method

Script:

    scripts/evaluate_http_load.py

Command:

    python scripts/evaluate_http_load.py --base-url http://127.0.0.1:8000 --concurrency 5 --requests 10

Test configuration:

    total_requests = 10
    concurrency_level = 5
    endpoint = POST /chat
    timeout_seconds = 30

Pass criteria:

    success_rate = 1.0
    within_10s_rate >= 0.9
    concurrency_level >= 5

---

## 3. Result

Final result:

    total_requests = 10
    concurrency_level = 5
    successful_requests = 10
    failed_requests = 0
    success_rate = 1.0
    within_10s_rate = 1.0
    refusal_rate = 0.0
    avg_latency_ms = 11.2
    p50_latency_ms = 10.5
    p95_latency_ms = 18.1
    max_latency_ms = 19
    wall_clock_latency_ms = 522
    PRD Status = PASS

---

## 4. Interpretation

The HTTP-level test confirms that the FastAPI `/chat` endpoint can handle at least 5 concurrent HTTP requests successfully.

The second successful run likely benefited from cache hits, which explains the very low average latency. Therefore, this result should be interpreted as HTTP endpoint and concurrent cached-path validation, not as a cold-cache LLM latency benchmark.

Cold-cache latency and LLM generation latency are still covered by the existing latency evaluation:

    scripts/evaluate_latency.py

---

## 5. PRD Impact

The PRD requires support for at least 5 concurrent requests on a single instance and 90% of QA requests to complete within 10 seconds.

This HTTP-level test provides additional evidence at the API boundary:

    concurrency_level = 5
    success_rate = 1.0
    within_10s_rate = 1.0

---

## 6. Limitations

Current limitations:

- This is a local single-instance HTTP test.
- The final successful run likely includes cache hits.
- It does not replace longer production load testing.
- It does not test 10/20/50 concurrent degradation curves.
- It does not include network latency outside localhost.

---

## 7. Future Work

Future enhancements may include:

- cold-cache HTTP load test mode
- cache-disabled HTTP load test mode
- 10/20/50 concurrent request scaling tests
- HTTP-level timeout and retry evaluation
- Locust or k6 benchmark scripts
- latency breakdown by request type

---

## 8. Conclusion

HTTP-level load evaluation is completed.

Final status:

    PASS

The service passed an additional HTTP-level 5-concurrent-request validation through the FastAPI `/chat` endpoint.
