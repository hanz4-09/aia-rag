# Evaluation Report: OCR Extraction for Scanned PDFs

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: PRD Feature Evaluation Report  
Evaluation Area: PDF Ingestion / OCR Extraction / Retrieval  
Related Components: `app/ingestion/loader.py`, `app/ingestion/chunker.py`, `scripts/ingest.py`, `scripts/evaluate_ingestion_pdf_handling.py`

---

## 1. Purpose

This report documents the implementation and validation of OCR extraction for scanned/image-only PDFs.

The PRD states that the internal knowledge base may include a small portion of scanned PDFs. Earlier implementation supported scanned PDF detection and graceful handling. This enhancement adds actual OCR extraction so scanned PDF text can enter the RAG retrieval pipeline.

---

## 2. Change Summary

Implemented OCR extraction in the ingestion pipeline.

New behavior:

1. Text-based PDFs are loaded with `pypdf` text extraction.
2. PDF pages with no or low extractable text are treated as OCR candidates.
3. OCR-enabled pages are rendered with PyMuPDF.
4. Tesseract OCR extracts text from rendered page images.
5. OCR-extracted text is included in loaded documents.
6. OCR text is chunked, embedded, and written to Chroma.
7. OCR text can be retrieved by the RAG retriever.
8. PDF/OCR diagnostics are written to ingestion reports.

Updated files:

- `app/ingestion/loader.py`
- `app/ingestion/chunker.py`
- `scripts/ingest.py`
- `scripts/evaluate_ingestion_pdf_handling.py`
- `configs/app.yaml`

---

## 3. Environment

OCR backend:

    Tesseract OCR

Validated version:

    5.4.0.20240606

OCR Python dependencies:

- PyMuPDF
- Pillow
- pytesseract

---

## 4. Ingestion Validation

Ingestion was executed with:

    python scripts/ingest.py

Final ingestion result:

    Loaded documents: 10
    Generated chunks: 32
    PDF files checked: 2
    Scanned PDF candidates: 1
    PDFs with OCR performed: 1
    PDFs with OCR succeeded: 1

Scanned PDF OCR result:

    File: 99_scanned_pdf_detection_test.pdf
    Status: loaded_with_ocr
    Total pages: 1
    Pages with text: 0
    Pages without text: 1
    Extracted characters: 131
    Scanned PDF candidate: True
    OCR enabled: True
    OCR available: True
    OCR performed: True
    OCR succeeded: True
    Pages OCR attempted: 1
    Pages OCR succeeded: 1

---

## 5. Retrieval Validation

A retrieval test was executed using the OCR-extracted text query:

    API Key incidents must be reported within 24 hours

The top retrieved result was:

    filename = 99_scanned_pdf_detection_test.pdf
    rank = 1

Retrieved text preview:

    Scanned OCR test document
    API Key incidents must be reported within 24 hours
    Audit logs for privileged operations are retained for

This confirms that OCR-extracted text was successfully written into Chroma and is retrievable.

---

## 6. Formal Evaluation Result

Formal PDF/OCR evaluation was executed with:

    python scripts/evaluate_ingestion_pdf_handling.py

Final result:

    Total cases: 2
    Passing cases: 2
    Pass rate: 1.0
    PDF files checked: 2
    Scanned PDF candidates: 1
    PDFs with OCR performed: 1
    PDFs with OCR succeeded: 1
    Retrieval hit rate: 1.0
    Loaded documents: 10
    Skipped empty documents: 0
    PRD Status: PASS

Case-level result:

1. text_based_pdf_loaded
   - status = loaded
   - OCR performed = False
   - retrieval_hit = True
   - retrieval_rank = 1

2. scanned_pdf_ocr_extracted
   - status = loaded_with_ocr
   - OCR performed = True
   - OCR succeeded = True
   - retrieval_hit = True
   - retrieval_rank = 1

---

## 7. PRD Impact

Before this enhancement:

    Scanned/no-text PDFs could be detected and skipped gracefully.

After this enhancement:

    Scanned/image-only PDFs can be OCR processed, loaded, chunked, embedded, and retrieved.

This closes the scanned PDF OCR extraction gap for the current MVP scope.

---

## 8. Limitations

Current OCR implementation is still MVP-level.

Known limitations:

- OCR depends on local Tesseract installation.
- OCR language is configured as English by default.
- OCR quality depends on image quality and page layout.
- No OCR confidence score is currently recorded.
- No page-level OCR retry or preprocessing pipeline is implemented.
- Chinese OCR would require additional Tesseract language data and configuration.

---

## 9. Future Enhancements

Future OCR improvements may include:

- multilingual OCR language packs
- OCR confidence logging
- page image preprocessing
- OCR fallback retries
- OCR quality evaluation set
- production container image with Tesseract preinstalled
- OCR cost/latency tracking

---

## 10. Conclusion

OCR extraction for scanned PDFs is implemented and formally validated.

Final status:

    PASS

The project now supports text-based PDF loading, scanned PDF OCR extraction, OCR text vectorization, and OCR text retrieval.
