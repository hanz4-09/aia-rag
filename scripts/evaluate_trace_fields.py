import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

LOG_PATH = PROJECT_ROOT / "logs" / "rag_service.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
TODAY = time.strftime("%Y-%m-%d")
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_trace_fields_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_trace_fields_eval.md"


REQUIRED_TRACE_FIELDS = [
    "request_id",
    "trace_id",
    "span_id",
    "parent_span_id",
    "memory_span_id",
    "retrieval_span_id",
    "rerank_span_id",
    "generation_span_id",
    "trace_schema_version",
]


def load_logs() -> List[Dict[str, Any]]:
    if not LOG_PATH.exists():
        return []

    records = []

    with LOG_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return records


def evaluate_record(record: Dict[str, Any], index: int) -> Dict[str, Any]:
    missing_fields = [
        field for field in REQUIRED_TRACE_FIELDS
        if field not in record
    ]

    empty_required_fields = [
        field for field in REQUIRED_TRACE_FIELDS
        if field != "parent_span_id"
        and field in record
        and record.get(field) in ("", None)
    ]

    trace_id_matches_request_id = (
        record.get("trace_id") == record.get("request_id")
    )

    span_fields = [
        "span_id",
        "memory_span_id",
        "retrieval_span_id",
        "rerank_span_id",
        "generation_span_id",
    ]

    span_format_ok = all(
        isinstance(record.get(field), str)
        and len(record.get(field)) >= 8
        for field in span_fields
    )

    schema_version_ok = record.get("trace_schema_version") == "otel-lite-v1"

    pass_result = all(
        [
            not missing_fields,
            not empty_required_fields,
            trace_id_matches_request_id,
            span_format_ok,
            schema_version_ok,
        ]
    )

    return {
        "row_index": index,
        "request_id": record.get("request_id", ""),
        "trace_id": record.get("trace_id", ""),
        "span_id": record.get("span_id", ""),
        "memory_span_id": record.get("memory_span_id", ""),
        "retrieval_span_id": record.get("retrieval_span_id", ""),
        "rerank_span_id": record.get("rerank_span_id", ""),
        "generation_span_id": record.get("generation_span_id", ""),
        "trace_schema_version": record.get("trace_schema_version", ""),
        "missing_fields": "|".join(missing_fields),
        "empty_required_fields": "|".join(empty_required_fields),
        "trace_id_matches_request_id": trace_id_matches_request_id,
        "span_format_ok": span_format_ok,
        "schema_version_ok": schema_version_ok,
        "pass": pass_result,
    }


def summarize(results: List[Dict[str, Any]], total_logs: int) -> Dict[str, Any]:
    total = len(results)
    passing = sum(1 for item in results if item["pass"])

    return {
        "total_logs": total_logs,
        "trace_enabled_logs": total,
        "passing_count": passing,
        "pass_rate": round(passing / total, 4) if total else 0.0,
        "trace_coverage_rate": round(total / total_logs, 4) if total_logs else 0.0,
        "prd_pass": total > 0 and passing == total,
    }


def write_csv(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "row_index",
        "request_id",
        "trace_id",
        "span_id",
        "memory_span_id",
        "retrieval_span_id",
        "rerank_span_id",
        "generation_span_id",
        "trace_schema_version",
        "missing_fields",
        "empty_required_fields",
        "trace_id_matches_request_id",
        "span_format_ok",
        "schema_version_ok",
        "pass",
        "total_logs",
        "trace_enabled_logs",
        "passing_count",
        "pass_rate",
        "trace_coverage_rate",
        "prd_pass",
    ]

    with CSV_REPORT_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        summary_row = {field: "" for field in fieldnames}
        summary_row.update({"row_type": "summary", **summary})
        writer.writerow(summary_row)

        for result in results:
            row = {field: "" for field in fieldnames}
            row.update(result)
            row["row_type"] = "detail"
            writer.writerow(row)


def write_markdown(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    lines = [
        "# Trace Fields Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: OpenTelemetry-style Trace Field Validation",
        "",
        "## Summary",
        "",
        f"- Total logs: {summary['total_logs']}",
        f"- Trace-enabled logs: {summary['trace_enabled_logs']}",
        f"- Passing count: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
        f"- Trace coverage rate: {summary['trace_coverage_rate']}",
        f"- PRD pass: {summary['prd_pass']}",
        "",
        "## Required Fields",
        "",
    ]

    for field in REQUIRED_TRACE_FIELDS:
        lines.append(f"- {field}")

    lines.extend(
        [
            "",
            "## Method",
            "",
            "This evaluation reads structured runtime logs from `logs/rag_service.jsonl`.",
            "It validates whether trace-enabled log records contain OpenTelemetry-style lightweight trace fields.",
            "",
            "The current schema uses `trace_id = request_id` and stage-level span identifiers for memory, retrieval, rerank, and generation.",
            "",
            "## Case Results",
            "",
        ]
    )

    for result in results[-10:]:
        lines.extend(
            [
                f"### Row {result['row_index']}",
                "",
                f"- Request ID: {result['request_id']}",
                f"- Trace ID: {result['trace_id']}",
                f"- Span ID: {result['span_id']}",
                f"- Trace schema version: {result['trace_schema_version']}",
                f"- Missing fields: {result['missing_fields'] or 'None'}",
                f"- Empty required fields: {result['empty_required_fields'] or 'None'}",
                f"- Trace ID matches request ID: {result['trace_id_matches_request_id']}",
                f"- Span format OK: {result['span_format_ok']}",
                f"- Schema version OK: {result['schema_version_ok']}",
                f"- Pass: {result['pass']}",
                "",
            ]
        )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    logs = load_logs()

    trace_logs = [
        record for record in logs
        if "trace_id" in record or "trace_schema_version" in record
    ]

    results = [
        evaluate_record(record, index)
        for index, record in enumerate(trace_logs, start=1)
    ]

    summary = summarize(results, len(logs))

    write_csv(results, summary)
    write_markdown(results, summary)

    print("=" * 60)
    print("TRACE FIELDS EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total logs:           {summary['total_logs']}")
    print(f"  Trace-enabled logs:   {summary['trace_enabled_logs']}")
    print(f"  Passing count:        {summary['passing_count']}")
    print(f"  Pass rate:            {summary['pass_rate']}")
    print(f"  Trace coverage rate:  {summary['trace_coverage_rate']}")
    print(f"  PRD Status:           {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")

    if summary["trace_enabled_logs"] == 0:
        print()
        print("No trace-enabled logs found.")
        print("Generate one /chat request after patching app/api/chat.py, then rerun this script.")


if __name__ == "__main__":
    main()
