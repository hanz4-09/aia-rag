# Trace Fields Evaluation Report

Date: 2026-05-12
Project: AIA RAG Case Study Service
Evaluation Type: OpenTelemetry-style Trace Field Validation

## Summary

- Total logs: 40
- Trace-enabled logs: 1
- Passing count: 1
- Pass rate: 1.0
- Trace coverage rate: 0.025
- PRD pass: True

## Required Fields

- request_id
- trace_id
- span_id
- parent_span_id
- memory_span_id
- retrieval_span_id
- rerank_span_id
- generation_span_id
- trace_schema_version

## Method

This evaluation reads structured runtime logs from `logs/rag_service.jsonl`.
It validates whether trace-enabled log records contain OpenTelemetry-style lightweight trace fields.

The current schema uses `trace_id = request_id` and stage-level span identifiers for memory, retrieval, rerank, and generation.

## Case Results

### Row 1

- Request ID: d728e9b2-00e2-4c68-b1ff-7831130e342d
- Trace ID: d728e9b2-00e2-4c68-b1ff-7831130e342d
- Span ID: ec134771040c4928
- Trace schema version: otel-lite-v1
- Missing fields: None
- Empty required fields: None
- Trace ID matches request ID: True
- Span format OK: True
- Schema version OK: True
- Pass: True
