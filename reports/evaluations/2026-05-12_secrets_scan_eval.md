# Secrets Scan Evaluation Report

Date: 2026-05-12
Project: AIA RAG Case Study Service
Evaluation Type: Ingestion Secrets Scan / False Positive Guard

## Summary

- Total cases: 1
- Passing cases: 1
- Pass rate: 1.0
- PRD pass: True

## Case Results

### secrets_scan_detects_secrets_without_policy_false_positive

- Scanned files: 5
- Findings count: 3
- High severity count: 1
- Medium severity count: 2
- Safe policy file not flagged: True
- Ignored example not active: True
- Ignored example recorded: True
- Ignored findings count: 1
- Ignored pattern names: generic_api_key_assignment
- API key detected: True
- Token detected: True
- Private key detected: True
- Pattern names: generic_access_token_assignment|generic_api_key_assignment|private_key_block
- Pass: True
