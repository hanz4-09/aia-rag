# Latency Evaluation Report

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Evaluation Type: Latency Evaluation  
Version: v1  
Supporting CSV: reports/evaluations/2026-05-11_latency_eval.csv

---

## 1. Objective

This evaluation validates the PRD latency requirement for the RAG service.

The PRD requires:

    90% of QA requests should complete end-to-end within 10 seconds.

This evaluation runs the QA pipeline against the answer evaluation set and records end-to-end latency for each request.

---

## 2. Dataset

Evaluation set:

    eval/answer_eval_set.jsonl

Total requests:

    30

---

## 3. Metrics

Measured metrics:

- success_rate
- within_10s_rate
- avg_latency_ms
- p50_latency_ms
- p90_latency_ms
- p95_latency_ms
- max_latency_ms
- avg_retrieval_latency_ms
- avg_generation_latency_ms

---

## 4. Summary Results

| Metric | Value |
|---|---:|
| Total Requests | 30 |
| Successful Requests | 30 |
| Failed Requests | 0 |
| Success Rate | 1.0 |
| Within 10s Count | 29 |
| Within 10s Rate | 0.9667 |
| Avg Latency ms | 3318.07 |
| P50 Latency ms | 2561.5 |
| P90 Latency ms | 5618.8 |
| P95 Latency ms | 6717.75 |
| Max Latency ms | 10087 |
| Avg Retrieval Latency ms | 46.97 |
| Avg Generation Latency ms | 3270.47 |
| PRD Latency Threshold ms | 10000 |
| Required Within-threshold Rate | 0.9 |
| PRD Pass | True |

---

## 5. PRD Status

PRD target:

    within_10s_rate >= 0.90

Current result:

    within_10s_rate = 0.9667

Status:

    PASS

---

## 6. Notes

This is a sequential latency evaluation, not a concurrent load test.

Concurrent request handling will be evaluated separately.
