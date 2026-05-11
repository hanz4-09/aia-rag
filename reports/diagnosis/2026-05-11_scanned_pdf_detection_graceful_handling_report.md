# Optimization Report: Scanned PDF Detection and Graceful Handling

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Report Type: PRD Gap Closure / Ingestion Enhancement  
Optimization Area: PDF Ingestion / Scanned PDF Handling  
Related Components: `app/ingestion/loader.py`, `app/ingestion/chunker.py`, `scripts/ingest.py`

---

## 1. Purpose

This report documents the implementation of scanned PDF detection and graceful handling.

The PRD states that the bilingual internal knowledge base may include a small portion of scanned PDFs. The goal of this enhancement was to ensure that scanned or no-text PDFs are detected and handled gracefully during ingestion.

OCR is not implemented in this phase and remains a future enhancement.

---

## 2. Initial Gap

Before this change, PDF loading used text extraction through `pypdf`.

If a PDF page had no extractable text, the system did not explicitly classify it as a scanned or no-text PDF.

This made scanned PDF handling unclear and provided no ingestion diagnostic report.

---

## 3. Change

Updated the ingestion pipeline to support scanned PDF detection.

Updated files:

- `app/ingestion/loader.py`
- `app/ingestion/chunker.py`
- `scripts/ingest.py`

New behavior:

1. Text-based PDFs continue to be loaded with `pypdf` text extraction.
2. PDF pages with too little extractable text are counted as no-text pages.
3. PDFs with no extractable text are marked as scanned PDF candidates.
4. Scanned/no-text PDFs are skipped gracefully instead of failing ingestion.
5. Partial scanned PDFs are loaded with warning metadata.
6. Ingestion writes diagnostic reports.

Generated reports:

- `reports/ingestion/scanned_pdf_detection_report.json`
- `reports/ingestion/scanned_pdf_detection_report.md`

---

## 4. Validation Setup

Two PDF test files were generated with `reportlab`:

1. `98_text_pdf_detection_test.pdf`
   - contains a real text layer
   - expected to be loaded

2. `99_scanned_pdf_detection_test.pdf`
   - contains visual content without extractable text
   - used to simulate a scanned/no-text PDF
   - expected to be detected and skipped gracefully

---

## 5. Validation Result

Ingestion was executed with:

    python scripts/ingest.py

Final ingestion result:

    Supported files seen: 10
    Loaded documents: 9
    Skipped empty documents: 1
    PDF files checked: 2
    Scanned PDF candidates: 1
    Partial scanned PDF candidates: 1

Text-based PDF result:

    File: 98_text_pdf_detection_test.pdf
    Status: loaded
    Total pages: 1
    Pages with text: 1
    Pages without text: 0
    Extracted characters: 100
    Scanned PDF candidate: False
    OCR performed: False

Scanned/no-text PDF result:

    File: 99_scanned_pdf_detection_test.pdf
    Status: skipped_no_extractable_text
    Total pages: 1
    Pages with text: 0
    Pages without text: 1
    Extracted characters: 0
    Scanned PDF candidate: True
    OCR performed: False

The vector store was rebuilt successfully:

    Generated chunks: 31
    Total chunks stored: 31

---

## 6. PRD Impact

This enhancement addresses the scanned PDF part of the PRD at the ingestion robustness level.

Completed:

- text-based PDF ingestion
- scanned/no-text PDF detection
- graceful skip for no-text PDFs
- ingestion diagnostic report
- OCR status explicitly recorded as false

Not completed in this phase:

- OCR extraction from scanned PDF images

OCR remains a future enhancement.

---

## 7. Known Limitations

Current limitations:

- no OCR is performed
- scanned PDF detection is based on missing or low extracted text
- image-only PDFs are detected but not converted into text
- partially scanned PDFs may still require manual review or future OCR support

---

## 8. Future Enhancement

Future OCR support may include:

- `pdf2image`
- `pytesseract`
- page-level OCR fallback
- OCR confidence logging
- OCR-specific ingestion report fields
- scanned PDF evaluation cases

---

## 9. Conclusion

Scanned PDF detection and graceful handling is implemented and validated.

Final status:

    Completed at detection/graceful-handling level
    OCR remains future enhancement
