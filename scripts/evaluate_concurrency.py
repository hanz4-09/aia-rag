import csv
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.rag.generator import create_generator
from app.rag.pii import redact_pii
from app.rag.retriever_factory import create_retriever
from app.rag.safety import check_safety


EVAL_SET_PATH = PROJECT_ROOT / "eval" / "answer_eval_set.jsonl"
CSV_REPORT_PATH = PROJECT_ROOT / "reports" / "evaluations" / "2026-05-11_concurrency_eval.csv"
MD_REPORT_PATH = PROJECT_ROOT / "reports" / "evaluations" / "2026-05-11_concurrency_eval.md"

CONCURRENCY_LEVEL = 5
PRD_LATENCY_THRESHOLD_MS = 10_000
PRD_REQUIRED_SUCCESS_RATE = 1.0
PRD_REQUIRED_WITHIN_10S_RATE = 0.90


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


def build_pipeline_components(config: Dict[str, Any]):
    """
    Build one retriever/generator pair.

    This is intentionally done before the timed concurrency test because
    component initialization is startup cost, not per-request latency.
    """
    retriever = create_retriever(config)
    generator = create_generator(config)
    return retriever, generator


def prebuild_worker_components(
    config: Dict[str, Any],
    worker_count: int,
) -> List[Tuple[Any, Any]]:
    """
    Prebuild one retriever/generator pair per worker.

    This avoids sharing potentially non-thread-safe client objects while also
    excluding startup/model initialization time from request latency.
    """
    components = []

    print(f"Prebuilding {worker_count} retriever/generator worker components...")
    prebuild_start = time.time()

    for index in range(worker_count):
        worker_start = time.time()
        retriever, generator = build_pipeline_components(config)
        components.append((retriever, generator))
        worker_latency_ms = int((time.time() - worker_start) * 1000)
        print(f"  Worker component {index + 1}/{worker_count} ready in {worker_latency_ms} ms")

    prebuild_latency_ms = int((time.time() - prebuild_start) * 1000)
    print(f"Prebuild completed in {prebuild_latency_ms} ms")
    print()

    return components


def run_answer_pipeline(
    request_index: int,
    record: Dict[str, Any],
    config: Dict[str, Any],
    retriever,
    generator,
) -> Dict[str, Any]:
    question = record["question"]
    category = record.get("category", "")
    expected_refused = record.get("expected_refused", False)

    start_time = time.time()

    try:
        safety_result = check_safety(question)

        if not safety_result["safe"]:
            total_latency_ms = int((time.time() - start_time) * 1000)
            return {
                "request_index": request_index,
                "question": question,
                "category": category,
                "expected_refused": expected_refused,
                "actual_refused": True,
                "refusal_reason": safety_result["reason"],
                "success": True,
                "within_10s": total_latency_ms <= PRD_LATENCY_THRESHOLD_MS,
                "retrieval_latency_ms": 0,
                "generation_latency_ms": 0,
                "total_latency_ms": total_latency_ms,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "model_name": config.get("llm", {}).get("model"),
                "generator_type": config.get("generator", {}).get("type"),
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
            "request_index": request_index,
            "question": question,
            "category": category,
            "expected_refused": expected_refused,
            "actual_refused": generation_result.get("refused"),
            "refusal_reason": generation_result.get("refusal_reason"),
            "success": bool(answer.strip()),
            "within_10s": total_latency_ms <= PRD_LATENCY_THRESHOLD_MS,
            "retrieval_latency_ms": retrieval_latency_ms,
            "generation_latency_ms": generation_latency_ms,
            "total_latency_ms": total_latency_ms,
            "input_tokens": generation_result.get("input_tokens"),
            "output_tokens": generation_result.get("output_tokens"),
            "total_tokens": generation_result.get("total_tokens"),
            "model_name": generation_result.get("model_name"),
            "generator_type": generation_result.get("generator_type"),
            "error": "",
        }

    except Exception as exc:
        total_latency_ms = int((time.time() - start_time) * 1000)
        return {
            "request_index": request_index,
            "question": question,
            "category": category,
            "expected_refused": expected_refused,
            "actual_refused": None,
            "refusal_reason": None,
            "success": False,
            "within_10s": False,
            "retrieval_latency_ms": None,
            "generation_latency_ms": None,
            "total_latency_ms": total_latency_ms,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "model_name": config.get("llm", {}).get("model"),
            "generator_type": config.get("generator", {}).get("type"),
            "error": str(exc),
        }


