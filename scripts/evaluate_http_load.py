import argparse
import asyncio
import csv
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

TODAY = time.strftime("%Y-%m-%d")
OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_http_load_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_http_load_eval.md"


DEFAULT_REQUESTS = [
    {
        "case_id": "http_audit_logging",
        "payload": {
            "question": "What are the audit logging requirements?",
            "session_id": "http-load-audit-001",
        },
    },
    {
        "case_id": "http_api_key_leak",
        "payload": {
            "question": "API Key 泄露后应该怎么处理？",
            "session_id": "http-load-security-001",
        },
    },
    {
        "case_id": "http_akp_endpoints",
        "payload": {
            "question": "What endpoints does the AKP Platform provide?",
            "session_id": "http-load-akp-001",
        },
    },
    {
        "case_id": "http_cn_architecture",
        "payload": {
            "question": "AKP Platform 的核心模块有哪些？",
            "session_id": "http-load-arch-001",
        },
    },
    {
        "case_id": "http_retention_policy",
        "payload": {
            "question": "What are the log retention requirements?",
            "session_id": "http-load-retention-001",
        },
    },
]


def percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]

    index = (len(sorted_values) - 1) * pct
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = index - lower

    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


async def send_request(
    client: httpx.AsyncClient,
    base_url: str,
    case: Dict[str, Any],
    timeout_seconds: int,
) -> Dict[str, Any]:
    case_id = case["case_id"]
    payload = case["payload"]

    start_time = time.time()

    try:
        response = await client.post(
            f"{base_url.rstrip('/')}/chat",
            json=payload,
            timeout=timeout_seconds,
        )
        elapsed_ms = int((time.time() - start_time) * 1000)

        success = response.status_code == 200

        response_json: Dict[str, Any] = {}
        error = ""

        try:
            response_json = response.json()
        except Exception as exc:
            error = f"response_json_parse_error: {exc}"

        return {
            "case_id": case_id,
            "status_code": response.status_code,
            "success": success,
            "within_10s": elapsed_ms <= 10000,
            "latency_ms": elapsed_ms,
            "answer_latency_ms": response_json.get("latency_ms"),
            "refused": response_json.get("refused"),
            "refusal_reason": response_json.get("refusal_reason"),
            "source_count": len(response_json.get("sources", []) or []),
            "answer_preview": str(response_json.get("answer", ""))[:200].replace(
                "\n",
                " ",
            ),
            "error": error,
        }

    except Exception as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "case_id": case_id,
            "status_code": "",
            "success": False,
            "within_10s": False,
            "latency_ms": elapsed_ms,
            "answer_latency_ms": "",
            "refused": "",
            "refusal_reason": "",
            "source_count": "",
            "answer_preview": "",
            "error": str(exc),
        }


