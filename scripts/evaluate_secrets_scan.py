import csv
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.ingestion.secrets_scanner import scan_directory, write_scan_reports


OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
TODAY = time.strftime("%Y-%m-%d")
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_secrets_scan_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_secrets_scan_eval.md"


def create_eval_corpus(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)

    (root / "safe_policy.txt").write_text(
        "API Key leakage must be reported within 24 hours. "
        "This is a policy concept, not an actual secret value.",
        encoding="utf-8",
    )

    (root / "secret_api_key.txt").write_text(
        "api_key=abc123secret456789\n",
        encoding="utf-8",
    )

    (root / "secret_token.env").write_text(
        "ACCESS_TOKEN=tok_live_123456789\n",
        encoding="utf-8",
    )

    (root / "private_key.txt").write_text(
        "-----BEGIN PRIVATE KEY-----\nABCDEF\n-----END PRIVATE KEY-----\n",
        encoding="utf-8",
    )

    (root / "ignored_example_secret.txt").write_text(
        "api_key=exampleabcdef123456  # secret-scan-ignore\n",
        encoding="utf-8",
    )


def evaluate_case() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "raw"
        create_eval_corpus(root)

        report = scan_directory(root)

        findings = report["findings"]
        ignored_findings = report.get("ignored_findings", [])
        pattern_names = {item["pattern_name"] for item in findings}
        ignored_pattern_names = {item["pattern_name"] for item in ignored_findings}
        finding_files = {item["filename"] for item in findings}
        ignored_finding_files = {item["filename"] for item in ignored_findings}

        safe_file_not_flagged = "safe_policy.txt" not in finding_files
        ignored_example_not_active = "ignored_example_secret.txt" not in finding_files
        ignored_example_recorded = "ignored_example_secret.txt" in ignored_finding_files
        api_key_detected = "generic_api_key_assignment" in pattern_names
        token_detected = "generic_access_token_assignment" in pattern_names
        private_key_detected = "private_key_block" in pattern_names

        eval_report_dir = PROJECT_ROOT / "reports" / "ingestion"
        write_scan_reports(
            report,
            eval_report_dir / "secrets_scan_eval_sample_report.json",
            eval_report_dir / "secrets_scan_eval_sample_report.md",
        )

        pass_result = all(
            [
                report["scanned_files"] == 5,
                report["findings_count"] >= 3,
                report.get("ignored_findings_count", 0) >= 1,
                safe_file_not_flagged,
                ignored_example_not_active,
                ignored_example_recorded,
                api_key_detected,
                token_detected,
                private_key_detected,
            ]
        )

        return {
            "case_id": "secrets_scan_detects_secrets_without_policy_false_positive",
            "scanned_files": report["scanned_files"],
            "findings_count": report["findings_count"],
            "high_severity_count": report["high_severity_count"],
            "medium_severity_count": report["medium_severity_count"],
            "safe_file_not_flagged": safe_file_not_flagged,
            "ignored_example_not_active": ignored_example_not_active,
            "ignored_example_recorded": ignored_example_recorded,
            "ignored_findings_count": report.get("ignored_findings_count", 0),
            "ignored_pattern_names": "|".join(sorted(ignored_pattern_names)),
            "api_key_detected": api_key_detected,
            "token_detected": token_detected,
            "private_key_detected": private_key_detected,
            "pattern_names": "|".join(sorted(pattern_names)),
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
        "scanned_files",
        "findings_count",
        "high_severity_count",
        "medium_severity_count",
        "safe_file_not_flagged",
        "ignored_example_not_active",
        "ignored_example_recorded",
        "ignored_findings_count",
        "ignored_pattern_names",
        "api_key_detected",
        "token_detected",
        "private_key_detected",
        "pattern_names",
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
        "# Secrets Scan Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: Ingestion Secrets Scan / False Positive Guard",
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
                f"- Scanned files: {result['scanned_files']}",
                f"- Findings count: {result['findings_count']}",
                f"- High severity count: {result['high_severity_count']}",
                f"- Medium severity count: {result['medium_severity_count']}",
                f"- Safe policy file not flagged: {result['safe_file_not_flagged']}",
                f"- Ignored example not active: {result['ignored_example_not_active']}",
                f"- Ignored example recorded: {result['ignored_example_recorded']}",
                f"- Ignored findings count: {result['ignored_findings_count']}",
                f"- Ignored pattern names: {result['ignored_pattern_names']}",
                f"- API key detected: {result['api_key_detected']}",
                f"- Token detected: {result['token_detected']}",
                f"- Private key detected: {result['private_key_detected']}",
                f"- Pattern names: {result['pattern_names']}",
                f"- Pass: {result['pass']}",
                "",
            ]
        )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    results = [evaluate_case()]
    summary = summarize(results)

    for index, result in enumerate(results, start=1):
        status = "✅" if result["pass"] else "❌"
        print(
            f"[{index}/{len(results)}] {result['case_id']} "
            f"{status} pass={result['pass']}, "
            f"findings={result['findings_count']}, "
            f"patterns={result['pattern_names']}"
        )

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("SECRETS SCAN EVALUATION SUMMARY")
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
