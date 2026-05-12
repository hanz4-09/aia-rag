# Optimization Report: Corpus Growth Regression Evaluation

Date: 2026-05-12  
Project: AIA RAG Case Study Service  
Report Type: Corpus Growth / Retrieval Regression Evaluation  
Optimization Area: RAG Retrieval Robustness / New Document Regression Guard  
Related Components: `scripts/evaluate_corpus_regression.py`, Chroma vector store, retrieval pipeline

---

## 1. Purpose

This report documents the addition of a corpus growth regression evaluation.

RAG accuracy is corpus-dependent. When new files are added to `data/raw/`, the retrieval space changes. New documents may introduce ranking competition, duplicate content, conflicting policy statements, OCR noise, or irrelevant keyword matches.

Therefore, the current high accuracy on the existing Chroma collection should not be assumed to hold automatically after new files are added.

This evaluation provides a golden-query regression guard for future corpus growth.

---

## 2. Change

Added:

    scripts/evaluate_corpus_regression.py

The script runs a fixed set of golden retrieval cases after ingestion.

It verifies:

- expected source rank
- Top-1 hit
- Top-3 hit
- Top-5 hit
- required Top-K hit
- expected keyword coverage inside the matched source chunk
- average expected source rank
- maximum expected source rank

Output reports:

    reports/evaluations/2026-05-12_corpus_regression_eval.csv
    reports/evaluations/2026-05-12_corpus_regression_eval.md

---

## 3. Evaluation Scope

The current golden regression set includes 7 cases:

1. audit logging requirements
2. audit log retention
3. Chinese API Key leakage handling
4. Chinese employee API Key reporting window
5. annual leave policy
6. OCR scanned PDF API Key incident reporting
7. Chinese PII redaction format

These cases cover:

- English compliance retrieval
- Chinese security retrieval
- HR policy retrieval
- OCR-derived PDF retrieval
- privacy / PII policy retrieval

---

## 4. Final Evaluation Result

Final command:

    python scripts/evaluate_corpus_regression.py

Final result:

    total_cases = 7
    passing_count = 7
    pass_rate = 1.0
    top1_hit_rate = 0.7143
    top3_hit_rate = 1.0
    top5_hit_rate = 1.0
    required_top_k_hit_rate = 1.0
    avg_expected_source_rank = 1.2857
    max_expected_source_rank = 2
    avg_keyword_hit_rate = 1.0
    PRD Status = PASS

---

## 5. Interpretation

The current corpus snapshot remains stable after the embedding model switch to `BAAI/bge-m3`.

All golden queries found their expected source within the required Top-K range.

The Top-1 hit rate is 0.7143, while Top-3 and Top-5 hit rates are both 1.0. This is acceptable for a RAG system because downstream context assembly can use multiple top chunks.

The maximum expected source rank is 2, meaning no golden source fell below rank 2 in the current evaluation.

---

## 6. Recommended Workflow for New Files

Whenever new files are added to `data/raw/`, use the following workflow:

    python scripts/ingest.py
    python scripts/evaluate_corpus_regression.py
    python scripts/evaluate_context_precision.py
    python scripts/run_all_evaluations.py --mode all --skip-run

If corpus regression fails, investigate:

- whether a new document is competing with existing golden sources
- whether duplicate or conflicting content was added
- whether chunking split important content poorly
- whether keyword-heavy but irrelevant chunks entered top results
- whether OCR noise polluted retrieval
- whether expected_source or expected_keywords need to be updated for legitimate corpus changes

---

## 7. PRD Impact

The PRD requires quantified retrieval quality and stable RAG behavior.

This optimization strengthens retrieval reliability by adding a regression guard for future corpus growth.

It also clarifies that reported accuracy is tied to a corpus snapshot and must be revalidated after document updates.

---

## 8. Limitations

Current limitations:

- The golden regression set has 7 cases.
- It does not cover every document in the corpus.
- It does not detect all possible policy conflicts.
- It focuses on retrieval quality, not full generated-answer quality.
- It does not yet run automatically in CI.
- It does not yet compare before/after corpus snapshots.

---

## 9. Future Work

Future improvements may include:

- expanding golden cases to 20+
- adding per-document golden queries
- adding conflict detection for policy changes
- adding duplicate document detection
- adding corpus-diff reports
- adding CI quality gates after ingestion
- adding regression trend tracking across corpus versions
- adding answer-level corpus regression evaluation

---

## 10. Conclusion

Corpus Growth Regression Evaluation is completed.

Final status:

    PASS

The project now has a repeatable regression guard to validate key retrieval behavior after new documents are added.
