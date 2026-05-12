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
from app.rag.generator import FallbackGenerator


OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
LOG_PATH = PROJECT_ROOT / "logs" / "rag_service.jsonl"
TODAY = time.strftime("%Y-%m-%d")
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_provider_fallback_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_provider_fallback_eval.md"


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


def evaluate_fallback_generator_present() -> Dict[str, Any]:
    is_fallback_generator = isinstance(chat_module.generator, FallbackGenerator)

    return {
        "case_id": "fallback_generator_is_configured",
        "status_code": "",
        "refused": "",
        "fallback_applied": "",
        "fallback_reason": "",
        "primary_generator_type": "",
        "fallback_generator_type": "",
        "final_generator_type": "",
        "log_fallback_applied": "",
        "log_fallback_reason": "",
        "pass": is_fallback_generator,
    }


def evaluate_primary_llm_failure_falls_back_to_extractive() -> Dict[str, Any]:
    if not isinstance(chat_module.generator, FallbackGenerator):
        return {
            "case_id": "primary_llm_failure_falls_back_to_extractive",
            "status_code": "",
            "refused": "",
            "fallback_applied": "",
            "fallback_reason": "",
            "primary_generator_type": "",
            "fallback_generator_type": "",
            "final_generator_type": "",
            "log_fallback_applied": "",
            "log_fallback_reason": "",
            "pass": False,
        }

    client = TestClient(app)

    with patch.object(
        chat_module.generator.primary_generator,
        "generate",
        side_effect=RuntimeError("simulated primary LLM failure"),
    ):
        response = client.post(
            "/chat",
            json={
                "question": "What are the audit logging requirements?",
                "session_id": f"provider-fallback-eval-{int(time.time())}",
            },
        )

    body = response.json()
    latest_log = load_latest_log()

    status_code = response.status_code
    refused = body.get("refused")
    answer = body.get("answer", "")

    log_fallback_applied = latest_log.get("fallback_applied")
    log_fallback_reason = latest_log.get("fallback_reason")
    log_primary_generator_type = latest_log.get("primary_generator_type")
    log_fallback_generator_type = latest_log.get("fallback_generator_type")
    log_final_generator_type = latest_log.get("final_generator_type")
    log_fallback_error_type = latest_log.get("fallback_error_type")

    pass_result = all(
        [
            status_code == 200,
            refused is False,
            "Based on the retrieved internal knowledge" in answer,
            log_fallback_applied is True,
            log_fallback_reason == "primary_generation_error",
            log_primary_generator_type == "llm",
            log_fallback_generator_type == "extractive",
            log_final_generator_type == "extractive",
            log_fallback_error_type == "RuntimeError",
        ]
    )

    return {
        "case_id": "primary_llm_failure_falls_back_to_extractive",
        "status_code": status_code,
        "refused": refused,
        "fallback_applied": True,
        "fallback_reason": "primary_generation_error",
        "primary_generator_type": log_primary_generator_type,
        "fallback_generator_type": log_fallback_generator_type,
        "final_generator_type": log_final_generator_type,
        "log_fallback_applied": log_fallback_applied,
        "log_fallback_reason": log_fallback_reason,
        "pass": pass_result,
    }


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    passing = sum(1 for item in results if item["pass"])

    return {
        "total_cases": total,
        "passing_count": passing,
        "pass_rate": round(passing / total, 4) if total else 0,
        "prd_pass": passing == total,
    }


def write_csv(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "case_id",
        "status_code",
        "refused",
        "fallback_applied",
        "fallback_reason",
        "primary_generator_type",
        "fallback_generator_type",
        "final_generator_type",
        "log_fallback_applied",
        "log_fallback_reason",
        "pass",
        "total_cases",
        "passing_count",
        "pass_rate",
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
        "# Provider Fallback Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: Provider Fallback / Generator Fallback",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passing cases: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
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
                f"- Status code: {result['status_code']}",
                f"- Refused: {result['refused']}",
                f"- Fallback applied: {result['fallback_applied']}",
                f"- Fallback reason: {result['fallback_reason']}",
                f"- Primary generator type: {result['primary_generator_type']}",
                f"- Fallback generator type: {result['fallback_generator_type']}",
                f"- Final generator type: {result['final_generator_type']}",
                f"- Log fallback applied: {result['log_fallback_applied']}",
                f"- Log fallback reason: {result['log_fallback_reason']}",
                f"- Pass: {result['pass']}",
                "",
            ]
        )

    MD_REPORT_PATH.write_text("\\n".join(lines), encoding="utf-8")


def main() -> None:
    results = [
        evaluate_fallback_generator_present(),
        evaluate_primary_llm_failure_falls_back_to_extractive(),
    ]

    summary = summarize(results)

    for index, result in enumerate(results, start=1):
        status = "✅" if result["pass"] else "❌"
        print(
            f"[{index}/{len(results)}] {result['case_id']} "
            f"{status} pass={result['pass']}, "
            f"fallback_applied={result['log_fallback_applied']}, "
            f"reason={result['log_fallback_reason']}"
        )

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("PROVIDER FALLBACK EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:     {summary['total_cases']}")
    print(f"  Passing cases:   {summary['passing_count']}")
    print(f"  Pass rate:       {summary['pass_rate']}")
    print(f"  PRD Status:      {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
