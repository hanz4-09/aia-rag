# Optimization Report: Context Assembly Top-3

Date: 2026-05-10  
Project: AIA RAG Case Study Service  
Report Type: Optimization Summary  
Optimization Area: Context Assembly / Token Efficiency / Answer Quality  
Related Components: `configs/app.yaml`, `app/rag/generator.py`, `app/schemas/response.py`, `app/api/chat.py`

---

## 1. Purpose

This report documents the Context Assembly v1 optimization.

The goal was to reduce noisy context passed to the LLM while preserving answer quality and source coverage.

Before this optimization, the retriever returned top 5 chunks and all 5 chunks were passed into the LLM prompt.

After this optimization, the retriever still returns top 5 chunks for observability and source coverage, but the LLM generator only uses the top 3 chunks as prompt context.

---

## 2. Problem

The context precision baseline showed that the system could reliably retrieve the expected source, but the retrieved context contained many weakly relevant chunks.

Baseline context precision result:

| Metric | Value |
|---|---:|
| Source Hit Rate | 1.0 |
| Top-1 Source Accuracy | 0.8 |
| Avg Context Precision@K | 0.46 |
| Avg Relevant Chunks | 2.3 |
| Avg Irrelevant Chunks | 2.7 |
| Avg Total Chunks | 5.0 |

The key issue was:

    The system usually retrieved the correct source, but passed too many irrelevant chunks to the LLM.

This increased:

- input token usage
- generation latency
- estimated LLM cost
- risk of answer distraction

---

## 3. Evidence

The baseline context precision evaluation showed:

    avg_context_precision_at_k = 0.46
    avg_irrelevant_chunks = 2.7
    avg_total_chunks = 5.0

This means that, on average, fewer than half of the retrieved chunks were considered relevant by the rule-based context precision criteria.

The issue was not retrieval recall. The expected source was still found:

    source_hit_rate = 1.0

The issue was context assembly quality.

---

## 4. Simulation Before Code Change

Before changing production behavior, a top-N context assembly simulation was run.

The simulation compared:

- top 5 chunks
- top 3 chunks
- top 2 chunks

Results:

| Context Strategy | Source Hit Rate | Top-1 Source Accuracy | Avg Context Precision | Avg Relevant Chunks | Avg Irrelevant Chunks |
|---|---:|---:|---:|---:|---:|
| Top 5 | 1.0 | 0.8 | 0.46 | 2.3 | 2.7 |
| Top 3 | 1.0 | 0.8 | 0.60 | 1.8 | 1.2 |
| Top 2 | 1.0 | 0.8 | 0.65 | 1.3 | 0.7 |

The top 3 strategy was selected because it provided the best balance:

- source_hit_rate stayed at 1.0
- top1_source_accuracy stayed at 0.8
- avg_context_precision improved from 0.46 to 0.60
- avg_irrelevant_chunks dropped from 2.7 to 1.2
- more relevant context was preserved than top 2

---

## 5. Change Made

A new context configuration was added:

    context:
      max_context_chunks: 3

The LLM generator was updated so that:

    retrieval top_k remains 5
    LLM prompt context uses only the top 3 chunks

This keeps retrieval observability and source coverage while reducing the context passed to the LLM.

The response source objects now include:

    used_in_context

This makes it clear which retrieved chunks were actually used in the LLM prompt.

The logs now include:

    context_chunks_used

Example validation log:

    top_k = 5
    context_chunks_used = 3
    generator_type = llm
    model_name = qwen-plus

---

## 6. Validation Results

After applying the top-3 context assembly change, the answer evaluation was rerun using the standard 10-question evaluation set.

Answer evaluation result:

| Metric | Value |
|---|---:|
| Total Questions | 10 |
| Rule-based Pass Rate | 1.0 |
| Answer Not Empty Rate | 1.0 |
| Expected Refusal Match Rate | 1.0 |
| Refusal Reason Match Rate | 1.0 |
| Source Hit Rate | 1.0 |
| Forbidden Keywords Clean Rate | 1.0 |
| Avg Expected Keywords Hit Rate | 0.95 |
| Avg Total Latency ms | 1737.0 |
| Avg Generation Latency ms | 1725.7 |
| Avg Total Tokens | 926.89 |

This confirms that the context assembly change did not degrade the rule-based answer quality evaluation.

---

## 7. Token and Latency Impact

Before the optimization, the answer evaluation result showed:

    avg_total_tokens ≈ 1392.56
    avg_generation_latency_ms ≈ 2145.2

After the optimization:

    avg_total_tokens ≈ 926.89
    avg_generation_latency_ms ≈ 1725.7

Estimated improvement:

| Metric | Before | After | Improvement |
|---|---:|---:|---:|
| Avg Total Tokens | 1392.56 | 926.89 | about 33.4% reduction |
| Avg Generation Latency ms | 2145.2 | 1725.7 | about 19.6% reduction |

This shows that reducing prompt context from 5 chunks to 3 chunks helped reduce token usage and generation latency while preserving answer quality.

---

## 8. Conclusion

Context Assembly v1 was successful.

The system now uses:

    retrieval.top_k = 5
    context.max_context_chunks = 3

This provides a better tradeoff between retrieval coverage and LLM prompt efficiency.

Final conclusion:

    Top-3 context assembly should be kept as the default context assembly strategy for the current project.

---

## 9. Remaining Risks

This optimization is based on the current small evaluation set.

Remaining risks:

1. Some future questions may require more than 3 chunks.
2. Rule-based context precision may undercount semantically relevant chunks.
3. The current optimization does not dynamically adjust context size.
4. A future LLM-as-judge evaluation may provide a more robust context relevance signal.

---

## 10. Next Steps

Recommended next steps:

1. Keep `context.max_context_chunks = 3` as the default.
2. Add a larger context precision evaluation set.
3. Consider dynamic context assembly based on reranker score or confidence.
4. Continue tracking `context_chunks_used`, token usage, and generation latency.
5. Add faithfulness evaluation to ensure reduced context does not hurt grounded answer quality.
