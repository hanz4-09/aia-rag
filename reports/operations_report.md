# Operations Report

**Project:** AIA RAG Case Study Service
**Report Date:** 2026-05-10
**Report Type:** Operations Metrics Summary

---

## 1. Executive Summary

This report summarizes the operational metrics for the RAG QA service, covering latency, token usage, cache performance, refusal behavior, and answer compliance. All metrics are measured against the PRD requirements.

| Metric | Value | PRD Target | Status |
|--------|-------|------------|--------|
| P90 Latency (hybrid_rerank) | 4,311 ms | < 10,000 ms | ✅ PASS |
| P95 Latency (hybrid_rerank) | 4,315 ms | < 10,000 ms | ✅ PASS |
| Avg Token Usage | 1,392.56 tokens/query | - | - |
| Cache Hit Rate | 66.7% (repeated queries) | - | ✅ Working |
| Refusal Rate | 0% | - | ✅ Normal |
| Answer Compliance Rate | 100% | ≥ 80% (≥ 90%) | ✅ PASS |
| Faithfulness | 100% | ≥ 85% | ✅ PASS |
| Context Precision | 97.17% | ≥ 70% | ✅ PASS |
| Style Consistency | 98.15% | ≥ 85% | ✅ PASS |
| Refusal Appropriateness | 100% | ≥ 80% (≥ 90%) | ✅ PASS |

---

## 2. Latency Metrics

### 2.1 End-to-End Latency (hybrid_rerank mode)

| Percentile | Latency (ms) | Notes |
|------------|--------------|-------|
| P50 | 2,523 | Median latency |
| P90 | 4,311 | 90th percentile |
| P95 | 4,315 | 95th percentile |
| Avg | 2,851 | Mean latency |

### 2.2 Latency Breakdown

| Stage | Avg Latency (ms) | % of Total |
|-------|------------------|------------|
| Retrieval | 68.67 | 2.4% |
| Generation (LLM) | 2,781 | 97.6% |
| **Total** | **2,851** | **100%** |

### 2.3 Retrieval Mode Comparison

| Retrieval Mode | Hit Rate | Top-1 Accuracy | MRR | Avg Latency (ms) |
|----------------|----------|----------------|-----|------------------|
| vector | 78.57% | 57.14% | 0.6452 | 41.71 |
| hybrid | 100% | 64.29% | 0.8214 | 10.79 |
| hybrid_rerank | 100% | 78.57% | 0.8929 | 9.21 |

**Key Finding:** Hybrid + Rerank mode provides the best retrieval quality with minimal latency overhead.

### 2.4 Reranker Latency Optimization

After optimization (reducing initial_k from 20 to 10, adding batch_size and max_length):

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Retrieval Latency | 3,773 ms | 1,666 ms | -55.8% |
| Quality Maintained | Yes | Yes | - |

---

## 3. Token Usage

### 3.1 Token Statistics

| Metric | Value |
|--------|-------|
| Total Requests | 10 |
| Total Input Tokens | 12,392 |
| Total Output Tokens | 1,036 |
| Total Tokens | 13,428 |
| Avg Input Tokens/Query | 1,239 |
| Avg Output Tokens/Query | 103.67 |
| Avg Total Tokens/Query | 1,392.56 |

### 3.2 Token Usage by Category

| Category | Avg Input Tokens | Avg Output Tokens | Avg Total Tokens |
|----------|------------------|-------------------|------------------|
| compliance | 921 | 38.5 | 959.5 |
| security_cn | 1,616.5 | 133 | 1,749.5 |
| technical_spec | 1,207 | 132.5 | 1,339.5 |
| hr_policy_cn | 1,458 | 57 | 1,515 |
| architecture_cn | 1,679 | 129 | 1,808 |

### 3.3 Cost Estimation (GPT-4o-mini pricing)

| Metric | Value |
|--------|-------|
| Model | qwen-plus (equivalent to GPT-4o-mini) |
| Input Price | $0.40 / 1M tokens |
| Output Price | $1.20 / 1M tokens |
| Cost per 1,000 calls | $0.62 - $1.86 |
| Monthly Cost (10K calls) | $6.20 - $18.60 |

---

## 4. Cache Performance

Cache is implemented as `InMemoryCache` with exact-match key and integrated into the `/chat` endpoint.

### 4.1 Configuration

```yaml
cache:
  enabled: true
  ttl_seconds: 300
```

### 4.2 Verification Results (5 questions × 3 passes)

