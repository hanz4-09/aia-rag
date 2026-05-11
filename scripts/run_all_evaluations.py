import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "reports" / "evaluations"

TODAY = time.strftime("%Y-%m-%d")
SUMMARY_CSV_PATH = REPORT_DIR / f"{TODAY}_all_evaluations_summary.csv"
SUMMARY_MD_PATH = REPORT_DIR / f"{TODAY}_all_evaluations_summary.md"


TASKS = [
    {
        "name": "operations_report",
        "script": "scripts/generate_report.py",
        "mode": "core",
        "report_glob": "operations_report.csv",
        "description": "Generate operations report from structured JSONL logs.",
        "key_metrics": [
            "total_requests",
            "p50_latency_ms",
            "p95_latency_ms",
            "avg_latency_ms",
            "avg_total_tokens",
            "reference_cost_per_1000_calls",
            "estimated_billable_cost_per_1000_calls",
            "answer_compliance_rate",
        ],
    },
    {
        "name": "answer_compliance",
        "script": "scripts/evaluate_answers.py",
        "mode": "core",
        "report_glob": "*answer_compliance_eval.csv",
        "description": "Evaluate rule-based answer compliance.",
        "key_metrics": [
            "total_questions",
            "answer_compliance_rate",
            "rule_based_pass_rate",
            "answer_not_empty_rate",
            "expected_refusal_match_rate",
            "refusal_reason_match_rate",
            "source_hit_rate",
            "forbidden_keywords_clean_rate",
            "avg_expected_keywords_hit_rate",
        ],
    },
    {
        "name": "refusal_appropriateness",
        "script": "scripts/evaluate_refusals.py",
        "mode": "core",
        "report_glob": "*refusal_appropriateness.csv",
        "description": "Evaluate refusal decision and refusal reason correctness.",
        "key_metrics": [
            "total_questions",
            "pass_rate",
            "refusal_decision_match_rate",
            "refusal_reason_match_rate",
            "false_positive_rate",
            "false_negative_rate",
        ],
    },
    {
        "name": "context_precision",
        "script": "scripts/evaluate_context_precision.py",
        "mode": "core",
        "report_glob": "*context_precision_eval.csv",
        "description": "Evaluate context precision against expected sources and keywords.",
        "key_metrics": [
            "answerable_questions",
            "evaluated_questions",
            "avg_context_precision",
            "avg_source_accuracy",
            "avg_keyword_coverage",
            "passing_count",
            "passing_rate",
            "prd_target",
            "prd_pass",
        ],
    },
    {
        "name": "faithfulness_llm_judge",
        "script": "scripts/evaluate_faithfulness_llm_judge.py",
        "mode": "core",
        "report_glob": "*faithfulness_eval.csv",
        "description": "Evaluate answer faithfulness using LLM-as-Judge.",
        "key_metrics": [
            "answerable_questions",
            "evaluated_questions",
            "avg_faithfulness",
            "overall_statements",
            "faithful_statements",
            "passing_count",
            "prd_target",
            "prd_pass",
        ],
    },
    {
        "name": "style_consistency",
        "script": "scripts/evaluate_style_consistency.py",
        "mode": "core",
        "report_glob": "*style_consistency_eval.csv",
        "description": "Evaluate answer style consistency using LLM-as-Judge.",
        "key_metrics": [
            "total_answerable",
            "total_evaluated",
            "avg_style_consistency",
            "avg_language_consistency",
            "avg_format_consistency",
            "avg_tone_professionalism",
            "passing_count",
            "passing_rate",
            "prd_target",
            "prd_pass",
        ],
    },
    {
        "name": "latency",
        "script": "scripts/evaluate_latency.py",
        "mode": "performance",
        "report_glob": "*latency_eval.csv",
        "description": "Evaluate sequential end-to-end latency.",
        "key_metrics": [
            "total_requests",
            "successful_requests",
            "failed_requests",
            "success_rate",
            "within_10s_rate",
            "avg_latency_ms",
            "p50_latency_ms",
            "p90_latency_ms",
            "p95_latency_ms",
            "max_latency_ms",
            "prd_pass",
        ],
    },
    {
        "name": "concurrency",
        "script": "scripts/evaluate_concurrency.py",
        "mode": "performance",
        "report_glob": "*concurrency_eval.csv",
        "description": "Evaluate 5 concurrent requests on a single instance.",
        "key_metrics": [
            "total_requests",
            "concurrency_level",
            "successful_requests",
            "failed_requests",
            "success_rate",
            "within_10s_rate",
            "avg_latency_ms",
            "p95_latency_ms",
            "max_latency_ms",
            "wall_clock_latency_ms",
            "prd_pass",
        ],
    },
]


def should_run_task(task: Dict[str, object], mode: str) -> bool:
    if mode == "all":
        return True
    if mode == "core":
        return task["mode"] == "core"
    if mode == "performance":
        return task["mode"] == "performance"
    return False


def run_script(script_path: str) -> Dict[str, object]:
    absolute_script = PROJECT_ROOT / script_path

    if not absolute_script.exists():
        return {
            "status": "missing",
            "return_code": None,
            "duration_seconds": 0,
            "error": f"Script not found: {script_path}",
        }

    start = time.time()

    process = subprocess.run(
        [sys.executable, str(absolute_script)],
        cwd=str(PROJECT_ROOT),
        text=True,
    )

    duration_seconds = round(time.time() - start, 2)

    return {
        "status": "success" if process.returncode == 0 else "failed",
        "return_code": process.returncode,
        "duration_seconds": duration_seconds,
        "error": "" if process.returncode == 0 else f"Process exited with code {process.returncode}",
    }


