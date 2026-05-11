# Cache Evaluation Report

Date: 2026-05-11
Project: AIA RAG Case Study Service
Evaluation Type: Cache Behavior Evaluation

## Summary

- Total cases: 2
- Passing cases: 2
- Pass rate: 1.0
- First cache miss rate: 1.0
- Second cache hit rate: 1.0
- Latency improved rate: 1.0
- Avg keyword hit rate: 1.0
- PRD pass: True

## Method

Each case sends the same question twice with the same session_id.
The first request is expected to miss the cache.
The second request is expected to hit the cache.
The evaluator checks cache_hit values from structured JSONL logs.

## Case Results

### cache_audit_logging

- Question: What are the audit logging requirements?
- First cache hit: False
- Second cache hit: True
- First measured latency ms: 5161
- Second measured latency ms: 6
- Latency improved: True
- Keyword hit rate: 1.0
- Pass: True

### cache_api_key_leak

- Question: API Key 泄露后应该怎么处理？
- First cache hit: False
- Second cache hit: True
- First measured latency ms: 2750
- Second measured latency ms: 7
- Latency improved: True
- Keyword hit rate: 1.0
- Pass: True
