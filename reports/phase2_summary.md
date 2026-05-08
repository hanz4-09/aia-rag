# Phase 2 Summary: Retrieval, Evaluation, Observability, and Cache Hardening

Date: 2026-05-08  
Project: AIA RAG Case Study Service  
Phase: Phase 2  
Status: Completed

---

## 1. Phase 2 Objective

The objective of Phase 2 was to extend the MVP RAG service toward the core case study requirements.

Phase 1 focused on making the RAG service runnable end-to-end.

Phase 2 focused on hardening the system in the following areas:

- Configurable retrieval modes
- Hybrid retrieval
- Reranker support
- Retrieval evaluation
- Formal evaluation reports
- Structured observability
- Issue diagnosis
- Cache support

---

## 2. Completed Capabilities

### 2.1 Configurable Retrieval Modes

The system now supports the following retrieval configurations:

    retrieval.mode = vector

    retrieval.mode = hybrid

    retrieval.mode = hybrid
    retrieval.enable_reranker = true

Supported modes:

| Mode | Description | Status |
|---|---|---|
| vector | Vector-only retrieval using Chroma similarity search | Completed |
| hybrid | Vector search + BM25 keyword search | Completed |
| hybrid + rerank | Hybrid retrieval followed by score-based reranking | Completed |

---

## 3. Retrieval Enhancements

### 3.1 Vector-only Retrieval

Vector-only retrieval was implemented as the MVP baseline.

It uses:

- Local HuggingFace multilingual embeddings
- Chroma vector store
- Top-k similarity search

### 3.2 Hybrid Retrieval

Hybrid retrieval was added to improve recall.

It combines:

    vector search + BM25 keyword search

Implemented files:

    app/rag/keyword_retriever.py
    app/rag/hybrid_retriever.py
    app/rag/retriever_factory.py

### 3.3 Reranker

A lightweight score-based reranker was added.

Implemented file:

    app/rag/reranker.py

Current reranker strategy:

    reranker_score =
      rerank_hybrid_score_weight * hybrid_score
      + rerank_keyword_score_weight * keyword_score
      + rerank_vector_rank_weight * vector_rank_score

Current limitation:

    The reranker is score-based, not a cross-encoder reranker yet.

---

## 4. Retrieval Evaluation

A retrieval evaluation set was created:

    eval/retrieval_eval_set.jsonl

The evaluation script was enhanced to support:

- vector
- hybrid
- hybrid_rerank

Metrics:

- Hit Rate
- Top-1 Accuracy
- Expected Rank
- Reciprocal Rank
- MRR
- Average retrieval latency

Implemented script:

    scripts/evaluate_retrieval.py

---

## 5. Evaluation Results

The latest three-mode retrieval evaluation produced the following results:

| Retrieval Mode | Hit Rate | Top-1 Accuracy | MRR | Avg Latency |
|---|---:|---:|---:|---:|
| Vector-only | 0.7857 | 0.5714 | 0.6452 | 41.71 ms |
| Hybrid | 1.0000 | 0.6429 | 0.8214 | 10.79 ms |
| Hybrid + Rerank | 1.0000 | 0.7857 | 0.8929 | 9.21 ms |

Key conclusion:

    Hybrid retrieval improves recall.
    Reranking improves ranking quality.

---

## 6. Formal Evaluation Reports

Formal versioned evaluation reports are stored under:

    reports/evaluations/

Current reports:

    2026-05-08_retrieval_vector_vs_hybrid.md
    2026-05-08_retrieval_vector_vs_hybrid.csv

    2026-05-08_retrieval_vector_vs_hybrid_mrr.md
    2026-05-08_retrieval_vector_vs_hybrid_mrr.csv

    2026-05-08_retrieval_three_modes.md
    2026-05-08_retrieval_three_modes.csv

Project rule:

    Every future evaluation must produce a formal Markdown report and a supporting CSV file.
    Old reports should not be overwritten.

---

## 7. Observability

Structured JSONL logging was enhanced.

Log file:

    logs/rag_service.jsonl

Log field dictionary:

    reports/observability/log_field_dictionary.md

Important logged fields include:

- request_id
- session_id
- query
- retrieval_mode
- reranker_enabled
- retrieved_chunk_ids
- retrieved_sources
- retrieval_distances
- retrieval_sources
- keyword_scores
- hybrid_scores
- reranker_scores
- rerank_latency_ms
- retrieval_latency_ms
- generation_latency_ms
- total_latency_ms
- cache_hit
- refused
- refusal_reason
- timestamp

---

## 8. Issue Diagnosis

Two major diagnosis reports were created.

### 8.1 Retrieval Quality Diagnosis

