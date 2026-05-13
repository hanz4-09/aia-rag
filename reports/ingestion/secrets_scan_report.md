# Secrets Scan Report

Project: AIA RAG Case Study Service
Report Type: Ingestion Safety / Secrets Scan

## Summary

- Root directory: data\raw
- Scanned files: 9
- Skipped files: 2
- Findings count: 0
- Ignored findings count: 2
- High severity count: 0
- Medium severity count: 0

## Findings

No unignored secret-like patterns were detected.

## Ignored Findings

### 08_pii_redaction_spec_cn.txt:52

- Pattern: generic_api_key_assignment
- Severity: medium
- Matched preview: `api_ke...[REDACTED]...cdef`
- Ignore marker: `secret-scan-ignore`

### 08_pii_redaction_spec_cn.txt:60

- Pattern: generic_access_token_assignment
- Severity: medium
- Matched preview: `token:...[REDACTED]...7890`
- Ignore marker: `secret-scan-ignore`
