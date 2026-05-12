# HTTP Load Evaluation Report

Date: 2026-05-12
Project: AIA RAG Case Study Service
Evaluation Type: HTTP-level Load Test

## Summary

- Total requests: 10
- Concurrency level: 5
- Successful requests: 10
- Failed requests: 0
- Success rate: 1.0
- Within 10s rate: 1.0
- Refusal rate: 0.0
- Average latency ms: 11.2
- P50 latency ms: 10.5
- P95 latency ms: 18.1
- Max latency ms: 19
- PRD pass: True

## Method

This evaluation sends concurrent HTTP POST requests to the FastAPI `/chat` endpoint.
It complements the internal latency and concurrency evaluation scripts by validating the API boundary.

Default pass criteria:

- concurrency_level >= 5
- success_rate = 1.0
- within_10s_rate >= 0.9

## Case Results

### http_audit_logging_1

- Status code: 200
- Success: True
- Within 10s: True
- Latency ms: 17
- Answer latency ms: 0
- Refused: False
- Refusal reason: None
- Source count: 5
- Error: None

### http_api_key_leak_2

- Status code: 200
- Success: True
- Within 10s: True
- Latency ms: 19
- Answer latency ms: 2
- Refused: False
- Refusal reason: None
- Source count: 5
- Error: None

### http_akp_endpoints_3

- Status code: 200
- Success: True
- Within 10s: True
- Latency ms: 13
- Answer latency ms: 2
- Refused: False
- Refusal reason: None
- Source count: 5
- Error: None

### http_cn_architecture_4

- Status code: 200
- Success: True
- Within 10s: True
- Latency ms: 15
- Answer latency ms: 1
- Refused: False
- Refusal reason: None
- Source count: 5
- Error: None

### http_retention_policy_5

- Status code: 200
- Success: True
- Within 10s: True
- Latency ms: 16
- Answer latency ms: 2
- Refused: False
- Refusal reason: None
- Source count: 5
- Error: None

### http_audit_logging_6

- Status code: 200
- Success: True
- Within 10s: True
- Latency ms: 8
- Answer latency ms: 2
- Refused: False
- Refusal reason: None
- Source count: 5
- Error: None

### http_api_key_leak_7

- Status code: 200
- Success: True
- Within 10s: True
- Latency ms: 6
- Answer latency ms: 0
- Refused: False
- Refusal reason: None
- Source count: 5
- Error: None

### http_akp_endpoints_8

- Status code: 200
- Success: True
- Within 10s: True
- Latency ms: 7
- Answer latency ms: 2
- Refused: False
- Refusal reason: None
- Source count: 5
- Error: None

### http_cn_architecture_9

- Status code: 200
- Success: True
- Within 10s: True
- Latency ms: 6
- Answer latency ms: 1
- Refused: False
- Refusal reason: None
- Source count: 5
- Error: None

### http_retention_policy_10

- Status code: 200
- Success: True
- Within 10s: True
- Latency ms: 5
- Answer latency ms: 0
- Refused: False
- Refusal reason: None
- Source count: 5
- Error: None
