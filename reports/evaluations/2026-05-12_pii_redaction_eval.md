# PII Redaction Evaluation Report

Date: 2026-05-12
Project: AIA RAG Case Study Service
Evaluation Type: PII Redaction / False Positive / False Negative Benchmark

## Summary

- Total cases: 13
- Passing cases: 13
- Pass rate: 1.0
- True-positive cases: 7
- True-positive pass rate: 1.0
- False-positive cases: 6
- False-positive clean rate: 1.0
- Forbidden clean rate: 1.0
- Placeholder present rate: 1.0
- Unexpected placeholder clean rate: 1.0
- PRD pass: True

## Method

The evaluation includes two case types:

1. True-positive cases: inputs contain sensitive values and must be redacted.
2. False-positive cases: inputs do not contain raw PII and should not be over-redacted.

The evaluator checks that raw sensitive values are removed, expected placeholders are present,
and non-sensitive policy or technical text is not incorrectly redacted.

## Case Results

### email_redaction

- Case type: true_positive
- Input: My email is ziwei@example.com.
- Redacted: My email is [EMAIL]
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: True
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### phone_redaction

- Case type: true_positive
- Input: My phone number is 13812345678.
- Redacted: My phone number is [PHONE].
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: True
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### api_key_redaction

- Case type: true_positive
- Input: The api_key=abc123secret should not be logged.
- Redacted: The api_key=[REDACTED_SECRET] should not be logged.
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: True
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### token_redaction

- Case type: true_positive
- Input: access_token=tok_live_123456789 must be hidden.
- Redacted: access_token=[REDACTED_SECRET] must be hidden.
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: True
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### secret_redaction

- Case type: true_positive
- Input: secret=my_private_secret_value should be redacted.
- Redacted: secret=[REDACTED_SECRET] should be redacted.
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: True
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### id_number_redaction

- Case type: true_positive
- Input: My ID number is 310101199001011234.
- Redacted: My ID number is [ID_NUMBER].
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: True
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### mixed_pii_redaction

- Case type: true_positive
- Input: Contact me at test.user@example.com or 13800138000. api_key=test_secret_123 should not appear.
- Redacted: Contact me at [EMAIL] or [PHONE]. api_key=[REDACTED_SECRET] should not appear.
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: True
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### normal_year_not_id

- Case type: false_positive
- Input: The retention policy was updated in 2026 and reviewed in 2025.
- Redacted: The retention policy was updated in 2026 and reviewed in 2025.
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: False
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### normal_latency_numbers_not_phone

- Case type: false_positive
- Input: The p50 latency is 751 ms and the p95 latency is 3355 ms.
- Redacted: The p50 latency is 751 ms and the p95 latency is 3355 ms.
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: False
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### api_key_policy_concept_not_secret

- Case type: false_positive
- Input: API Key leakage must be reported within 24 hours.
- Redacted: API Key leakage must be reported within 24 hours.
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: False
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### token_policy_concept_not_secret

- Case type: false_positive
- Input: Access token values must not be stored in plain text logs.
- Redacted: Access token values must not be stored in plain text logs.
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: False
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### employee_policy_numbers_not_phone

- Case type: false_positive
- Input: Employees must complete 2 trainings within 30 days.
- Redacted: Employees must complete 2 trainings within 30 days.
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: False
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True

### technical_endpoint_not_email

- Case type: false_positive
- Input: The service exposes /health and /chat endpoints.
- Redacted: The service exposes /health and /chat endpoints.
- Forbidden clean: True
- Placeholders present: True
- False-positive clean: True
- Redacted changed: False
- Leaked values: None
- Missing placeholders: None
- Unexpected placeholders: None
- Pass: True
