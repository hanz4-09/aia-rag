# Corpus Growth Regression Evaluation Report

Date: 2026-05-13
Project: AIA RAG Case Study Service
Evaluation Type: Corpus Growth / Golden Retrieval Regression

## Summary

- Total cases: 7
- Passing cases: 7
- Pass rate: 1.0
- Top-1 hit rate: 0.7143
- Top-3 hit rate: 1.0
- Top-5 hit rate: 1.0
- Required Top-K hit rate: 1.0
- Average expected source rank: 1.2857
- Max expected source rank: 2
- Average keyword hit rate: 1.0
- PRD pass: True

## Method

This evaluation runs a fixed set of golden retrieval queries after ingestion.
It verifies whether important expected sources still appear within the required Top-K range.

This is intended as a regression guard for future corpus growth.
When new files are added to `data/raw/`, the vector store should be rebuilt and this script should be rerun.

Recommended workflow:

    python scripts/ingest.py
    python scripts/evaluate_corpus_regression.py
    python scripts/evaluate_context_precision.py

## Case Results

### golden_audit_logging_requirements

- Category: compliance_en
- Query: What are the audit logging requirements?
- Expected source: 03_compliance_guide_en.txt
- Expected source rank: 1
- Required Top-K: 3
- Top-1 hit: True
- Top-3 hit: True
- Top-5 hit: True
- Required Top-K hit: True
- Keyword hit rate: 1.0
- Missing keywords: None
- Pass: True
- Retrieved sources: 03_compliance_guide_en.txt|99_scanned_pdf_detection_test.pdf|03_compliance_guide_en.txt|03_compliance_guide_en.txt|98_text_pdf_detection_test.pdf

### golden_audit_log_retention

- Category: compliance_en
- Query: How long should audit logs for privileged operations be retained?
- Expected source: 03_compliance_guide_en.txt
- Expected source rank: 2
- Required Top-K: 3
- Top-1 hit: False
- Top-3 hit: True
- Top-5 hit: True
- Required Top-K hit: True
- Keyword hit rate: 1.0
- Missing keywords: None
- Pass: True
- Retrieved sources: 99_scanned_pdf_detection_test.pdf|03_compliance_guide_en.txt|03_compliance_guide_en.txt|98_text_pdf_detection_test.pdf|03_compliance_guide_en.txt

### golden_api_key_leak_cn

- Category: security_cn
- Query: API Key 泄露后应该怎么处理？
- Expected source: 04_data_security_policy_cn.txt
- Expected source rank: 1
- Required Top-K: 3
- Top-1 hit: True
- Top-3 hit: True
- Top-5 hit: True
- Required Top-K hit: True
- Keyword hit rate: 1.0
- Missing keywords: None
- Pass: True
- Retrieved sources: 04_data_security_policy_cn.txt|04_data_security_policy_cn.txt|08_pii_redaction_spec_cn.txt|08_pii_redaction_spec_cn.txt|01_employee_handbook_en.txt

### golden_api_key_employee_report_cn

- Category: security_cn
- Query: 员工怀疑 API Key 泄露后应该多久内报告？
- Expected source: 02_employee_handbook_cn.txt
- Expected source rank: 2
- Required Top-K: 5
- Top-1 hit: False
- Top-3 hit: True
- Top-5 hit: True
- Required Top-K hit: True
- Keyword hit rate: 1.0
- Missing keywords: None
- Pass: True
- Retrieved sources: 04_data_security_policy_cn.txt|02_employee_handbook_cn.txt|04_data_security_policy_cn.txt|01_employee_handbook_en.txt|99_scanned_pdf_detection_test.pdf

### golden_annual_leave_policy

- Category: hr_policy
- Query: What is the annual leave policy and manager review time?
- Expected source: 01_employee_handbook_en.txt
- Expected source rank: 1
- Required Top-K: 5
- Top-1 hit: True
- Top-3 hit: True
- Top-5 hit: True
- Required Top-K hit: True
- Keyword hit rate: 1.0
- Missing keywords: None
- Pass: True
- Retrieved sources: 01_employee_handbook_en.txt|01_employee_handbook_en.txt|05_akp_technical_specification_en.txt|01_employee_handbook_en.txt|02_employee_handbook_cn.txt

### golden_ocr_api_key_incident

- Category: ocr_en
- Query: API Key incidents must be reported within 24 hours
- Expected source: 99_scanned_pdf_detection_test.pdf
- Expected source rank: 1
- Required Top-K: 3
- Top-1 hit: True
- Top-3 hit: True
- Top-5 hit: True
- Required Top-K hit: True
- Keyword hit rate: 1.0
- Missing keywords: None
- Pass: True
- Retrieved sources: 99_scanned_pdf_detection_test.pdf|01_employee_handbook_en.txt|03_compliance_guide_en.txt|04_data_security_policy_cn.txt|02_employee_handbook_cn.txt

### golden_pii_redaction_format_cn

- Category: privacy_cn
- Query: 敏感数据脱敏的格式是什么？
- Expected source: 08_pii_redaction_spec_cn.txt
- Expected source rank: 1
- Required Top-K: 5
- Top-1 hit: True
- Top-3 hit: True
- Top-5 hit: True
- Required Top-K hit: True
- Keyword hit rate: 1.0
- Missing keywords: None
- Pass: True
- Retrieved sources: 08_pii_redaction_spec_cn.txt|08_pii_redaction_spec_cn.txt|08_pii_redaction_spec_cn.txt|08_pii_redaction_spec_cn.txt|08_pii_redaction_spec_cn.txt
