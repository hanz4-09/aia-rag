import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
EVALUATIONS_DIR = REPORTS_DIR / "evaluations"
TODAY = time.strftime("%Y-%m-%d")

SUMMARY_CSV_PATH = EVALUATIONS_DIR / f"{TODAY}_all_evaluations_summary.csv"
SUMMARY_MD_PATH = EVALUATIONS_DIR / f"{TODAY}_all_evaluations_summary.md"


TASKS: List[Dict[str, Any]] = [
    {
        "task": "operations_report",
        "mode": "core",
        "description": "Generate operations report from runtime logs.",
        "command": [sys.executable, "scripts/generate_report.py"],
        "report_patterns": [
            "reports/operations_report.csv",
        ],
    },
    {
        "task": "answer_compliance",
        "mode": "core",
        "description": "Evaluate answer compliance against expected answers.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_answer_compliance.py"],
            [sys.executable, "scripts/evaluate_answers.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_answer_compliance_eval.csv",
        ],
    },
    {
        "task": "refusal_appropriateness",
        "mode": "core",
        "description": "Evaluate refusal behavior for unsafe or out-of-scope questions.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_refusal_appropriateness.py"],
            [sys.executable, "scripts/evaluate_refusal.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_refusal_appropriateness.csv",
            "reports/evaluations/*_refusal_appropriateness_eval.csv",
        ],
    },
    {
        "task": "context_precision",
        "mode": "core",
        "description": "Evaluate context precision and source accuracy.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_context_precision.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_context_precision_eval.csv",
        ],
    },
    {
        "task": "faithfulness_llm_judge",
        "mode": "core",
        "description": "Evaluate faithfulness with LLM judge or rule-based support checks.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_faithfulness.py"],
            [sys.executable, "scripts/evaluate_faithfulness_llm_judge.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_faithfulness_eval.csv",
        ],
    },
    {
        "task": "style_consistency",
        "mode": "core",
        "description": "Evaluate style and language consistency.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_style_consistency.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_style_consistency_eval.csv",
        ],
    },
    {
        "task": "pii_redaction",
        "mode": "core",
        "description": "Evaluate PII redaction behavior.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_pii_redaction.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_pii_redaction_eval.csv",
        ],
    },
    {
        "task": "multiturn_qa",
        "mode": "core",
        "description": "Evaluate multi-turn QA and session history usage.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_multiturn.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_multiturn_eval.csv",
        ],
    },
    {
        "task": "cache",
        "mode": "core",
        "description": "Evaluate cache behavior.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_cache.py"],
            [sys.executable, "scripts/evaluate_cache_behavior.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_cache_eval.csv",
        ],
    },
    {
        "task": "pdf_ingestion",
        "mode": "core",
        "description": "Evaluate PDF and OCR ingestion behavior.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_ingestion_pdf_handling.py"],
            [sys.executable, "scripts/evaluate_pdf_ingestion.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_pdf_ingestion_eval.csv",
        ],
    },
    {
        "task": "advanced_memory",
        "mode": "core",
        "description": "Evaluate persistent session memory and query rewrite.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_advanced_memory.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_advanced_memory_eval.csv",
        ],
    },
    {
        "task": "latency",
        "mode": "performance",
        "description": "Evaluate response latency against PRD target.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_latency.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_latency_eval.csv",
        ],
    },
    {
        "task": "concurrency",
        "mode": "performance",
        "description": "Evaluate concurrent request behavior.",
        "command_candidates": [
            [sys.executable, "scripts/evaluate_concurrency.py"],
        ],
        "report_patterns": [
            "reports/evaluations/*_concurrency_eval.csv",
        ],
    },
]


def resolve_command(task: Dict[str, Any]) -> Optional[List[str]]:
    if "command" in task:
        return task["command"]

    for command in task.get("command_candidates", []):
        if len(command) < 2:
            continue

        script_path = PROJECT_ROOT / command[1]
        if script_path.exists():
            return command

    return None


def find_latest_report(task: Dict[str, Any]) -> Optional[Path]:
    candidates: List[Path] = []

    for pattern in task.get("report_patterns", []):
        matched = list(PROJECT_ROOT.glob(pattern))
        candidates.extend(path for path in matched if path.is_file())

    if not candidates:
        return None

    # Prefer today's report if available.
    today_candidates = [
        path for path in candidates if path.name.startswith(TODAY)
    ]
    if today_candidates:
        return max(today_candidates, key=lambda path: path.stat().st_mtime)

    return max(candidates, key=lambda path: path.stat().st_mtime)


