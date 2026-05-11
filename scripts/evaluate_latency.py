import csv
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.rag.generator import create_generator
from app.rag.pii import redact_pii
from app.rag.retriever_factory import create_retriever
from app.rag.safety import check_safety


EVAL_SET_PATH = PROJECT_ROOT / "eval" / "answer_eval_set.jsonl"
CSV_REPORT_PATH = PROJECT_ROOT / "reports" / "evaluations" / "2026-05-11_latency_eval.csv"
MD_REPORT_PATH = PROJECT_ROOT / "reports" / "evaluations" / "2026-05-11_latency_eval.md"

PRD_LATENCY_THRESHOLD_MS = 10_000
PRD_WITHIN_THRESHOLD_RATE = 0.90


def load_eval_set(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Evaluation set not found: {path}")

    records = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    return records


def percentile(values: List[int], percentile_value: float) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)

    if len(sorted_values) == 1:
        return float(sorted_values[0])

    rank = (len(sorted_values) - 1) * percentile_value
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    weight = rank - lower_index

    return round(
        sorted_values[lower_index] * (1 - weight)
        + sorted_values[upper_index] * weight,
        2,
    )


def run_answer_pipeline(
    question: str,
    config: Dict[str, Any],
    retriever,
    generator,
) -> Dict[str, Any]:
    start_time = time.time()

    safety_result = check_safety(question)

    if not safety_result["safe"]:
        total_latency_ms = int((time.time() - start_time) * 1000)
        return {
            "answer": safety_result["message"],
            "refused": True,
            "refusal_reason": safety_result["reason"],
            "retrieval_latency_ms": 0,
            "generation_latency_ms": 0,
            "total_latency_ms": total_latency_ms,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "model_name": config.get("llm", {}).get("model"),
            "generator_type": config.get("generator", {}).get("type"),
            "success": True,
            "error": "",
        }

    retrieval_start = time.time()
    retrieved_chunks = retriever.retrieve(question)
    retrieval_latency_ms = int((time.time() - retrieval_start) * 1000)

    generation_start = time.time()
    generation_result = generator.generate(
        question=question,
        retrieved_chunks=retrieved_chunks,
    )
    generation_latency_ms = int((time.time() - generation_start) * 1000)

    answer = redact_pii(generation_result["answer"])
    total_latency_ms = int((time.time() - start_time) * 1000)

    return {
        "answer": answer,
        "refused": generation_result["refused"],
        "refusal_reason": generation_result["refusal_reason"],
        "retrieval_latency_ms": retrieval_latency_ms,
        "generation_latency_ms": generation_latency_ms,
        "total_latency_ms": total_latency_ms,
        "input_tokens": generation_result.get("input_tokens"),
        "output_tokens": generation_result.get("output_tokens"),
        "total_tokens": generation_result.get("total_tokens"),
        "model_name": generation_result.get("model_name"),
        "generator_type": generation_result.get("generator_type"),
        "success": True,
        "error": "",
    }


def evaluate_latency_record(
    record: Dict[str, Any],
    pipeline_result: Dict[str, Any],
) -> Dict[str, Any]:
    total_latency_ms = pipeline_result.get("total_latency_ms", 0)
    within_10s = (
        isinstance(total_latency_ms, (int, float))
        and total_latency_ms <= PRD_LATENCY_THRESHOLD_MS
    )

    return {
        "question": record.get("question", ""),
        "category": record.get("category", ""),
        "expected_refused": record.get("expected_refused", False),
        "actual_refused": pipeline_result.get("refused"),
        "refusal_reason": pipeline_result.get("refusal_reason"),
        "success": pipeline_result.get("success", False),
        "within_10s": within_10s,
        "retrieval_latency_ms": pipeline_result.get("retrieval_latency_ms"),
        "generation_latency_ms": pipeline_result.get("generation_latency_ms"),
        "total_latency_ms": pipeline_result.get("total_latency_ms"),
        "input_tokens": pipeline_result.get("input_tokens"),
        "output_tokens": pipeline_result.get("output_tokens"),
        "total_tokens": pipeline_result.get("total_tokens"),
        "model_name": pipeline_result.get("model_name"),
        "generator_type": pipeline_result.get("generator_type"),
        "error": pipeline_result.get("error", ""),
    }


