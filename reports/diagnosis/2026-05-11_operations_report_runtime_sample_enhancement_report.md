# Optimization Report: Operations Report Runtime Sample Enhancement

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: Operations Report Enhancement  
Optimization Area: Runtime Observability / Operations Metrics  
Related Components: `logs/rag_service.jsonl`, `scripts/generate_report.py`, `reports/operations_report.csv`

---

## 1. Purpose

This report documents the enhancement of the runtime sample used by the operations report.

The PRD requires a minimal operations report including latency, token usage, cache hit rate, refusal rate, and answer compliance rate.

Before this enhancement, the operations report was generated from a very small runtime log sample.

---

## 2. Initial Issue

The previous operations report had limited runtime evidence:

    total_requests = 1

Although the report fields were present, the sample size was too small to demonstrate realistic runtime observability.

---

## 3. Change

A controlled runtime sample was generated to cover multiple representative request types.

The generated sample includes:

- normal answer request
- repeated request cache hit
- multi-turn follow-up request
- PII redaction request
- OCR-related query
- safety refusal
- out-of-scope refusal

The runtime log was regenerated in:

    logs/rag_service.jsonl

Then the operations report was regenerated with:

    python scripts/generate_report.py

---

## 4. Runtime Sample Coverage

Final runtime log sample:

    total_logs = 9
    cache_hits = 3
    refusals = 2
    memory_rewrites = 1

Covered scenarios:

1. Normal answer
2. Cache hit
3. Multi-turn memory rewrite
4. PII redaction
5. OCR-related retrieval
6. Safety refusal
7. Out-of-scope refusal

---

## 5. New Operations Report Result

Updated operations report:

    total_requests = 9
    p50_latency_ms = 751
    p95_latency_ms = 3355
    avg_latency_ms = 885.56
    avg_retrieval_latency_ms = 9.22
    avg_generation_latency_ms = 875.89
    cache_hit_rate = 0.3333
    refusal_rate = 0.2222
    generator_types = llm
    model_names = qwen-max
    total_tokens = 6338
    avg_total_tokens = 792.25
    reference_total_cost = 0.002886
    reference_cost_per_request = 0.000321
    reference_cost_per_1000_calls = 0.320711
    estimated_billable_cost_per_1000_calls = 0.0
    answer_compliance_rate = 1.0

---

## 6. One-click Summary Update

The one-click evaluation summary now includes the updated operations report metrics:

    total_requests = 9
    p50_latency_ms = 751
    p95_latency_ms = 3355
    avg_latency_ms = 885.56
    avg_total_tokens = 792.25
    reference_cost_per_1000_calls = 0.320711
    estimated_billable_cost_per_1000_calls = 0.0
    answer_compliance_rate = 1.0

---

## 7. PRD Impact

This enhancement strengthens the Minimal Operations Report evidence.

The report now demonstrates:

- latency metrics over multiple runtime requests
- token usage over multiple LLM calls
- cache hit rate from actual repeated requests
- refusal rate from actual refusal cases
- answer compliance integration
- cost estimate per 1,000 calls

---

## 8. Limitations

The runtime sample is still intentionally small and controlled.

It is suitable for PRD/demo validation, but not a production traffic benchmark.

Future production operations reporting should use larger traffic windows and real deployment telemetry.

---

## 9. Conclusion

Operations report runtime sample enhancement is completed.

Final status:

    Completed

The operations report now contains a more representative runtime sample and better supports the PRD observability requirement.