def run_subprocess(command: List[str]) -> Dict[str, Any]:
    start_time = time.time()

    process = subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    output_lines: List[str] = []
    assert process.stdout is not None

    for line in process.stdout:
        print(line, end="")
        output_lines.append(line)

    process.wait()

    duration_sec = round(time.time() - start_time, 2)
    combined_output = "".join(output_lines)

    return {
        "return_code": process.returncode,
        "duration_sec": duration_sec,
        "output_tail": combined_output[-4000:],
        "pass": process.returncode == 0,
    }


def read_csv_summary(report_path: Optional[Path]) -> Dict[str, Any]:
    if report_path is None or not report_path.exists():
        return {}

    try:
        with report_path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            rows = list(reader)
    except Exception:
        return {}

    if not rows:
        return {}

    # Common format: row_type=summary.
    for row in rows:
        if row.get("row_type") == "summary":
            return {
                key: value
                for key, value in row.items()
                if key and value not in {None, ""}
            }

    # Operations report format: metric,value.
    if set(rows[0].keys()) >= {"metric", "value"}:
        return {
            row.get("metric", ""): row.get("value", "")
            for row in rows
            if row.get("metric")
        }

    # Fallback: use first row.
    return {
        key: value
        for key, value in rows[0].items()
        if key and value not in {None, ""}
    }


def build_key_metrics(summary: Dict[str, Any]) -> str:
    if not summary:
        return ""

    ignored_keys = {
        "row_type",
        "task",
        "mode",
        "description",
        "report_path",
        "error",
    }

    parts = []

    for key, value in summary.items():
        if key in ignored_keys:
            continue

        if value in {None, ""}:
            continue

        parts.append(f"{key}={value}")

    return "; ".join(parts)


def relative_path(path: Optional[Path]) -> str:
    if path is None:
        return ""

    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def run_task(task: Dict[str, Any], skip_run: bool) -> Dict[str, Any]:
    task_name = task["task"]
    task_mode = task["mode"]

    command = resolve_command(task)
    duration_sec = 0.0
    error = ""

    if skip_run:
        report_path = find_latest_report(task)

        if report_path is None:
            status = "missing"
            error = "Report not found in skip-run mode."
        else:
            status = "skipped"

        report_summary = read_csv_summary(report_path)
        key_metrics = build_key_metrics(report_summary)

        return {
            "task": task_name,
            "mode": task_mode,
            "status": status,
            "duration_sec": duration_sec,
            "report_path": relative_path(report_path),
            "description": task.get("description", ""),
            "key_metrics": key_metrics,
            "error": error,
        }

    if command is None:
        report_path = find_latest_report(task)

        return {
            "task": task_name,
            "mode": task_mode,
            "status": "failed",
            "duration_sec": duration_sec,
            "report_path": relative_path(report_path),
            "description": task.get("description", ""),
            "key_metrics": "",
            "error": "No runnable evaluation script found.",
        }

    run_result = run_subprocess(command)
    duration_sec = run_result["duration_sec"]

    report_path = find_latest_report(task)
    report_summary = read_csv_summary(report_path)
    key_metrics = build_key_metrics(report_summary)

    if run_result["pass"]:
        status = "success"
    else:
        status = "failed"
        error = run_result["output_tail"]

    return {
        "task": task_name,
        "mode": task_mode,
        "status": status,
        "duration_sec": duration_sec,
        "report_path": relative_path(report_path),
        "description": task.get("description", ""),
        "key_metrics": key_metrics,
        "error": error,
    }


def select_tasks(mode: str) -> List[Dict[str, Any]]:
    if mode == "all":
        return TASKS

    if mode == "core":
        return [task for task in TASKS if task["mode"] == "core"]

    if mode == "performance":
        return [task for task in TASKS if task["mode"] == "performance"]

    raise ValueError(f"Unsupported mode: {mode}")


def is_success_result(row: Dict[str, Any]) -> bool:
    return row.get("status") == "success"


def is_skipped_result(row: Dict[str, Any]) -> bool:
    return row.get("status") == "skipped"


def is_report_available_result(row: Dict[str, Any]) -> bool:
    return row.get("status") in {"success", "skipped"} and bool(row.get("report_path"))


def is_failed_or_missing_result(row: Dict[str, Any]) -> bool:
    status = row.get("status")

    if status in {"failed", "missing"}:
        return True

    if status == "skipped":
        return not bool(row.get("report_path"))

    return status != "success"


