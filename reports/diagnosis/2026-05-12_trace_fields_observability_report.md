# Optimization Report: OpenTelemetry-style Trace Fields

Date: 2026-05-12  
Project: AIA RAG Case Study Service  
Report Type: Observability Enhancement Report  
Optimization Area: Structured Logging / Traceability / OpenTelemetry-style Fields  
Related Components: `app/api/chat.py`, `scripts/evaluate_trace_fields.py`, `logs/rag_service.jsonl`

---

## 1. Purpose

This report documents the addition of OpenTelemetry-style trace fields to the runtime structured logs.

The project already had structured JSONL logging with request-level metrics, retrieval metadata, generation metadata, refusal information, cache status, and latency fields.

This enhancement adds lightweight trace identifiers to improve request-level observability and future troubleshooting.

---

## 2. Change

Enhanced:

    app/api/chat.py

Added the following trace fields to runtime logs:

- `trace_id`
- `span_id`
- `parent_span_id`
- `memory_span_id`
- `retrieval_span_id`
- `rerank_span_id`
- `generation_span_id`
- `trace_schema_version`

Current schema:

    trace_schema_version = otel-lite-v1

Current design:

    trace_id = request_id

Stage-level span fields are generated for:

- memory
- retrieval
- rerank
- generation

Added validation script:

    scripts/evaluate_trace_fields.py

---

## 3. Validation Method

A new `/chat` request was generated using FastAPI TestClient.

The resulting runtime log was inspected and then validated with:

    python scripts/evaluate_trace_fields.py

The evaluator checks:

- all required trace fields exist
- required fields are non-empty
- `trace_id` matches `request_id`
- stage span IDs follow expected string format
- `trace_schema_version` equals `otel-lite-v1`

---

## 4. Final Evaluation Result

Final trace evaluation result:

    total_logs = 40
    trace_enabled_logs = 1
    passing_count = 1
    pass_rate = 1.0
    trace_coverage_rate = 0.025
    PRD Status = PASS

The low trace coverage rate is expected because older logs were generated before this enhancement. The latest trace-enabled log passed validation.

Output reports:

    reports/evaluations/2026-05-12_trace_fields_eval.csv
    reports/evaluations/2026-05-12_trace_fields_eval.md

---

## 5. Example Trace-enabled Log Fields

The latest runtime log includes:

    trace_id
    span_id
    parent_span_id
    memory_span_id
    retrieval_span_id
    rerank_span_id
    generation_span_id
    trace_schema_version

The log also preserves existing observability fields, including:

    retrieval_latency_ms
    generation_latency_ms
    total_latency_ms
    retrieved_sources
    model_name
    cache_hit
    refused
    refusal_reason

---

## 6. PRD Impact

The PRD requires structured runtime logs and operational reporting.

This enhancement strengthens the observability requirement by adding trace-style identifiers that make it easier to correlate request-level execution stages.

It prepares the project for future OpenTelemetry integration without adding external infrastructure.

---

## 7. Limitations

Current limitations:

- This is a lightweight OpenTelemetry-style schema, not full OpenTelemetry SDK integration.
- Stage-level spans are identifiers only; they are not exported to a tracing backend.
- `parent_span_id` is currently null because there is no distributed upstream trace context.
- Old logs do not contain trace fields.
- Trace coverage increases only for newly generated logs.
- No Prometheus, Jaeger, Grafana, or OTLP exporter is currently configured.

---

## 8. Future Work

Future improvements may include:

- real OpenTelemetry SDK integration
- OTLP exporter
- Jaeger or Tempo tracing backend
- trace propagation across services
- nested span timing for memory, retrieval, rerank, and generation
- trace-level error and timeout tagging
- dashboard integration

---

## 9. Conclusion

OpenTelemetry-style Trace Fields is completed.

Final status:

    PASS

The project now records lightweight trace fields in new runtime JSONL logs and validates them with a dedicated evaluation script.
