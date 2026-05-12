# Error Handling Evaluation Report

Date: 2026-05-12
Project: AIA RAG Case Study Service
Evaluation Type: Runtime Error Handling / Structured Error Logging

## Summary

- Total cases: 2
- Passing cases: 2
- Pass rate: 1.0
- Handled error rate: 1.0
- PRD pass: True

## Case Results

### retrieval_failure_returns_system_error

- Stage: retrieval
- Status code: 200
- Refused: True
- Refusal reason: SYSTEM_ERROR
- Log error stage: retrieval
- Log error type: RuntimeError
- Log error handled: True
- Trace schema version: otel-lite-v1
- Pass: True

### generation_failure_returns_system_error

- Stage: generation
- Status code: 200
- Refused: True
- Refusal reason: SYSTEM_ERROR
- Log error stage: generation
- Log error type: RuntimeError
- Log error handled: True
- Trace schema version: otel-lite-v1
- Pass: True
