# Retrieval Comparison Summary Report

Date: 2026-05-12  
Project: AIA RAG Case Study Service  
Report Type: Retrieval Quality Summary / PRD Evidence Report  
Evaluation Area: Vector Retrieval / Hybrid Retrieval / Hybrid + Rerank  
Related Components: `configs/app.yaml`, retriever implementation, retrieval evaluation reports

---

## 1. Purpose

This report summarizes the retrieval comparison evidence required by the PRD.

The PRD requires comparing three retrieval configurations:

1. vector-only
2. hybrid
3. hybrid + rerank

It also requires quantitative results and conclusions.

This report consolidates the existing retrieval evaluation artifacts into one reviewer-friendly summary.

---

## 2. Related Evaluation Artifacts

The following retrieval-related reports exist in the repository:

### Retrieval mode comparison

- `reports/evaluations/2026-05-08_retrieval_three_modes.csv`
- `reports/evaluations/2026-05-08_retrieval_three_modes.md`

Purpose:

    Compare vector-only, hybrid, and hybrid + rerank retrieval behavior.

### Vector vs Hybrid comparison

- `reports/evaluations/2026-05-08_retrieval_vector_vs_hybrid.csv`
- `reports/evaluations/2026-05-08_retrieval_vector_vs_hybrid.md`

Purpose:

    Compare vector-only retrieval with hybrid retrieval.

### MRR retrieval comparison

- `reports/evaluations/2026-05-08_retrieval_vector_vs_hybrid_mrr.csv`
- `reports/evaluations/2026-05-08_retrieval_vector_vs_hybrid_mrr.md`

Purpose:

    Compare retrieval ranking quality using MRR-style metrics.

### Context assembly and context precision

- `reports/evaluations/2026-05-09_context_assembly_topn_comparison.csv`
- `reports/evaluations/2026-05-09_context_assembly_topn_comparison.md`
- `reports/evaluations/2026-05-09_context_precision_baseline.csv`
- `reports/evaluations/2026-05-09_context_precision_baseline.md`
- `reports/evaluations/2026-05-10_context_precision_eval.csv`
- `reports/evaluations/2026-05-10_context_precision_eval.md`
- `reports/evaluations/2026-05-11_context_precision_eval.csv`

Purpose:

    Validate final context assembly quality and context precision after retrieval optimization.

### Diagnosis reports

- `reports/diagnosis/2026-05-08_retrieval_issue_diagnosis.md`
- `reports/diagnosis/2026-05-09_llm_insufficient_context_refusal_diagnosis.md`
- `reports/diagnosis/2026-05-10_context_assembly_optimization_report.md`

Purpose:

    Document retrieval and context assembly issues, fixes, and final improvements.

---

## 3. Final Retrieval Configuration

The final project configuration uses:

    retrieval.mode = hybrid
    retrieval.enable_reranker = true

This corresponds to the final selected configuration:

    hybrid + rerank

Reason:

- vector-only retrieval is useful for semantic similarity
- keyword retrieval improves exact-match recall for policy terms, compliance terms, API names, and bilingual terms
- reranking improves final ordering and context selection stability
- hybrid + rerank produced the strongest final retrieval quality evidence in the project

---

## 4. Final Quantitative Retrieval Result

The final context precision evaluation result is:

    avg_context_precision = 0.9807
    avg_source_accuracy = 1.0
    avg_keyword_coverage = 0.9613
    passing_count = 28
    passing_rate = 1.0
    prd_target = 0.7
    prd_pass = True

Evidence:

    reports/evaluations/2026-05-11_context_precision_eval.csv

This final result is well above the PRD target:

    Context Precision >= 0.70

---

## 5. Retrieval Comparison Conclusion

Based on the retrieval comparison artifacts and final validation result:

### Vector-only

Vector-only retrieval provides semantic matching and is useful for paraphrased questions.

However, in this project it is less robust for:

- exact compliance phrases
- policy-specific keywords
- API names
- bilingual CN/EN terminology
- short factual questions that depend on precise source matching

### Hybrid

Hybrid retrieval improves recall by combining semantic similarity with keyword matching.

It is more stable for:

- compliance questions
- security policy questions
- exact terminology
- mixed Chinese and English queries

### Hybrid + Rerank

Hybrid + rerank is the selected final configuration.

It provides the best balance of:

- source accuracy
- keyword coverage
- context precision
- bilingual retrieval robustness
- downstream answer grounding

Final selected configuration:

    hybrid + rerank

Final result:

    avg_context_precision = 0.9807
    prd_pass = True

---

## 6. PRD Impact

This report addresses the PRD requirement:

    Compare three configurations: vector-only, hybrid, hybrid + rerank.
    Provide quantitative results and conclusions.

Status:

    Completed

The project includes both the underlying evaluation files and this consolidated summary report.

---

## 7. Limitations

Current retrieval comparison is sufficient for the PRD case study, but it can still be improved.

Known limitations:

- evaluation set is still relatively small
- no production traffic retrieval benchmark
- no Elasticsearch BM25 backend
- no cross-encoder reranker
- no MMR diversity-based retrieval
- no retrieval confidence calibration model
- no per-category retrieval tuning

---

## 8. Future Work

Future retrieval improvements may include:

- BM25 or Elasticsearch lexical retrieval
- cross-encoder reranking
- MMR retrieval for source diversity
- query expansion
- LLM-based query rewriting
- per-category retrieval configuration
- retrieval confidence calibration
- larger bilingual retrieval benchmark
- retrieval regression dashboard

---

## 9. Conclusion

Retrieval Comparison Summary is completed.

Final status:

    PASS

The project satisfies the PRD retrieval comparison requirement and selects hybrid + rerank as the final retrieval strategy.
