# Optimization Report: Embedding Model Switch to BAAI/bge-m3

Date: 2026-05-12  
Project: AIA RAG Case Study Service  
Report Type: Retrieval / Embedding Optimization Report  
Optimization Area: Embedding Model / Multilingual Retrieval  
Related Components: `configs/app.yaml`, `scripts/ingest.py`, Chroma vector store

---

## 1. Purpose

This report documents the embedding model switch to `BAAI/bge-m3`.

The project corpus is bilingual, containing both English and Chinese internal documents. It also includes OCR-extracted PDF text. A stronger multilingual embedding model is beneficial for improving retrieval robustness across English, Chinese, and OCR-derived text.

---

## 2. Change

The embedding configuration was updated to use a local HuggingFace embedding provider with `BAAI/bge-m3`.

Final configuration:

    embedding:
      provider: huggingface
      model: BAAI/bge-m3

The vector store was rebuilt after the model switch:

    rm -rf data/chroma
    python scripts/ingest.py

Ingestion result:

    Loaded documents = 10
    Generated chunks = 32
    Total chunks stored = 32

---

## 3. Manual Retrieval Sanity Check

Three manual retrieval checks were performed after rebuilding Chroma.

### 3.1 Audit logging query

Query:

    What are the audit logging requirements?

Top result:

    03_compliance_guide_en.txt_chunk_2

Result:

    PASS

### 3.2 Chinese API Key leakage query

Query:

    API Key 泄露后应该怎么处理？

Top result:

    04_data_security_policy_cn.txt_chunk_1

Result:

    PASS

### 3.3 OCR scanned PDF query

Query:

    API Key incidents must be reported within 24 hours

Top result:

    99_scanned_pdf_detection_test.pdf_chunk_0

Result:

    PASS

This confirms that English retrieval, Chinese retrieval, and OCR-based retrieval remained functional after the embedding switch.

---

## 4. Formal Evaluation Result

After switching to `BAAI/bge-m3`, the following key evaluations were re-run or refreshed.

### Context Precision

    avg_context_precision = 0.9807
    avg_source_accuracy = 1.0
    avg_keyword_coverage = 0.9613
    passing_count = 28
    passing_rate = 1.0
    prd_target = 0.7
    prd_pass = True

### Answer Compliance

    total_questions = 30
    answer_compliance_rate = 1.0
    source_hit_rate = 1.0
    prd_pass = True

### PDF/OCR Ingestion

    total_cases = 2
    passing_count = 2
    pass_rate = 1.0
    pdfs_with_ocr_performed = 1
    pdfs_with_ocr_succeeded = 1
    retrieval_hit_rate = 1.0
    prd_pass = True

### Advanced Memory

    total_cases = 2
    passing_count = 2
    pass_rate = 1.0
    persistent_memory_pass_rate = 1.0
    query_rewrite_applied_rate = 1.0
    retrieval_query_resolution_rate = 1.0
    source_hit_rate = 1.0
    avg_keyword_hit_rate = 0.8334
    prd_pass = True

### One-click Summary

The one-click summary was refreshed with:

    python scripts/run_all_evaluations.py --mode all --skip-run

The 13-task evaluation suite remained passing.

---

## 5. PRD Impact

The PRD requires strong bilingual RAG quality and quantified retrieval quality.

This embedding model switch improves alignment with that goal by using a stronger multilingual embedding model while preserving all key PRD metrics.

Final status:

    PASS

The project remains compliant with retrieval, OCR, advanced memory, and answer quality requirements after switching to `BAAI/bge-m3`.

---

## 6. Notes

The embedding switch requires rebuilding the vector store because different embedding models use different vector spaces.

Required command after changing embedding model:

    rm -rf data/chroma
    python scripts/ingest.py

---

## 7. Limitations

Current limitations:

- The evaluation set is still relatively small.
- No large-scale embedding model benchmark was performed.
- No direct before/after MRR comparison against the previous embedding model was re-run.
- The model depends on HuggingFace model availability and local cache.
- No HF_TOKEN is configured, so unauthenticated HuggingFace downloads may be rate-limited.

---

## 8. Future Work

Future improvements may include:

- direct before/after retrieval comparison between MiniLM and BGE-M3
- larger bilingual retrieval benchmark
- embedding latency and memory footprint measurement
- local model cache documentation
- optional HF_TOKEN configuration
- embedding model fallback strategy

---

## 9. Conclusion

Embedding Model Switch to `BAAI/bge-m3` is completed.

Final status:

    PASS

The project now uses a stronger multilingual local embedding model and all key PRD evaluations remain passing after re-ingestion.