| Metric | Value |
|--------|-------|
| Total Requests | 15 |
| Cache Hits | 10 |
| Cache Misses | 5 |
| Cache Hit Rate | 66.7% |
| Avg Latency (miss) | 2,486 ms |
| Avg Latency (hit) | 0 ms |
| Latency Reduction | 100% |

### 4.3 Cache Key Format

```
question={normalized_question}|mode={retrieval_mode}|reranker={bool}|top_k={int}
```

**Note:** Cache hit rate depends on query repetition. First-time queries always miss. In production with repeated questions, cache significantly reduces latency and token cost.

---

## 5. Refusal Metrics

### 5.1 Refusal Statistics

| Metric | Value |
|--------|-------|
| Total Requests | 10 |
| Refused Requests | 0 |
| Refusal Rate | 0% |

### 5.2 Refusal Reasons (from evaluation)

| Refusal Reason | Count | Description |
|----------------|-------|-------------|
| NO_RETRIEVED_CONTEXT | 1 | Out-of-scope question (Kubernetes) |
| SAFETY_RULE_TRIGGERED | 1 | Prompt injection attempt |

**Note:** These refusals are appropriate and expected behavior.

---

## 6. Answer Compliance

### 6.1 Compliance Metrics

| Metric | Value | PRD Target |
|--------|-------|------------|
| Rule-Based Pass Rate | 100% | ≥ 80% |
| Answer Not Empty Rate | 100% | - |
| Expected Refusal Match Rate | 100% | - |
| Refusal Reason Match Rate | 100% | - |
| Source Hit Rate | 100% | - |
| Forbidden Keywords Clean Rate | 100% | - |
| Expected Keywords Hit Rate | 97.5% | - |

### 6.2 Quality Metrics

| Metric | Value | PRD Target | Status |
|--------|-------|------------|--------|
| Faithfulness | 100% | ≥ 85% | ✅ PASS |
| Context Precision | 97.17% | ≥ 70% | ✅ PASS |
| Source Accuracy | 71.3% | - | - |
| Context Relevancy | 72.4% | - | - |

---

## 7. Concurrency Performance

### 7.1 Test Results (with warmup)

| Concurrent Users | P50 Latency | P90 Latency | P95 Latency | Success Rate |
|------------------|-------------|-------------|-------------|--------------|
| 5 | 2.1s | 2.3s | 2.4s | 100% |
| 10 | 2.2s | 2.5s | 2.6s | 100% |
| 20 | 2.4s | 2.8s | 3.0s | 100% |

**PRD Requirement:** ≥ 5 concurrent users with P90 < 10s → ✅ PASS

---

## 8. Issue Diagnosis Summary

### 8.1 Issue 1: Vector-only Retrieval Recall Insufficient

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Hit Rate | 78.57% | 100% | +27.28% |

**Fix:** Added hybrid retrieval combining vector + BM25 keyword search.

### 8.2 Issue 2: Hybrid Ranking Quality Limited

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Top-1 Accuracy | 64.29% | 78.57% | +22.21% |

**Fix:** Added CrossEncoder reranker for second-stage ranking.

---

## 9. Recommendations

### 9.1 High Priority

1. ~~**Improve Faithfulness** (current: 83.5%, target: 85%)~~
   - ~~Gap is only 1.5%~~
   - ✅ **RESOLVED**: Faithfulness = 100% (33/33 statements faithful across 8 questions)
   - Evaluated using LLM-as-judge (qwen-plus, temperature=0)
2. **Expand Evaluation Set**

### 9.2 Medium Priority

3. **Monitor Token Usage**
   - Implement token budgeting
   - Add cost alerts at threshold levels

4. **Expand Evaluation Set**
   - Current: 10 questions
   - Target: 50+ questions for better coverage

### 9.3 Low Priority

5. **Add More Refusal Reasons**
   - LOW_RETRIEVAL_CONFIDENCE
   - RATE_LIMIT_EXCEEDED

---

## 10. Appendix

### 10.1 Data Sources

- `reports/evaluations/2026-05-10_faithfulness_eval.csv`
- `reports/evaluations/2026-05-08_retrieval_three_modes.csv`
- `reports/operations_report.csv`
- `reports/diagnosis/2026-05-08_retrieval_issue_diagnosis.md`

### 10.2 Model Configuration

```yaml
retrieval:
  mode: hybrid
  enable_reranker: true
  vector_weight: 0.6
  keyword_weight: 0.4

generation:
  model: qwen-plus
  max_tokens: 512
  temperature: 0.1
```

### 10.3 Log Fields

See `reports/observability/log_field_dictionary.md` for complete log field documentation.

---

**Report Generated:** 2026-05-10
**Next Review:** 2026-05-17