def summarize(
    details: List[Dict[str, Any]],
    wall_clock_latency_ms: int,
    prebuild_latency_ms: int,
) -> Dict[str, Any]:
    total_requests = len(details)

    if total_requests == 0:
        return {
            "total_requests": 0,
            "concurrency_level": CONCURRENCY_LEVEL,
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
            "wall_clock_latency_ms": wall_clock_latency_ms,
            "prebuild_latency_ms": prebuild_latency_ms,
            "avg_retrieval_latency_ms": 0,
            "avg_generation_latency_ms": 0,
            "prd_required_success_rate": PRD_REQUIRED_SUCCESS_RATE,
            "prd_required_within_10s_rate": PRD_REQUIRED_WITHIN_10S_RATE,
            "prd_pass": False,
        }

    successful = [item for item in details if item.get("success") is True]
    failed = [item for item in details if item.get("success") is not True]

    latencies = [
        item.get("total_latency_ms")
        for item in details
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
    success_rate = round(len(successful) / total_requests, 4)
    within_10s_rate = round(within_10s_count / len(successful), 4) if successful else 0

    prd_pass = (
        CONCURRENCY_LEVEL >= 5
        and success_rate >= PRD_REQUIRED_SUCCESS_RATE
        and within_10s_rate >= PRD_REQUIRED_WITHIN_10S_RATE
    )

    return {
        "total_requests": total_requests,
        "concurrency_level": CONCURRENCY_LEVEL,
        "successful_requests": len(successful),
        "failed_requests": len(failed),
        "success_rate": success_rate,
        "within_10s_count": within_10s_count,
        "within_10s_rate": within_10s_rate,
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
        "p50_latency_ms": percentile(latencies, 0.50),
        "p90_latency_ms": percentile(latencies, 0.90),
        "p95_latency_ms": percentile(latencies, 0.95),
        "max_latency_ms": max(latencies) if latencies else 0,
        "wall_clock_latency_ms": wall_clock_latency_ms,
        "prebuild_latency_ms": prebuild_latency_ms,
        "avg_retrieval_latency_ms": round(statistics.mean(retrieval_latencies), 2)
        if retrieval_latencies
        else 0,
        "avg_generation_latency_ms": round(statistics.mean(generation_latencies), 2)
        if generation_latencies
        else 0,
        "prd_required_success_rate": PRD_REQUIRED_SUCCESS_RATE,
        "prd_required_within_10s_rate": PRD_REQUIRED_WITHIN_10S_RATE,
        "prd_pass": prd_pass,
    }


def write_csv_report(details: List[Dict[str, Any]], summary: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "request_index",
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
        "concurrency_level",
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
        "wall_clock_latency_ms",
        "prebuild_latency_ms",
        "avg_retrieval_latency_ms",
        "avg_generation_latency_ms",
        "prd_required_success_rate",
        "prd_required_within_10s_rate",
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

    content = f"""# Concurrency Evaluation Report

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Evaluation Type: Concurrency Evaluation  
Version: v1  
Supporting CSV: reports/evaluations/2026-05-11_concurrency_eval.csv

---

## 1. Objective

This evaluation validates the PRD concurrency requirement for the RAG service.

The PRD requires:

    A single instance should support at least 5 concurrent requests.

This evaluation runs 5 requests concurrently through the QA pipeline and records success rate and latency.

---

## 2. Important Measurement Note

The retriever and generator are prebuilt before the timed concurrency window.

This is intentional because model loading, embedding model initialization, and client initialization are startup costs, not per-request latency in a running service.

The reported request latency measures the actual concurrent request processing time after components are initialized.

---

## 3. Dataset

Evaluation set:

    eval/answer_eval_set.jsonl

Concurrency level:

    {summary["concurrency_level"]}

Total requests executed:

    {summary["total_requests"]}

---

## 4. Summary Results

| Metric | Value |
|---|---:|
| Total Requests | {summary["total_requests"]} |
| Concurrency Level | {summary["concurrency_level"]} |
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
| Wall-clock Latency ms | {summary["wall_clock_latency_ms"]} |
| Prebuild Latency ms | {summary["prebuild_latency_ms"]} |
| Avg Retrieval Latency ms | {summary["avg_retrieval_latency_ms"]} |
| Avg Generation Latency ms | {summary["avg_generation_latency_ms"]} |
| Required Success Rate | {summary["prd_required_success_rate"]} |
| Required Within 10s Rate | {summary["prd_required_within_10s_rate"]} |
| PRD Pass | {summary["prd_pass"]} |

---

## 5. PRD Status

PRD target:

    single instance supports at least 5 concurrent requests

Additional acceptance criteria used in this evaluation:

    success_rate >= 1.0
    within_10s_rate >= 0.90

Current result:

    concurrency_level = {summary["concurrency_level"]}
    success_rate = {summary["success_rate"]}
    within_10s_rate = {summary["within_10s_rate"]}

Status:

    {"PASS" if summary["prd_pass"] else "FAIL"}

---

## 6. Notes

This evaluation uses an in-process concurrent execution model with ThreadPoolExecutor.

It validates local pipeline concurrency behavior, but it is not a full production load test through an HTTP server.
"""

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def main() -> None:
    config = load_config()
    eval_set = load_eval_set(EVAL_SET_PATH)

    selected_records = eval_set[:CONCURRENCY_LEVEL]

    print(f"Concurrency level: {CONCURRENCY_LEVEL}")
    print(f"Total selected requests: {len(selected_records)}")
    print()

    prebuild_start = time.time()
    worker_components = prebuild_worker_components(config, CONCURRENCY_LEVEL)
    prebuild_latency_ms = int((time.time() - prebuild_start) * 1000)

    print("Starting timed concurrent request execution...")
    print()

    start_wall_clock = time.time()
    details = []

    with ThreadPoolExecutor(max_workers=CONCURRENCY_LEVEL) as executor:
        future_to_index = {}

        for index, record in enumerate(selected_records, start=1):
            retriever, generator = worker_components[index - 1]
            future = executor.submit(
                run_answer_pipeline,
                index,
                record,
                config,
                retriever,
                generator,
            )
            future_to_index[future] = index

        for future in as_completed(future_to_index):
            detail = future.result()
            details.append(detail)

            print(
                f"Request {detail['request_index']}: "
                f"success={detail['success']}, "
                f"within_10s={detail['within_10s']}, "
                f"latency_ms={detail['total_latency_ms']}"
            )

    wall_clock_latency_ms = int((time.time() - start_wall_clock) * 1000)

    details.sort(key=lambda item: item["request_index"])
    summary = summarize(details, wall_clock_latency_ms, prebuild_latency_ms)

    write_csv_report(details, summary, CSV_REPORT_PATH)
    write_markdown_report(summary, MD_REPORT_PATH)

    print()
    print("Concurrency evaluation completed.")
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")
    print()
    print("Summary:")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()