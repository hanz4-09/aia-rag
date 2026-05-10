import csv
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOG_PATH = PROJECT_ROOT / "logs" / "rag_service.jsonl"
CONFIG_PATH = PROJECT_ROOT / "configs" / "app.yaml"
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


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


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


def numeric_values(records: List[Dict[str, Any]], field: str) -> List[float]:
    values = []

    for record in records:
        value = record.get(field)

        if isinstance(value, (int, float)):
            values.append(value)

    return values


def average_or_na(values: List[float]) -> float | str:
    if not values:
        return "N/A"

    return round(statistics.mean(values), 2)


def sum_or_na(values: List[float]) -> float | str:
    if not values:
        return "N/A"

    return round(sum(values), 2)


def unique_non_empty_values(records: List[Dict[str, Any]], field: str) -> str:
    values = sorted(
        {
            str(record.get(field))
            for record in records
            if record.get(field) not in [None, ""]
        }
    )

    if not values:
        return "N/A"

    return "|".join(values)


def calculate_reference_cost(
    input_tokens: float,
    output_tokens: float,
    input_price_per_1m_tokens: float,
    output_price_per_1m_tokens: float,
) -> float:
    """
    Estimate cost based on list price.

    Formula:
    input_tokens / 1,000,000 * input_price
    + output_tokens / 1,000,000 * output_price
    """
    input_cost = input_tokens / 1_000_000 * input_price_per_1m_tokens
    output_cost = output_tokens / 1_000_000 * output_price_per_1m_tokens

    return input_cost + output_cost


def generate_report(
    records: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    total_requests = len(records)

    total_latencies = numeric_values(records, "total_latency_ms")
    retrieval_latencies = numeric_values(records, "retrieval_latency_ms")
    generation_latencies = numeric_values(records, "generation_latency_ms")

    input_tokens = numeric_values(records, "input_tokens")
    output_tokens = numeric_values(records, "output_tokens")
    total_tokens = numeric_values(records, "total_tokens")

    total_input_tokens = sum(input_tokens) if input_tokens else 0
    total_output_tokens = sum(output_tokens) if output_tokens else 0
    total_all_tokens = sum(total_tokens) if total_tokens else 0

    cache_hits = [
        record for record in records
        if record.get("cache_hit") is True
    ]

    refused_requests = [
        record for record in records
        if record.get("refused") is True
    ]

    llm_requests = [
        record for record in records
        if record.get("generator_type") == "llm"
    ]

    extractive_requests = [
        record for record in records
        if record.get("generator_type") == "extractive"
    ]

    cost_config = config.get("cost", {})
    cost_enabled = cost_config.get("enabled", False)
    currency = cost_config.get("currency", "USD")
    input_price_per_1m_tokens = float(
        cost_config.get("input_price_per_1m_tokens", 0.0)
    )
    output_price_per_1m_tokens = float(
        cost_config.get("output_price_per_1m_tokens", 0.0)
    )
    free_quota_enabled = bool(cost_config.get("free_quota_enabled", False))

    reference_total_cost = 0.0
    reference_cost_per_request = 0.0
    reference_cost_per_1000_calls = 0.0
    estimated_billable_total_cost = 0.0
    estimated_billable_cost_per_1000_calls = 0.0

    if cost_enabled and total_requests > 0:
        reference_total_cost = calculate_reference_cost(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            input_price_per_1m_tokens=input_price_per_1m_tokens,
            output_price_per_1m_tokens=output_price_per_1m_tokens,
        )

        reference_cost_per_request = reference_total_cost / total_requests
        reference_cost_per_1000_calls = reference_cost_per_request * 1000

        if free_quota_enabled:
            estimated_billable_total_cost = 0.0
            estimated_billable_cost_per_1000_calls = 0.0
        else:
            estimated_billable_total_cost = reference_total_cost
            estimated_billable_cost_per_1000_calls = reference_cost_per_1000_calls

    report = {
        "total_requests": total_requests,

        "p50_latency_ms": percentile(total_latencies, 50),
        "p95_latency_ms": percentile(total_latencies, 95),
        "avg_latency_ms": round(statistics.mean(total_latencies), 2)
        if total_latencies
        else 0,

        "avg_retrieval_latency_ms": average_or_na(retrieval_latencies),
        "avg_generation_latency_ms": average_or_na(generation_latencies),

        "cache_hit_rate": safe_rate(len(cache_hits), total_requests),
        "refusal_rate": safe_rate(len(refused_requests), total_requests),

        "llm_request_count": len(llm_requests),
        "extractive_request_count": len(extractive_requests),
        "generator_types": unique_non_empty_values(records, "generator_type"),
        "model_names": unique_non_empty_values(records, "model_name"),

        "total_input_tokens": round(total_input_tokens, 2) if input_tokens else "N/A",
        "total_output_tokens": round(total_output_tokens, 2) if output_tokens else "N/A",
        "total_tokens": round(total_all_tokens, 2) if total_tokens else "N/A",

        "avg_input_tokens": average_or_na(input_tokens),
        "avg_output_tokens": average_or_na(output_tokens),
        "avg_total_tokens": average_or_na(total_tokens),

        "cost_enabled": cost_enabled,
        "currency": currency,
        "input_price_per_1m_tokens": input_price_per_1m_tokens,
        "output_price_per_1m_tokens": output_price_per_1m_tokens,
        "free_quota_enabled": free_quota_enabled,

        "reference_total_cost": round(reference_total_cost, 6),
        "reference_cost_per_request": round(reference_cost_per_request, 6),
        "reference_cost_per_1000_calls": round(reference_cost_per_1000_calls, 6),

        "estimated_billable_total_cost": round(estimated_billable_total_cost, 6),
        "estimated_billable_cost_per_1000_calls": round(
            estimated_billable_cost_per_1000_calls,
            6,
        ),

        "answer_compliance_rate": "N/A",
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

    config = load_yaml_config(CONFIG_PATH)

    report = generate_report(records, config)
    write_csv_report(report, REPORT_PATH)

    print("Operations report generated successfully.")
    print(f"Log file: {LOG_PATH}")
    print(f"Config file: {CONFIG_PATH}")
    print(f"Report file: {REPORT_PATH}")
    print()
    print("Report summary:")
    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()