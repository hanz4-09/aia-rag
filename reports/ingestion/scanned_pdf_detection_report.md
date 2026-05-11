# Scanned PDF Detection Report

Project: AIA RAG Case Study Service
Report Type: Ingestion Diagnostics

## Summary

- Supported files seen: 10
- Loaded documents: 9
- Skipped empty documents: 1
- PDF files checked: 2
- Scanned PDF candidates: 1
- Partial scanned PDF candidates: 1

## Notes

- OCR is not performed in the current implementation.
- Text-based PDFs are loaded using pypdf text extraction.
- PDFs with no extractable text are detected and skipped gracefully.
- PDFs with some low-text pages are loaded with a warning.

## PDF Details

### 98_text_pdf_detection_test.pdf

- Status: loaded
- Total pages: 1
- Pages with text: 1
- Pages without text: 0
- Extracted characters: 100
- Scanned PDF candidate: False
- OCR performed: False

### 99_scanned_pdf_detection_test.pdf

- Status: skipped_no_extractable_text
- Total pages: 1
- Pages with text: 0
- Pages without text: 1
- Extracted characters: 0
- Scanned PDF candidate: True
- OCR performed: False
