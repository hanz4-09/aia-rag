# Secrets Scan Report

Project: AIA RAG Case Study Service
Report Type: Ingestion Safety / Secrets Scan

## Summary

- Root directory: C:\Users\dx\AppData\Local\Temp\tmpfe9v1e9v\raw
- Scanned files: 5
- Skipped files: 0
- Findings count: 3
- Ignored findings count: 1
- High severity count: 1
- Medium severity count: 2

## Findings

### private_key.txt:1

- Pattern: private_key_block
- Severity: high
- Matched preview: `-----B...[REDACTED]...----`

### secret_api_key.txt:1

- Pattern: generic_api_key_assignment
- Severity: medium
- Matched preview: `api_ke...[REDACTED]...6789`

### secret_token.env:1

- Pattern: generic_access_token_assignment
- Severity: medium
- Matched preview: `ACCESS...[REDACTED]...6789`


## Ignored Findings

### ignored_example_secret.txt:1

- Pattern: generic_api_key_assignment
- Severity: medium
- Matched preview: `api_ke...[REDACTED]...3456`
- Ignore marker: `secret-scan-ignore`