def write_summary_csv(rows: List[Dict[str, Any]]) -> None:
    EVALUATIONS_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "task",
        "mode",
        "status",
        "duration_sec",
        "report_path",
        "description",
        "key_metrics",
        "error",
    ]

    with SUMMARY_CSV_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def write_summary_markdown(rows: List[Dict[str, Any]], mode: str) -> None:
    successful_tasks = sum(1 for row in rows if is_success_result(row))
    skipped_tasks = sum(1 for row in rows if is_skipped_result(row))
    report_available_tasks = sum(
        1 for row in rows if is_report_available_result(row)
    )
    failed_or_missing_tasks = sum(
        1 for row in rows if is_failed_or_missing_result(row)
    )
    total_tasks = len(rows)

    lines = [
        "# All Evaluations Summary",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        f"Mode: `{mode}`",
        "",
        "---",
        "",
        "## 1. Summary",
        "",
        f"- Total tasks: {total_tasks}",
        f"- Successful tasks: {successful_tasks}",
        f"- Skipped tasks: {skipped_tasks}",
        f"- Tasks with available reports: {report_available_tasks}",
        f"- Failed or missing tasks: {failed_or_missing_tasks}",
        "",
        "---",
        "",
        "## 2. Task Results",
        "",
        "| Task | Status | Duration sec | Report | Key Metrics |",
        "|---|---:|---:|---|---|",
    ]

    for row in rows:
        lines.append(
            f"| {row['task']} | {row['status']} | {row['duration_sec']} | "
            f"`{row['report_path']}` | {row['key_metrics']} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Notes",
            "",
            "- This script orchestrates existing evaluation scripts.",
            "- It does not replace the individual detailed evaluation reports.",
            "- LLM-based evaluations may consume model quota.",
            "- Performance evaluations may take longer than rule-based checks.",
            "- `--skip-run` summarizes existing reports without rerunning evaluations.",
            "",
        ]
    )

    SUMMARY_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def print_task_progress_header() -> None:
    print()
    print("=" * 80)
    print("CORE EVALUATION TASKS")
    print("=" * 80)


def print_task_progress_footer() -> None:
    print()
    print("=" * 80)
    print("CORE EVALUATION TASKS COMPLETED")
    print("=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run or summarize core PRD evaluation tasks."
    )
    parser.add_argument(
        "--mode",
        choices=["core", "performance", "all"],
        default="core",
        help="Evaluation mode to run or summarize.",
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Do not run evaluation scripts; summarize existing reports only.",
    )

    args = parser.parse_args()

    selected_tasks = select_tasks(args.mode)
    total_tasks = len(selected_tasks)
    rows: List[Dict[str, Any]] = []

    print_task_progress_header()

    for index, task in enumerate(selected_tasks, start=1):
        task_name = task["task"]

        action = (
            "checking existing report"
            if args.skip_run
            else "running evaluation"
        )

        print()
        print(f"[{index}/{total_tasks}] {task_name} ... {action}")

        task_start = time.time()
        result = run_task(task, skip_run=args.skip_run)
        duration_sec = round(time.time() - task_start, 2)

        # Keep the duration measured by the task itself when available.
        if not result.get("duration_sec"):
            result["duration_sec"] = duration_sec

        status = result.get("status", "unknown")

        if status in {"success", "skipped"}:
            icon = "✅"
        else:
            icon = "❌"

        print(
            f"[{index}/{total_tasks}] {task_name} ... "
            f"{icon} {status}, duration={result['duration_sec']}s"
        )

        if result.get("report_path"):
            print(f"  report: {result['report_path']}")

        if result.get("error"):
            print(f"  error: {result['error']}")

        rows.append(result)

    print_task_progress_footer()

    write_summary_csv(rows)
    write_summary_markdown(rows, mode=args.mode)

    failed_or_missing_tasks = sum(
        1 for row in rows if is_failed_or_missing_result(row)
    )

    print()
    print("=" * 80)
    print("ALL EVALUATIONS SUMMARY")
    print("=" * 80)
    print(f"  Mode:                         {args.mode}")
    print(f"  Total tasks:                  {len(rows)}")
    print(f"  Tasks with available reports: {sum(1 for row in rows if is_report_available_result(row))}")
    print(f"  Failed or missing tasks:      {failed_or_missing_tasks}")
    print(f"  CSV summary:                  {SUMMARY_CSV_PATH}")
    print(f"  Markdown summary:             {SUMMARY_MD_PATH}")
    print("=" * 80)

    if failed_or_missing_tasks > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()