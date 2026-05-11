# Evaluation Report: Latency Evaluation

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: PRD Metric Evaluation Summary  
Evaluation Area: Latency / Performance  
Related Components: `scripts/evaluate_latency.py`, `eval/answer_eval_set.jsonl`, `reports/evaluations/2026-05-11_latency_eval.csv`

---

## 1. Purpose

This report documents the latency evaluation performed during Phase 3.

The goal was to verify whether the RAG service satisfies the PRD latency requirement:

    90% of QA requests should complete end-to-end within 10 seconds.

---

## 2. Evaluation Method

The evaluation uses:

    scripts/evaluate_latency.py

The script runs the full QA pipeline against:

    eval/answer_eval_set.jsonl

For each request, the script records:

- retrieval latency
- generation latency
- total end-to-end latency
- success status
- whether the request completed within 10 seconds

This evaluation is a sequential latency baseline. Concurrent request handling is evaluated separately.

---

## 3. PRD Target

PRD target:

    within_10s_rate >= 0.90

Latency threshold:

    10000 ms

---

## 4. Evaluation Result

Final result:

| Metric | Value |
|---|---:|
| Total Requests | 30 |
| Successful Requests | 30 |
| Failed Requests | 0 |
| Success Rate | 1.0 |
| Within 10s Count | 30 |
| Within 10s Rate | 1.0 |
| Avg Latency ms | 1714.23 |
| P50 Latency ms | 1189.0 |
| P90 Latency ms | 3319.1 |
| P95 Latency ms | 4133.75 |
| Max Latency ms | 5123 |
| Avg Retrieval Latency ms | 11.93 |
| Avg Generation Latency ms | 1701.77 |
| PRD Latency Threshold ms | 10000 |
| Required Within-threshold Rate | 0.90 |
| PRD Status | PASS |

---

## 5. Interpretation

The service satisfies the PRD latency requirement.

All 30 evaluated QA requests completed within 10 seconds.

The latency distribution shows that generation latency is the dominant component:

    avg_generation_latency_ms = 1701.77

Retrieval latency is low:

    avg_retrieval_latency_ms = 11.93

This indicates that the current retrieval path is efficient, and most end-to-end latency comes from LLM generation.

---

## 6. Caveats

This evaluation is sequential and does not measure concurrent request behavior.

The following performance requirement still needs a separate evaluation:

    single instance supports at least 5 concurrent requests

---

## 7. Conclusion

Latency Evaluation passed the PRD target.

Final measured value:

    within_10s_rate = 1.0

PRD status:

    PASS