def summarize(details: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_requests = len(details)

    if total_requests == 0:
        return {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "success_rate": 0,
            "within_10s_count": 0,
            "within_10s_rate": 0,
            "avg_latency_ms": 0,
            "p50_latency_ms": 0,
            "p90_latency_ms": 0,
            "p95_latency_ms": 0,
            "max_latency_ms": 0,
            "avg_retrieval_latency_ms": 0,
            "avg_generation_latency_ms": 0,
            "prd_latency_threshold_ms": PRD_LATENCY_THRESHOLD_MS,
            "prd_required_within_threshold_rate": PRD_WITHIN_THRESHOLD_RATE,
            "prd_pass": False,
        }

    successful = [item for item in details if item.get("success") is True]
    failed = [item for item in details if item.get("success") is not True]

    latencies = [
        item.get("total_latency_ms")
        for item in successful
        if isinstance(item.get("total_latency_ms"), (int, float))
    ]

    retrieval_latencies = [
        item.get("retrieval_latency_ms")
        for item in successful
        if isinstance(item.get("retrieval_latency_ms"), (int, float))
    ]

    generation_latencies = [
        item.get("generation_latency_ms")
        for item in successful
        if isinstance(item.get("generation_latency_ms"), (int, float))
    ]

    within_10s_count = sum(1 for item in successful if item.get("within_10s") is True)
    within_10s_rate = round(within_10s_count / len(successful), 4) if successful else 0

    return {
        "total_requests": total_requests,
        "successful_requests": len(successful),
        "failed_requests": len(failed),
        "success_rate": round(len(successful) / total_requests, 4),
        "within_10s_count": within_10s_count,
        "within_10s_rate": within_10s_rate,
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
        "p50_latency_ms": percentile(latencies, 0.50),
        "p90_latency_ms": percentile(latencies, 0.90),
        "p95_latency_ms": percentile(latencies, 0.95),
        "max_latency_ms": max(latencies) if latencies else 0,
        "avg_retrieval_latency_ms": round(statistics.mean(retrieval_latencies), 2)
        if retrieval_latencies
        else 0,
        "avg_generation_latency_ms": round(statistics.mean(generation_latencies), 2)
        if generation_latencies
        else 0,
        "prd_latency_threshold_ms": PRD_LATENCY_THRESHOLD_MS,
        "prd_required_within_threshold_rate": PRD_WITHIN_THRESHOLD_RATE,
        "prd_pass": within_10s_rate >= PRD_WITHIN_THRESHOLD_RATE,
    }


def write_csv_report(details: List[Dict[str, Any]], summary: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "question",
        "category",
        "expected_refused",
        "actual_refused",
        "refusal_reason",
        "success",
        "within_10s",
        "retrieval_latency_ms",
        "generation_latency_ms",
        "total_latency_ms",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "model_name",
        "generator_type",
        "error",
        "total_requests",
        "successful_requests",
        "failed_requests",
        "success_rate",
        "within_10s_count",
        "within_10s_rate",
        "avg_latency_ms",
        "p50_latency_ms",
        "p90_latency_ms",
        "p95_latency_ms",
        "max_latency_ms",
        "avg_retrieval_latency_ms",
        "avg_generation_latency_ms",
        "prd_latency_threshold_ms",
        "prd_required_within_threshold_rate",
        "prd_pass",
    ]

    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        summary_row = {field: "" for field in fieldnames}
        summary_row.update({"row_type": "summary", **summary})
        writer.writerow(summary_row)

        for detail in details:
            row = {field: "" for field in fieldnames}
            row.update(detail)
            row["row_type"] = "detail"
            writer.writerow(row)


def write_markdown_report(summary: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# Latency Evaluation Report

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Evaluation Type: Latency Evaluation  
Version: v1  
Supporting CSV: reports/evaluations/2026-05-11_latency_eval.csv

---

## 1. Objective

This evaluation validates the PRD latency requirement for the RAG service.

The PRD requires:

    90% of QA requests should complete end-to-end within 10 seconds.

This evaluation runs the QA pipeline against the answer evaluation set and records end-to-end latency for each request.

---

## 2. Dataset

Evaluation set:

    eval/answer_eval_set.jsonl

Total requests:

    {summary["total_requests"]}

---

## 3. Metrics

Measured metrics:

- success_rate
- within_10s_rate
- avg_latency_ms
- p50_latency_ms
- p90_latency_ms
- p95_latency_ms
- max_latency_ms
- avg_retrieval_latency_ms
- avg_generation_latency_ms

---

## 4. Summary Results

| Metric | Value |
|---|---:|
| Total Requests | {summary["total_requests"]} |
| Successful Requests | {summary["successful_requests"]} |
| Failed Requests | {summary["failed_requests"]} |
| Success Rate | {summary["success_rate"]} |
| Within 10s Count | {summary["within_10s_count"]} |
| Within 10s Rate | {summary["within_10s_rate"]} |
| Avg Latency ms | {summary["avg_latency_ms"]} |
| P50 Latency ms | {summary["p50_latency_ms"]} |
| P90 Latency ms | {summary["p90_latency_ms"]} |
| P95 Latency ms | {summary["p95_latency_ms"]} |
| Max Latency ms | {summary["max_latency_ms"]} |
| Avg Retrieval Latency ms | {summary["avg_retrieval_latency_ms"]} |
| Avg Generation Latency ms | {summary["avg_generation_latency_ms"]} |
| PRD Latency Threshold ms | {summary["prd_latency_threshold_ms"]} |
| Required Within-threshold Rate | {summary["prd_required_within_threshold_rate"]} |
| PRD Pass | {summary["prd_pass"]} |

---

## 5. PRD Status

PRD target:

    within_10s_rate >= 0.90

Current result:

    within_10s_rate = {summary["within_10s_rate"]}

Status:

    {"PASS" if summary["prd_pass"] else "FAIL"}

---

## 6. Notes

This is a sequential latency evaluation, not a concurrent load test.

Concurrent request handling will be evaluated separately.
"""

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def main() -> None:
    config = load_config()
    eval_set = load_eval_set(EVAL_SET_PATH)

    retriever = create_retriever(config)
    generator = create_generator(config)

    details = []

    for index, record in enumerate(eval_set, start=1):
        question = record["question"]
        print(f"Evaluating latency {index}/{len(eval_set)}: {question}")

        try:
            pipeline_result = run_answer_pipeline(
                question=question,
                config=config,
                retriever=retriever,
                generator=generator,
            )
        except Exception as exc:
            pipeline_result = {
                "answer": "",
                "refused": None,
                "refusal_reason": None,
                "retrieval_latency_ms": None,
                "generation_latency_ms": None,
                "total_latency_ms": None,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "model_name": config.get("llm", {}).get("model"),
                "generator_type": config.get("generator", {}).get("type"),
                "success": False,
                "error": str(exc),
            }

        detail = evaluate_latency_record(record, pipeline_result)
        details.append(detail)

        print(
            f"  success={detail['success']}, "
            f"within_10s={detail['within_10s']}, "
            f"latency_ms={detail['total_latency_ms']}"
        )

    summary = summarize(details)

    write_csv_report(details, summary, CSV_REPORT_PATH)
    write_markdown_report(summary, MD_REPORT_PATH)

    print()
    print("Latency evaluation completed.")
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")
    print()
    print("Summary:")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
