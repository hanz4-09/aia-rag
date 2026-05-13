# Cache Evaluation Report

Date: 2026-05-13
Project: AIA RAG Case Study Service
Evaluation Type: Cache Behavior Evaluation

## Summary

- Total cases: 2
- Passing cases: 0
- Pass rate: 0.0
- First cache miss rate: 1.0
- Second cache hit rate: 0.0
- Latency improved rate: 0.0
- Avg keyword hit rate: 1.0
- PRD pass: False

## Method

Each case sends the same question twice with the same session_id.
The first request is expected to miss the cache.
The second request is expected to hit the cache.
The evaluator checks cache_hit values from structured JSONL logs.

## Case Results

### cache_audit_logging

- Question: What are the audit logging requirements?
- First cache hit: False
- Second cache hit: False
- First measured latency ms: 2841
- Second measured latency ms: 4440
- Latency improved: False
- Keyword hit rate: 1.0
- Pass: False

### cache_api_key_leak

- Question: API Key 泄露后应该怎么处理？
- First cache hit: False
- Second cache hit: False
- First measured latency ms: 6834
- Second measured latency ms: 8342
- Latency improved: False
- Keyword hit rate: 1.0
- Pass: False
