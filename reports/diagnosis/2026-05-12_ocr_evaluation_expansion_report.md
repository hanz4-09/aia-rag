# Optimization Report: OCR Evaluation Set Expansion

Date: 2026-05-12  
Project: AIA RAG Case Study Service  
Report Type: OCR Evaluation Enhancement  
Optimization Area: OCR Extraction / PDF Ingestion / Retrieval Validation  
Related Components: `app/ingestion/loader.py`, `scripts/evaluate_ingestion_pdf_handling.py`

---

## 1. Purpose

This report documents the expansion of the OCR evaluation set.

The project already supported scanned PDF detection, OCR extraction, and retrieval validation. The original OCR evaluation mainly validated text-based PDF loading and scanned PDF OCR extraction.

This enhancement expands OCR evaluation to validate OCR-derived content retrieval more directly.

---

## 2. Change

Enhanced:

    scripts/evaluate_ingestion_pdf_handling.py

The OCR evaluation was expanded from 2 cases to 4 cases.

New coverage includes:

- text-based PDF loading
- scanned PDF OCR extraction
- scanned PDF OCR retrieval hit
- OCR content retrieval for API Key incident reporting window
- OCR content retrieval for audit log retention content

The evaluator now also records OCR retrieval keyword metrics:

- expected keyword count
- matched keyword count
- keyword hit rate
- missing keywords
- retrieved text preview

---

## 3. Final Evaluation Result

Final command:

    python scripts/evaluate_ingestion_pdf_handling.py

Final result:

    total_cases = 4
    passing_count = 4
    pass_rate = 1.0
    pdf_files_checked = 2
    scanned_pdf_candidates = 1
    pdfs_with_ocr_performed = 1
    pdfs_with_ocr_succeeded = 1
    retrieval_hit_rate = 1.0
    loaded_documents = 10
    skipped_empty_documents = 0
    PRD Status = PASS

Case-level result:

1. text_based_pdf_loaded
   - status = loaded
   - retrieval_hit = True
   - retrieval_rank = 1
   - pass = True

2. scanned_pdf_ocr_extracted
   - status = loaded_with_ocr
   - ocr_performed = True
   - ocr_succeeded = True
   - retrieval_hit = True
   - retrieval_rank = 1
   - pass = True

3. ocr_api_key_reporting_window_content
   - status = loaded_with_ocr
   - ocr_performed = True
   - ocr_succeeded = True
   - retrieval_hit = True
   - retrieval_rank = 1
   - pass = True

4. ocr_audit_log_retention_content
   - status = loaded_with_ocr
   - ocr_performed = True
   - ocr_succeeded = True
   - retrieval_hit = True
   - retrieval_rank = 1
   - pass = True

Output reports:

    reports/evaluations/2026-05-12_pdf_ingestion_eval.csv
    reports/evaluations/2026-05-12_pdf_ingestion_eval.md

---

## 4. PRD Impact

The PRD states that the corpus includes a small portion of scanned PDFs.

This enhancement strengthens that requirement by verifying that scanned PDF OCR text is not only extracted, but also retrievable for downstream RAG use.

The expanded OCR evaluation confirms:

- scanned PDFs are detected
- OCR is performed
- OCR succeeds
- OCR-derived text is embedded into Chroma
- OCR-derived text can be retrieved by content-specific queries

---

## 5. Limitations

Current limitations:

- The OCR evaluation still uses a small synthetic scanned PDF.
- It does not test multi-page scanned PDFs.
- It does not test Chinese OCR.
- It does not measure OCR confidence.
- It does not test noisy, rotated, or low-resolution scans.
- It does not yet evaluate full end-to-end answer generation from OCR-only context.

---

## 6. Future Work

Future improvements may include:

- multi-page scanned PDF evaluation
- Chinese OCR evaluation
- OCR confidence score checks
- OCR preprocessing benchmark
- noisy scanned PDF benchmark
- end-to-end OCR answer generation evaluation
- OCR latency evaluation

---

## 7. Conclusion

OCR Evaluation Set Expansion is completed.

Final status:

    PASS

The project now has stronger OCR evaluation coverage for scanned PDF extraction and OCR-derived retrieval content.
