# PDF Detection and OCR Report

Project: AIA RAG Case Study Service
Report Type: Ingestion Diagnostics

## Summary

- Supported files seen: 10
- Loaded documents: 10
- Skipped empty documents: 0
- PDF files checked: 2
- Scanned PDF candidates: 1
- Partial scanned PDF candidates: 1
- PDFs with OCR performed: 1
- PDFs with OCR succeeded: 1

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
- OCR available: True
- OCR performed: False
- OCR succeeded: False
- Pages OCR attempted: 0
- Pages OCR succeeded: 0
- OCR status: Tesseract available: 5.4.0.20240606

Page-level results:

- Page 0: method=pypdf, pypdf_chars=100, ocr_performed=False, ocr_chars=0, ocr_error=None

### 99_scanned_pdf_detection_test.pdf

- Status: loaded_with_ocr
- Total pages: 1
- Pages with text: 0
- Pages without text: 1
- Extracted characters: 131
- Scanned PDF candidate: True
- OCR enabled: True
- OCR available: True
- OCR performed: True
- OCR succeeded: True
- Pages OCR attempted: 1
- Pages OCR succeeded: 1
- OCR status: Tesseract available: 5.4.0.20240606

Page-level results:

- Page 0: method=ocr, pypdf_chars=0, ocr_performed=True, ocr_chars=131, ocr_error=None
