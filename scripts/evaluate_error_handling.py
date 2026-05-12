import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.main import app
import app.api.chat as chat_module


OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
LOG_PATH = PROJECT_ROOT / "logs" / "rag_service.jsonl"
TODAY = time.strftime("%Y-%m-%d")
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_error_handling_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_error_handling_eval.md"


def load_latest_log() -> Dict[str, Any]:
    if not LOG_PATH.exists():
        return {}

    lines = [
        line.strip()
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if not lines:
        return {}

    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {}


def run_case(case_id: str, stage: str) -> Dict[str, Any]:
    client = TestClient(app)

    session_id = f"error-handling-{case_id}-{int(time.time())}"

    if stage == "retrieval":
        patch_target = patch.object(
            chat_module.retriever,
            "retrieve",
            side_effect=RuntimeError("simulated retrieval failure"),
        )
    elif stage == "generation":
        patch_target = patch.object(
            chat_module.generator,
            "generate",
            side_effect=RuntimeError("simulated generation failure"),
        )
    else:
        raise ValueError(f"Unsupported stage: {stage}")

    with patch_target:
        response = client.post(
            "/chat",
            json={
                "question": "What are the audit logging requirements?",
                "session_id": session_id,
            },
        )

    latest_log = load_latest_log()

    status_code = response.status_code

    try:
        body = response.json()
    except Exception:
        body = {}

    refused = body.get("refused")
    refusal_reason = body.get("refusal_reason")
    answer = body.get("answer", "")

    log_error_stage = latest_log.get("error_stage")
    log_error_type = latest_log.get("error_type")
    log_error_message = latest_log.get("error_message")
    log_error_handled = latest_log.get("error_handled")
    log_trace_schema_version = latest_log.get("trace_schema_version")

    pass_result = all(
        [
            status_code == 200,
            refused is True,
            refusal_reason == "SYSTEM_ERROR",
            log_error_stage == stage,
            log_error_type == "RuntimeError",
            "simulated" in (log_error_message or ""),
            log_error_handled is True,
            log_trace_schema_version == "otel-lite-v1",
        ]
    )

    return {
        "case_id": case_id,
        "stage": stage,
        "status_code": status_code,
        "refused": refused,
        "refusal_reason": refusal_reason,
        "answer_preview": answer[:200].replace("\n", " "),
        "log_error_stage": log_error_stage,
        "log_error_type": log_error_type,
        "log_error_message": log_error_message,
        "log_error_handled": log_error_handled,
        "log_trace_schema_version": log_trace_schema_version,
        "pass": pass_result,
    }


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    passing = sum(1 for item in results if item["pass"])
    handled_errors = sum(1 for item in results if item["log_error_handled"] is True)

    return {
        "total_cases": total,
        "passing_count": passing,
        "pass_rate": round(passing / total, 4) if total else 0,
        "handled_error_rate": round(handled_errors / total, 4) if total else 0,
        "prd_pass": passing == total,
    }


def write_csv(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "case_id",
        "stage",
        "status_code",
        "refused",
        "refusal_reason",
        "answer_preview",
        "log_error_stage",
        "log_error_type",
        "log_error_message",
        "log_error_handled",
        "log_trace_schema_version",
        "pass",
        "total_cases",
        "passing_count",
        "pass_rate",
        "handled_error_rate",
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
        "# Error Handling Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: Runtime Error Handling / Structured Error Logging",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passing cases: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
        f"- Handled error rate: {summary['handled_error_rate']}",
        f"- PRD pass: {summary['prd_pass']}",
        "",
        "## Case Results",
        "",
    ]

    for result in results:
        lines.extend(
            [
                f"### {result['case_id']}",
                "",
                f"- Stage: {result['stage']}",
                f"- Status code: {result['status_code']}",
                f"- Refused: {result['refused']}",
                f"- Refusal reason: {result['refusal_reason']}",
                f"- Log error stage: {result['log_error_stage']}",
                f"- Log error type: {result['log_error_type']}",
                f"- Log error handled: {result['log_error_handled']}",
                f"- Trace schema version: {result['log_trace_schema_version']}",
                f"- Pass: {result['pass']}",
                "",
            ]
        )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    results = [
        run_case("retrieval_failure_returns_system_error", "retrieval"),
        run_case("generation_failure_returns_system_error", "generation"),
    ]

    summary = summarize(results)

    for index, result in enumerate(results, start=1):
        status = "✅" if result["pass"] else "❌"
        print(
            f"[{index}/{len(results)}] {result['case_id']} "
            f"{status} pass={result['pass']}, "
            f"stage={result['stage']}, "
            f"status={result['status_code']}, "
            f"reason={result['refusal_reason']}"
        )

        if not result["pass"]:
            print(f"  log_error_stage={result['log_error_stage']}")
            print(f"  log_error_type={result['log_error_type']}")
            print(f"  log_error_message={result['log_error_message']}")

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("ERROR HANDLING EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:         {summary['total_cases']}")
    print(f"  Passing cases:       {summary['passing_count']}")
    print(f"  Pass rate:           {summary['pass_rate']}")
    print(f"  Handled error rate:  {summary['handled_error_rate']}")
    print(f"  PRD Status:          {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
