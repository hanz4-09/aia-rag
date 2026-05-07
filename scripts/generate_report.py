import csv
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOG_PATH = PROJECT_ROOT / "logs" / "rag_service.jsonl"
REPORT_PATH = PROJECT_ROOT / "reports" / "operations_report.csv"


def load_logs(log_path: Path) -> List[Dict[str, Any]]:
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    records = []

    with open(log_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line: {line}")

    return records


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = int(round((p / 100) * (len(sorted_values) - 1)))
    return sorted_values[index]


def safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def generate_report(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_requests = len(records)

    latencies = [
        record.get("total_latency_ms", 0)
        for record in records
        if record.get("total_latency_ms") is not None
    ]

    cache_hits = [
        record for record in records
        if record.get("cache_hit") is True
    ]

    refused_requests = [
        record for record in records
        if record.get("refused") is True
    ]

    input_tokens = [
        record.get("input_tokens")
        for record in records
        if isinstance(record.get("input_tokens"), int)
    ]

    output_tokens = [
        record.get("output_tokens")
        for record in records
        if isinstance(record.get("output_tokens"), int)
    ]

    report = {
        "total_requests": total_requests,
        "p50_latency_ms": percentile(latencies, 50),
        "p95_latency_ms": percentile(latencies, 95),
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
        "cache_hit_rate": safe_rate(len(cache_hits), total_requests),
        "refusal_rate": safe_rate(len(refused_requests), total_requests),
        "answer_compliance_rate": "N/A",
        "avg_input_tokens": round(statistics.mean(input_tokens), 2) if input_tokens else "N/A",
        "avg_output_tokens": round(statistics.mean(output_tokens), 2) if output_tokens else "N/A",
    }

    return report


def write_csv_report(report: Dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(report.keys()))
        writer.writeheader()
        writer.writerow(report)


def main():
    records = load_logs(LOG_PATH)

    if not records:
        print("No log records found.")
        return

    report = generate_report(records)
    write_csv_report(report, REPORT_PATH)

    print("Operations report generated successfully.")
    print(f"Log file: {LOG_PATH}")
    print(f"Report file: {REPORT_PATH}")
    print()
    print("Report summary:")
    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()