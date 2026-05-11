# PII Redaction Evaluation Report

Date: 2026-05-11
Project: AIA RAG Case Study Service
Evaluation Type: PII Redaction Evaluation

## Summary

- Total cases: 7
- Passing cases: 7
- Pass rate: 1.0
- Forbidden clean rate: 1.0
- Placeholder present rate: 1.0
- PRD pass: True

## Method

Each case sends text containing one or more PII-like values into the redaction function.
The evaluator checks that raw sensitive values are removed and expected placeholders are present.

## Case Results

### email_redaction

- Input: My email is ziwei@example.com.
- Redacted: My email is [EMAIL]
- Forbidden clean: True
- Placeholders present: True
- Leaked values: None
- Missing placeholders: None
- Pass: True

### phone_redaction

- Input: My phone number is 13812345678.
- Redacted: My phone number is [PHONE].
- Forbidden clean: True
- Placeholders present: True
- Leaked values: None
- Missing placeholders: None
- Pass: True

### api_key_redaction

- Input: The api_key=abc123secret should not be logged.
- Redacted: The api_key=[REDACTED_SECRET] should not be logged.
- Forbidden clean: True
- Placeholders present: True
- Leaked values: None
- Missing placeholders: None
- Pass: True

### token_redaction

- Input: access_token=tok_live_123456789 must be hidden.
- Redacted: access_token=[REDACTED_SECRET] must be hidden.
- Forbidden clean: True
- Placeholders present: True
- Leaked values: None
- Missing placeholders: None
- Pass: True

### secret_redaction

- Input: secret=my_private_secret_value should be redacted.
- Redacted: secret=[REDACTED_SECRET] should be redacted.
- Forbidden clean: True
- Placeholders present: True
- Leaked values: None
- Missing placeholders: None
- Pass: True

### id_number_redaction

- Input: My ID number is 310101199001011234.
- Redacted: My ID number is [ID_NUMBER].
- Forbidden clean: True
- Placeholders present: True
- Leaked values: None
- Missing placeholders: None
- Pass: True

### mixed_pii_redaction

- Input: Contact me at test.user@example.com or 13800138000. api_key=test_secret_123 should not appear.
- Redacted: Contact me at [EMAIL] or [PHONE]. api_key=[REDACTED_SECRET] should not appear.
- Forbidden clean: True
- Placeholders present: True
- Leaked values: None
- Missing placeholders: None
- Pass: True
