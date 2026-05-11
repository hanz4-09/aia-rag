# Diagnosis Report: Qwen-Max Latency Outlier

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: Performance Diagnosis  
Area: Latency Evaluation / Qwen-Max Generation Latency  
Related Files: `reports/evaluations/2026-05-11_latency_eval.csv`, `scripts/evaluate_latency.py`

---

## 1. Purpose

This report documents the investigation of the latency outlier observed during the qwen-max full evaluation run.

The goal was to determine whether the request exceeding 10 seconds was caused by retrieval, generation, answer length, or system-level issues.

---

## 2. Observed Outlier

The latency evaluation reported:

    within_10s_rate = 0.9667
    max_latency_ms = 10591
    PRD status = PASS

The only request exceeding 10 seconds was:

    系统在什么情况下会返回拒答？

Detailed metrics:

    category = architecture_cn
    retrieval_latency_ms = 11
    generation_latency_ms = 10580
    total_latency_ms = 10591
    input_tokens = 943
    output_tokens = 86
    total_tokens = 1029
    model_name = qwen-max
    generator_type = llm

---

## 3. Diagnosis

The outlier was not caused by retrieval.

Evidence:

    retrieval_latency_ms = 11

The outlier was dominated by LLM generation latency.

Evidence:

    generation_latency_ms = 10580

The output was not unusually long.

Evidence:

    output_tokens = 86

Therefore, the most likely cause is qwen-max provider latency, network variance, or model-side generation fluctuation.

---

## 4. Top Slow Requests

The top slow requests all showed the same pattern: low retrieval latency and high generation latency.

Examples:

1. 系统在什么情况下会返回拒答？
   - total_latency_ms = 10591
   - retrieval_latency_ms = 11
   - generation_latency_ms = 10580

2. What are the audit logging requirements?
   - total_latency_ms = 7277
   - retrieval_latency_ms = 32
   - generation_latency_ms = 7243

3. 敏感数据脱敏的格式是什么？
   - total_latency_ms = 7003
   - retrieval_latency_ms = 11
   - generation_latency_ms = 6991

This confirms that the latency bottleneck is the qwen-max generation call rather than retrieval.

---

## 5. PRD Impact

The PRD latency target is:

    90% of QA requests should complete within 10 seconds.

Current result:

    within_10s_rate = 0.9667

Status:

    PASS

The outlier does not block PRD completion.

---

## 6. Decision

No immediate code change is required.

Reason:

- retrieval is fast
- answer length is normal
- PRD target still passes
- changing prompt/context to optimize one provider-side outlier may risk answer quality

This issue will be recorded as a known performance caveat.

---

## 7. Future Options

Possible future improvements:

1. Add retry or timeout policy for LLM provider calls.
2. Add model selection guidance for quality, latency, and cost trade-offs.
3. Use lower-latency models for repeated evaluations.
4. Keep qwen-max for final validation or demo scenarios.
5. Add HTTP-level load testing for production-like latency measurement.

---

## 8. Conclusion

The qwen-max latency outlier was caused by LLM generation latency, not retrieval or context assembly.

Final status:

    Diagnosed
    No immediate code change required
    PRD latency target remains PASS
