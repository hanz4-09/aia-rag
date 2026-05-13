import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
EVALUATIONS_DIR = REPORTS_DIR / "evaluations"
PRD_RUNS_DIR = REPORTS_DIR / "prd_runs"

TODAY = time.strftime("%Y-%m-%d")
CORE_SUMMARY_CSV = EVALUATIONS_DIR / f"{TODAY}_all_evaluations_summary.csv"
CORE_SUMMARY_MD = EVALUATIONS_DIR / f"{TODAY}_all_evaluations_summary.md"
OPERATIONS_REPORT_CSV = REPORTS_DIR / "operations_report.csv"


def run_command(command: List[str], description: str) -> Dict[str, Any]:
    """
    Run a child command and stream its output in real time.

    This is important for reviewer-facing long-running evaluation commands.
    Without streaming, reviewers may think the script is stuck while the full
    evaluation suite is still running.
    """
    start_time = time.time()

    print()
    print("-" * 80)
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print("-" * 80)

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

    duration_ms = int((time.time() - start_time) * 1000)
    combined_output = "".join(output_lines)

    print()
    print("-" * 80)
    print(
        f"Finished: {description} | "
        f"return_code={process.returncode} | "
        f"duration_ms={duration_ms}"
    )
    print("-" * 80)

    return {
        "description": description,
        "command": " ".join(command),
        "return_code": process.returncode,
        "duration_ms": duration_ms,
        "stdout_tail": combined_output[-4000:],
        "stderr_tail": "",
        "pass": process.returncode == 0,
    }


def create_run_dir() -> Path:
    run_id = time.strftime("run_%Y%m%d_%H%M%S")
    run_dir = PRD_RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def read_core_summary_rows(summary_csv: Path) -> List[Dict[str, Any]]:
    if not summary_csv.exists():
        return []

    with summary_csv.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def parse_key_metrics(metrics_text: str) -> Dict[str, str]:
    result: Dict[str, str] = {}

    if not metrics_text:
        return result

    parts = [part.strip() for part in metrics_text.split(";") if part.strip()]

    for part in parts:
        if "=" not in part:
            continue

        key, value = part.split("=", 1)
        result[key.strip()] = value.strip()

    return result


