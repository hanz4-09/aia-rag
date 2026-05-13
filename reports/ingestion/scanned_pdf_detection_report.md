# PDF Detection and OCR Report

Project: AIA RAG Case Study Service
Report Type: Ingestion Diagnostics

## Summary

- Supported files seen: 11
- Loaded documents: 10
- Skipped empty documents: 1
- PDF files checked: 2
- Scanned PDF candidates: 1
- Partial scanned PDF candidates: 1
- PDFs with OCR performed: 0
- PDFs with OCR succeeded: 0

## Notes

- Text-based PDFs are loaded using pypdf text extraction.
- Scanned/no-text PDF pages can be rendered and processed by OCR when OCR is enabled and Tesseract is available.
- OCR result availability depends on local Tesseract installation and configured language data.

## PDF Details

### 98_text_pdf_detection_test.pdf

- Status: loaded
- Total pages: 1
- Pages with text: 1
- Pages without text: 0
- Extracted characters: 100
- Scanned PDF candidate: False
- OCR enabled: True
- OCR available: False
- OCR performed: False
- OCR succeeded: False
- Pages OCR attempted: 0
- Pages OCR succeeded: 0
- OCR status: OCR Python dependencies unavailable: No module named 'fitz'

Page-level results:

- Page 0: method=pypdf, pypdf_chars=100, ocr_performed=False, ocr_chars=0, ocr_error=None

### 99_scanned_pdf_detection_test.pdf

- Status: skipped_no_extractable_text
- Total pages: 1
- Pages with text: 0
- Pages without text: 1
- Extracted characters: 0
- Scanned PDF candidate: True
- OCR enabled: True
- OCR available: False
- OCR performed: False
- OCR succeeded: False
- Pages OCR attempted: 0
- Pages OCR succeeded: 0
- OCR status: OCR Python dependencies unavailable: No module named 'fitz'

Page-level results:

- Page 0: method=pypdf, pypdf_chars=0, ocr_performed=False, ocr_chars=0, ocr_error=None