async def run_http_load(
    base_url: str,
    concurrency_level: int,
    total_requests: int,
    timeout_seconds: int,
) -> List[Dict[str, Any]]:
    selected_cases = []

    for index in range(total_requests):
        case = DEFAULT_REQUESTS[index % len(DEFAULT_REQUESTS)]
        selected_cases.append(
            {
                "case_id": f"{case['case_id']}_{index + 1}",
                "payload": {
                    **case["payload"],
                    "session_id": f"{case['payload'].get('session_id')}-{index + 1}",
                },
            }
        )

    semaphore = asyncio.Semaphore(concurrency_level)

    async with httpx.AsyncClient() as client:

        async def bounded_send(case: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await send_request(
                    client=client,
                    base_url=base_url,
                    case=case,
                    timeout_seconds=timeout_seconds,
                )

        tasks = [bounded_send(case) for case in selected_cases]
        return await asyncio.gather(*tasks)


def summarize(
    results: List[Dict[str, Any]],
    concurrency_level: int,
) -> Dict[str, Any]:
    total = len(results)
    successful = sum(1 for item in results if item["success"])
    failed = total - successful
    within_10s = sum(1 for item in results if item["within_10s"])
    refused = sum(1 for item in results if item.get("refused") is True)

    latencies = [
        float(item["latency_ms"])
        for item in results
        if isinstance(item.get("latency_ms"), int)
    ]

    avg_latency = round(statistics.mean(latencies), 2) if latencies else 0.0
    p50_latency = round(percentile(latencies, 0.50), 2) if latencies else 0.0
    p95_latency = round(percentile(latencies, 0.95), 2) if latencies else 0.0
    max_latency = int(max(latencies)) if latencies else 0

    success_rate = round(successful / total, 4) if total else 0.0
    within_10s_rate = round(within_10s / total, 4) if total else 0.0
    refusal_rate = round(refused / total, 4) if total else 0.0

    prd_pass = (
        total > 0
        and concurrency_level >= 5
        and success_rate == 1.0
        and within_10s_rate >= 0.9
    )

    return {
        "total_requests": total,
        "concurrency_level": concurrency_level,
        "successful_requests": successful,
        "failed_requests": failed,
        "success_rate": success_rate,
        "within_10s_count": within_10s,
        "within_10s_rate": within_10s_rate,
        "refusal_count": refused,
        "refusal_rate": refusal_rate,
        "avg_latency_ms": avg_latency,
        "p50_latency_ms": p50_latency,
        "p95_latency_ms": p95_latency,
        "max_latency_ms": max_latency,
        "prd_pass": prd_pass,
    }


def write_csv(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "case_id",
        "status_code",
        "success",
        "within_10s",
        "latency_ms",
        "answer_latency_ms",
        "refused",
        "refusal_reason",
        "source_count",
        "answer_preview",
        "error",
        "total_requests",
        "concurrency_level",
        "successful_requests",
        "failed_requests",
        "success_rate",
        "within_10s_count",
        "within_10s_rate",
        "refusal_count",
        "refusal_rate",
        "avg_latency_ms",
        "p50_latency_ms",
        "p95_latency_ms",
        "max_latency_ms",
        "wall_clock_latency_ms",
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
        "# HTTP Load Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: HTTP-level Load Test",
        "",
        "## Summary",
        "",
        f"- Total requests: {summary['total_requests']}",
        f"- Concurrency level: {summary['concurrency_level']}",
        f"- Successful requests: {summary['successful_requests']}",
        f"- Failed requests: {summary['failed_requests']}",
        f"- Success rate: {summary['success_rate']}",
        f"- Within 10s rate: {summary['within_10s_rate']}",
        f"- Refusal rate: {summary['refusal_rate']}",
        f"- Average latency ms: {summary['avg_latency_ms']}",
        f"- P50 latency ms: {summary['p50_latency_ms']}",
        f"- P95 latency ms: {summary['p95_latency_ms']}",
        f"- Max latency ms: {summary['max_latency_ms']}",
        f"- PRD pass: {summary['prd_pass']}",
        "",
        "## Method",
        "",
        "This evaluation sends concurrent HTTP POST requests to the FastAPI `/chat` endpoint.",
        "It complements the internal latency and concurrency evaluation scripts by validating the API boundary.",
        "",
        "Default pass criteria:",
        "",
        "- concurrency_level >= 5",
        "- success_rate = 1.0",
        "- within_10s_rate >= 0.9",
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
                f"- Success: {result['success']}",
                f"- Within 10s: {result['within_10s']}",
                f"- Latency ms: {result['latency_ms']}",
                f"- Answer latency ms: {result['answer_latency_ms']}",
                f"- Refused: {result['refused']}",
                f"- Refusal reason: {result['refusal_reason']}",
                f"- Source count: {result['source_count']}",
                f"- Error: {result['error'] or 'None'}",
                "",
            ]
        )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate HTTP-level FastAPI /chat load."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the running FastAPI service.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Concurrent HTTP requests.",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=10,
        help="Total number of HTTP requests to send.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP request timeout in seconds.",
    )

    args = parser.parse_args()

    print("HTTP Load Evaluation")
    print(f"Base URL: {args.base_url}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Total requests: {args.requests}")
    print(f"Timeout seconds: {args.timeout}")
    print()

    start_time = time.time()

    results = asyncio.run(
        run_http_load(
            base_url=args.base_url,
            concurrency_level=args.concurrency,
            total_requests=args.requests,
            timeout_seconds=args.timeout,
        )
    )

    wall_clock_ms = int((time.time() - start_time) * 1000)
    summary = summarize(results, args.concurrency)
    summary["wall_clock_latency_ms"] = wall_clock_ms

    for index, result in enumerate(results, start=1):
        status = "✅" if result["success"] and result["within_10s"] else "❌"
        print(
            f"[{index}/{len(results)}] {result['case_id']} "
            f"{status} status={result['status_code']}, "
            f"latency={result['latency_ms']}ms, "
            f"within_10s={result['within_10s']}, "
            f"refused={result['refused']}"
        )
        if result["error"]:
            print(f"  Error: {result['error']}")

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("HTTP LOAD EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total requests:        {summary['total_requests']}")
    print(f"  Concurrency level:     {summary['concurrency_level']}")
    print(f"  Successful requests:   {summary['successful_requests']}")
    print(f"  Failed requests:       {summary['failed_requests']}")
    print(f"  Success rate:          {summary['success_rate']}")
    print(f"  Within 10s rate:       {summary['within_10s_rate']}")
    print(f"  Refusal rate:          {summary['refusal_rate']}")
    print(f"  Avg latency ms:        {summary['avg_latency_ms']}")
    print(f"  P50 latency ms:        {summary['p50_latency_ms']}")
    print(f"  P95 latency ms:        {summary['p95_latency_ms']}")
    print(f"  Max latency ms:        {summary['max_latency_ms']}")
    print(f"  Wall clock ms:         {summary['wall_clock_latency_ms']}")
    print(f"  PRD Status:            {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