def build_full_metrics(summary_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    metrics_rows: List[Dict[str, Any]] = []

    for row in summary_rows:
        key_metrics = parse_key_metrics(row.get("key_metrics", ""))

        metrics_rows.append(
            {
                "task": row.get("task", ""),
                "mode": row.get("mode", ""),
                "status": row.get("status", ""),
                "duration_sec": row.get("duration_sec", ""),
                "report_path": row.get("report_path", ""),
                "description": row.get("description", ""),
                "prd_pass": key_metrics.get("prd_pass", ""),
                "pass_rate": key_metrics.get("pass_rate", ""),
                "passing_count": key_metrics.get("passing_count", ""),
                "total_cases": key_metrics.get("total_cases", ""),
                "success_rate": key_metrics.get("success_rate", ""),
                "within_10s_rate": key_metrics.get("within_10s_rate", ""),
                "avg_latency_ms": key_metrics.get("avg_latency_ms", ""),
                "p95_latency_ms": key_metrics.get("p95_latency_ms", ""),
                "key_metrics": row.get("key_metrics", ""),
                "error": row.get("error", ""),
            }
        )

    return metrics_rows


def write_full_metrics(run_dir: Path, metrics_rows: List[Dict[str, Any]]) -> Path:
    output_path = run_dir / "full_metrics.csv"

    fieldnames = [
        "task",
        "mode",
        "status",
        "duration_sec",
        "report_path",
        "description",
        "prd_pass",
        "pass_rate",
        "passing_count",
        "total_cases",
        "success_rate",
        "within_10s_rate",
        "avg_latency_ms",
        "p95_latency_ms",
        "key_metrics",
        "error",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in metrics_rows:
            writer.writerow(row)

    return output_path


def build_summary(
    run_dir: Path,
    command_results: List[Dict[str, Any]],
    summary_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    total_tasks = len(summary_rows)

    tasks_with_reports = sum(
        1
        for row in summary_rows
        if bool(row.get("report_path"))
    )

    failed_or_missing_tasks = sum(
        1
        for row in summary_rows
        if row.get("status") in {"failed", "missing"}
        or (
            row.get("status") == "skipped"
            and not bool(row.get("report_path"))
        )
    )

    command_pass = all(item["pass"] for item in command_results)

    return {
        "run_id": run_dir.name,
        "run_dir": str(run_dir),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "command_pass": command_pass,
        "total_core_tasks": total_tasks,
        "tasks_with_available_reports": tasks_with_reports,
        "failed_or_missing_tasks": failed_or_missing_tasks,
        "overall_pass": command_pass and failed_or_missing_tasks == 0,
        "commands": command_results,
    }


def write_summary_json(run_dir: Path, summary: Dict[str, Any]) -> Path:
    output_path = run_dir / "summary.json"
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def write_full_results_json(
    run_dir: Path,
    summary_rows: List[Dict[str, Any]],
    command_results: List[Dict[str, Any]],
) -> Path:
    output_path = run_dir / "full_results.json"

    data = {
        "summary_rows": summary_rows,
        "command_results": command_results,
    }

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return output_path


def write_ops_report_md(
    run_dir: Path,
    summary: Dict[str, Any],
    metrics_rows: List[Dict[str, Any]],
) -> Path:
    output_path = run_dir / "ops_report.md"

    lines = [
        "# Full PRD Evaluation Report",
        "",
        f"Run ID: `{summary['run_id']}`",
        f"Created at: {summary['created_at']}",
        "",
        "## Summary",
        "",
        f"- Overall pass: {summary['overall_pass']}",
        f"- Command pass: {summary['command_pass']}",
        f"- Total core tasks: {summary['total_core_tasks']}",
        f"- Tasks with available reports: {summary['tasks_with_available_reports']}",
        f"- Failed or missing tasks: {summary['failed_or_missing_tasks']}",
        "",
        "## Core Task Results",
        "",
        "| Task | Mode | Status | PRD Pass | Pass Rate | Report |",
        "|---|---|---:|---:|---:|---|",
    ]

    for row in metrics_rows:
        lines.append(
            f"| {row['task']} | {row['mode']} | {row['status']} | "
            f"{row['prd_pass']} | {row['pass_rate']} | `{row['report_path']}` |"
        )

    lines.extend(
        [
            "",
            "## Command Results",
            "",
            "| Command | Return Code | Duration ms | Pass |",
            "|---|---:|---:|---:|",
        ]
    )

    for command in summary["commands"]:
        lines.append(
            f"| `{command['command']}` | {command['return_code']} | "
            f"{command['duration_ms']} | {command['pass']} |"
        )

    lines.extend(
        [
            "",
            "## Generated Files",
            "",
            "- `full_metrics.csv`",
            "- `full_results.json`",
            "- `summary.json`",
            "- `ops_report.md`",
            "- `ops_report.csv`",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def write_ops_report_csv(run_dir: Path, summary: Dict[str, Any]) -> Path:
    output_path = run_dir / "ops_report.csv"

    rows = [
        {"metric": "overall_pass", "value": summary["overall_pass"]},
        {"metric": "command_pass", "value": summary["command_pass"]},
        {"metric": "total_core_tasks", "value": summary["total_core_tasks"]},
        {
            "metric": "tasks_with_available_reports",
            "value": summary["tasks_with_available_reports"],
        },
        {
            "metric": "failed_or_missing_tasks",
            "value": summary["failed_or_missing_tasks"],
        },
    ]

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def copy_if_exists(source: Path, destination_dir: Path) -> None:
    if source.exists():
        shutil.copy2(source, destination_dir / source.name)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run full PRD evaluation and generate a timestamped reviewer "
            "report bundle."
        )
    )
    parser.add_argument(
        "--with-ingest",
        action="store_true",
        help="Run scripts/ingest.py before generating the PRD evaluation summary.",
    )
    parser.add_argument(
        "--rerun-evaluations",
        action="store_true",
        help="Rerun core evaluations instead of summarizing existing reports.",
    )

    args = parser.parse_args()

    run_dir = create_run_dir()
    command_results: List[Dict[str, Any]] = []

    print("=" * 80)
    print("FULL PRD EVALUATION")
    print("=" * 80)
    print(f"Run directory: {run_dir}")

    if args.with_ingest:
        print("\n[1] Running ingestion...")
        result = run_command(
            [sys.executable, "scripts/ingest.py"],
            "Run document ingestion",
        )
        command_results.append(result)
        print(f"  pass={result['pass']}, return_code={result['return_code']}")

        if not result["pass"]:
            summary = build_summary(run_dir, command_results, [])
            write_summary_json(run_dir, summary)
            write_full_results_json(run_dir, [], command_results)
            write_ops_report_md(run_dir, summary, [])
            write_ops_report_csv(run_dir, summary)
            print("Ingestion failed. Stop.")
            sys.exit(1)

    print("\n[2] Generating core evaluation summary...")

    eval_command = [
        sys.executable,
        "scripts/run_all_evaluations.py",
        "--mode",
        "all",
    ]

    if not args.rerun_evaluations:
        eval_command.append("--skip-run")

    result = run_command(
        eval_command,
        "Generate core PRD evaluation summary",
    )
    command_results.append(result)
    print(f"  pass={result['pass']}, return_code={result['return_code']}")

    if not result["pass"]:
        summary = build_summary(run_dir, command_results, [])
        write_summary_json(run_dir, summary)
        write_full_results_json(run_dir, [], command_results)
        write_ops_report_md(run_dir, summary, [])
        write_ops_report_csv(run_dir, summary)
        print("Core evaluation summary failed. Stop.")
        sys.exit(1)

    print("\n[3] Generating operations report...")
    result = run_command(
        [sys.executable, "scripts/generate_report.py"],
        "Generate operations report from JSONL logs",
    )
    command_results.append(result)
    print(f"  pass={result['pass']}, return_code={result['return_code']}")

    print("\n[4] Collecting reports...")

    summary_rows = read_core_summary_rows(CORE_SUMMARY_CSV)
    metrics_rows = build_full_metrics(summary_rows)
    summary = build_summary(run_dir, command_results, summary_rows)

    full_metrics_path = write_full_metrics(run_dir, metrics_rows)
    full_results_path = write_full_results_json(run_dir, summary_rows, command_results)
    summary_json_path = write_summary_json(run_dir, summary)
    ops_md_path = write_ops_report_md(run_dir, summary, metrics_rows)
    ops_csv_path = write_ops_report_csv(run_dir, summary)

    copy_if_exists(CORE_SUMMARY_CSV, run_dir)
    copy_if_exists(CORE_SUMMARY_MD, run_dir)
    copy_if_exists(OPERATIONS_REPORT_CSV, run_dir)

    print("\nGenerated files:")
    print(f"  {full_metrics_path}")
    print(f"  {full_results_path}")
    print(f"  {summary_json_path}")
    print(f"  {ops_md_path}")
    print(f"  {ops_csv_path}")

    print()
    print("=" * 80)
    print("FULL PRD EVALUATION SUMMARY")
    print("=" * 80)
    print(f"  Run directory:                  {run_dir}")
    print(f"  Total core tasks:               {summary['total_core_tasks']}")
    print(f"  Tasks with available reports:   {summary['tasks_with_available_reports']}")
    print(f"  Failed or missing tasks:        {summary['failed_or_missing_tasks']}")
    print(
        f"  Overall pass:                   "
        f"{'✅ PASS' if summary['overall_pass'] else '❌ FAIL'}"
    )
    print("=" * 80)

    if not summary["overall_pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()