Report:

    reports/diagnosis/2026-05-08_retrieval_issue_diagnosis.md

Issues diagnosed:

1. Vector-only retrieval recall was insufficient.
2. Hybrid retrieval ranking quality was limited.

Fixes:

1. Added hybrid retrieval.
2. Added score-based reranker.

Before / after improvements:

| Issue | Before | Fix | After | Improvement |
|---|---:|---|---:|---:|
| Vector recall insufficient | hit_rate = 0.7857 | Add hybrid retrieval | hit_rate = 1.0000 | +27.28% |
| Hybrid top-1 ranking limited | top1_accuracy = 0.6429 | Add reranker | top1_accuracy = 0.7857 | +22.21% |

### 8.2 Safety False Positive Diagnosis

Report:

    reports/diagnosis/2026-05-08_safety_false_positive_diagnosis.md

Issue:

    The query "API Key 泄露后应该怎么处理？" was incorrectly refused as SAFETY_RULE_TRIGGERED.

Root cause:

    The original safety rule relied too heavily on broad keyword matching.

Fix:

    Updated safety logic from broad keyword blocking to intent-based pattern matching.

Post-fix validation:

    The query passed safety check, entered normal RAG flow, and repeated requests could hit cache.

---

## 9. Cache

A simple in-memory exact-match cache was added.

Implemented file:

    app/core/cache.py

Cache configuration:

    cache.enabled = true
    cache.ttl_seconds = 300

Cache key includes:

- normalized question
- retrieval mode
- reranker enabled flag
- top_k

Current behavior:

    Only non-refusal answers are cached.
    Safety refusals and low-confidence refusals are not cached.

Cache is reflected in logs through:

    cache_hit

And in the operations report through:

    cache_hit_rate

---

## 10. Operations Report

Operations report script:

    scripts/generate_report.py

Output:

    reports/operations_report.csv

Current supported fields:

- total_requests
- p50_latency_ms
- p95_latency_ms
- avg_latency_ms
- cache_hit_rate
- refusal_rate
- answer_compliance_rate
- avg_input_tokens
- avg_output_tokens

Current limitations:

    answer_compliance_rate = N/A
    avg_input_tokens = N/A
    avg_output_tokens = N/A

Reason:

    The current generator is still extractive and does not call a real LLM.

---

## 11. Files Added or Updated in Phase 2

### Added

    app/rag/keyword_retriever.py
    app/rag/hybrid_retriever.py
    app/rag/retriever_factory.py
    app/rag/reranker.py
    app/core/cache.py
    eval/retrieval_eval_set.jsonl
    reports/evaluations/
    reports/observability/log_field_dictionary.md
    reports/diagnosis/
    reports/phase2_summary.md

### Updated

    app/api/chat.py
    app/rag/generator.py
    app/rag/safety.py
    app/schemas/response.py
    configs/app.yaml
    scripts/evaluate_retrieval.py
    scripts/generate_report.py
    README.md

---

## 12. Remaining Limitations

The project still has the following limitations:

1. The generator is still extractive and does not call a real LLM.
2. The reranker is score-based, not model-based.
3. Evaluation is source-level, not chunk-level.
4. Context Precision is not implemented yet.
5. Faithfulness evaluation is not implemented yet.
6. Answer Compliance evaluation is not implemented yet.
7. Style Consistency evaluation is not implemented yet.
8. Refusal Appropriateness evaluation is not yet quantified with a full test set.
9. OCR for scanned PDFs is not implemented yet.
10. Cache is in-memory only and not shared across processes.

---

## 13. Recommended Next Phase

Phase 3 should focus on answer quality and production-like evaluation.

Recommended Phase 3 items:

1. Replace extractive generator with real LLM-based generator.
2. Add token usage tracking.
3. Add cost estimation per 1,000 calls.
4. Add context precision evaluation.
5. Add faithfulness evaluation.
6. Add answer compliance evaluation.
7. Add refusal appropriateness evaluation set.
8. Add real cross-encoder reranker.
9. Add larger evaluation dataset.
10. Add p50 / p95 end-to-end latency under concurrent requests.

---

## 14. Phase 2 Conclusion

Phase 2 successfully extended the MVP into a more robust RAG service.

The project now supports configurable retrieval modes, hybrid retrieval, reranking, structured logs, evaluation reports, issue diagnosis, and cache reporting.

The strongest retrieval configuration currently is:

    retrieval.mode = hybrid
    retrieval.enable_reranker = true

This configuration achieved:

    hit_rate = 1.0000
    top1_accuracy = 0.7857
    MRR = 0.8929

The next major gap is answer generation quality, which depends on replacing the temporary extractive generator with a real LLM-based generator.
