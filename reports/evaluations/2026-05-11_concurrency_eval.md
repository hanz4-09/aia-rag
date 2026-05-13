# Concurrency Evaluation Report

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Evaluation Type: Concurrency Evaluation  
Version: v1  
Supporting CSV: reports/evaluations/2026-05-11_concurrency_eval.csv

---

## 1. Objective

This evaluation validates the PRD concurrency requirement for the RAG service.

The PRD requires:

    A single instance should support at least 5 concurrent requests.

This evaluation runs 5 requests concurrently through the QA pipeline and records success rate and latency.

---

## 2. Important Measurement Note

The retriever and generator are prebuilt before the timed concurrency window.

This is intentional because model loading, embedding model initialization, and client initialization are startup costs, not per-request latency in a running service.

The reported request latency measures the actual concurrent request processing time after components are initialized.

---

## 3. Dataset

Evaluation set:

    eval/answer_eval_set.jsonl

Concurrency level:

    5

Total requests executed:

    5

---

## 4. Summary Results

| Metric | Value |
|---|---:|
| Total Requests | 5 |
| Concurrency Level | 5 |
| Successful Requests | 5 |
| Failed Requests | 0 |
| Success Rate | 1.0 |
| Within 10s Count | 5 |
| Within 10s Rate | 1.0 |
| Avg Latency ms | 3684.4 |
| P50 Latency ms | 3996.0 |
| P90 Latency ms | 5403.4 |
| P95 Latency ms | 5423.2 |
| Max Latency ms | 5443 |
| Wall-clock Latency ms | 5448 |
| Prebuild Latency ms | 46574 |
| Avg Retrieval Latency ms | 528.6 |
| Avg Generation Latency ms | 3154.4 |
| Required Success Rate | 1.0 |
| Required Within 10s Rate | 0.9 |
| PRD Pass | True |

---

## 5. PRD Status

PRD target:

    single instance supports at least 5 concurrent requests

Additional acceptance criteria used in this evaluation:

    success_rate >= 1.0
    within_10s_rate >= 0.90

Current result:

    concurrency_level = 5
    success_rate = 1.0
    within_10s_rate = 1.0

Status:

    PASS

---

## 6. Notes

This evaluation uses an in-process concurrent execution model with ThreadPoolExecutor.

It validates local pipeline concurrency behavior, but it is not a full production load test through an HTTP server.