def find_latest_report(report_glob: str) -> Optional[Path]:
    candidates = []

    if report_glob == "operations_report.csv":
        path = PROJECT_ROOT / "reports" / report_glob
        return path if path.exists() else None

    for path in REPORT_DIR.glob(report_glob):
        if path.is_file():
            candidates.append(path)

    if not candidates:
        return None

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def read_summary_row(csv_path: Optional[Path]) -> Dict[str, str]:
    if not csv_path or not csv_path.exists():
        return {}

    with open(csv_path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            # Most evaluation reports use row_type=summary.
            # operations_report.csv has only one data row without row_type.
            if row.get("row_type") == "summary":
                return {k: v for k, v in row.items() if v not in [None, ""]}

            if "row_type" not in row:
                return {k: v for k, v in row.items() if v not in [None, ""]}

    return {}


def write_summary_csv(rows: List[Dict[str, object]]) -> None:
    SUMMARY_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "task",
        "mode",
        "script",
        "status",
        "return_code",
        "duration_seconds",
        "report_path",
        "description",
        "key_metrics",
        "error",
    ]

    with open(SUMMARY_CSV_PATH, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                "task": row.get("task", ""),
                "mode": row.get("mode", ""),
                "script": row.get("script", ""),
                "status": row.get("status", ""),
                "return_code": row.get("return_code", ""),
                "duration_seconds": row.get("duration_seconds", ""),
                "report_path": row.get("report_path", ""),
                "description": row.get("description", ""),
                "key_metrics": row.get("key_metrics", ""),
                "error": row.get("error", ""),
            })


def write_summary_markdown(rows: List[Dict[str, object]], mode: str) -> None:
    passed_tasks = sum(1 for row in rows if row.get("status") == "success")
    total_tasks = len(rows)

    lines = [
        "# All Evaluations Summary",
        "",
        f"Date: {TODAY}  ",
        "Project: AIA RAG Case Study Service  ",
        f"Mode: `{mode}`  ",
        "",
        "---",
        "",
        "## 1. Summary",
        "",
        f"- Total tasks: {total_tasks}",
        f"- Successful tasks: {passed_tasks}",
        f"- Failed or missing tasks: {total_tasks - passed_tasks}",
        "",
        "---",
        "",
        "## 2. Task Results",
        "",
        "| Task | Status | Duration sec | Report | Key Metrics |",
        "|---|---:|---:|---|---|",
    ]

    for row in rows:
        report_path = row.get("report_path") or ""
        display_report = report_path.replace(str(PROJECT_ROOT) + "\\", "").replace(str(PROJECT_ROOT) + "/", "")
        lines.append(
            f"| {row.get('task')} | {row.get('status')} | {row.get('duration_seconds')} | "
            f"`{display_report}` | {row.get('key_metrics')} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Notes",
        "",
        "- This script orchestrates existing evaluation scripts.",
        "- It does not replace the individual detailed evaluation reports.",
        "- LLM-based evaluations may consume model quota.",
        "- Performance evaluations may be skipped by running `--mode core`.",
        "",
    ])

    with open(SUMMARY_MD_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AIA RAG evaluation suite.")
    parser.add_argument(
        "--mode",
        choices=["core", "performance", "all"],
        default="all",
        help="Which evaluation group to run.",
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Do not execute scripts; only aggregate latest existing CSV reports.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failed task.",
    )

    args = parser.parse_args()

    selected_tasks = [task for task in TASKS if should_run_task(task, args.mode)]

    print(f"Running evaluation suite. mode={args.mode}, skip_run={args.skip_run}")
    print(f"Selected tasks: {len(selected_tasks)}")
    print()

    rows = []

    for task in selected_tasks:
        print("=" * 100)
        print(f"Task: {task['name']}")
        print(f"Script: {task['script']}")
        print("=" * 100)

        if args.skip_run:
            run_result = {
                "status": "skipped",
                "return_code": None,
                "duration_seconds": 0,
                "error": "",
            }
        else:
            run_result = run_script(task["script"])

        latest_report = find_latest_report(task["report_glob"])
        summary = read_summary_row(latest_report)

        key_metrics = []
        for metric in task["key_metrics"]:
            if metric in summary:
                key_metrics.append(f"{metric}={summary[metric]}")

        row = {
            "task": task["name"],
            "mode": task["mode"],
            "script": task["script"],
            "status": run_result["status"],
            "return_code": run_result["return_code"],
            "duration_seconds": run_result["duration_seconds"],
            "report_path": str(latest_report) if latest_report else "",
            "description": task["description"],
            "key_metrics": "; ".join(key_metrics),
            "error": run_result["error"],
        }

        rows.append(row)

        print(f"Status: {row['status']}")
        print(f"Duration seconds: {row['duration_seconds']}")
        print(f"Report: {row['report_path']}")
        print(f"Key metrics: {row['key_metrics']}")
        if row["error"]:
            print(f"Error: {row['error']}")

        if args.fail_fast and row["status"] not in ["success", "skipped"]:
            print("Fail-fast enabled. Stopping.")
            break

        print()

    write_summary_csv(rows)
    write_summary_markdown(rows, args.mode)

    print("=" * 100)
    print("Evaluation suite completed.")
    print(f"Summary CSV: {SUMMARY_CSV_PATH}")
    print(f"Summary Markdown: {SUMMARY_MD_PATH}")
    print("=" * 100)


if __name__ == "__main__":
    main()
