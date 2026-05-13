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
| Avg Latency ms | 2804.6 |
| P50 Latency ms | 2596.0 |
| P90 Latency ms | 4141.2 |
| P95 Latency ms | 4422.6 |
| Max Latency ms | 4704 |
| Wall-clock Latency ms | 4706 |
| Prebuild Latency ms | 48011 |
| Avg Retrieval Latency ms | 560 |
| Avg Generation Latency ms | 2243.6 |
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
