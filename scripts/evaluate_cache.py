import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.main import app


LOG_PATH = PROJECT_ROOT / "logs" / "rag_service.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
TODAY = time.strftime("%Y-%m-%d")
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_cache_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_cache_eval.md"


CACHE_CASES = [
    {
        "case_id": "cache_audit_logging",
        "question": "What are the audit logging requirements?",
        "session_id": "eval-cache-audit-001",
        "expected_keywords": ["audit logs", "timestamp", "user identity"],
    },
    {
        "case_id": "cache_api_key_leak",
        "question": "API Key 泄露后应该怎么处理？",
        "session_id": "eval-cache-apikey-001",
        "expected_keywords": ["API Key", "24 小时", "吊销"],
    },
]


def count_log_lines() -> int:
    if not LOG_PATH.exists():
        return 0

    with LOG_PATH.open("r", encoding="utf-8") as file:
        return sum(1 for _ in file)


def read_new_logs(start_line_count: int) -> List[Dict[str, Any]]:
    if not LOG_PATH.exists():
        return []

    records = []

    with LOG_PATH.open("r", encoding="utf-8") as file:
        for index, line in enumerate(file):
            if index < start_line_count:
                continue

            line = line.strip()
            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return records


def contains_keyword(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def keyword_hit_rate(answer: str, expected_keywords: List[str]) -> float:
    if not expected_keywords:
        return 1.0

    matched = sum(
        1 for keyword in expected_keywords if contains_keyword(answer, keyword)
    )

    return round(matched / len(expected_keywords), 4)


def post_chat(client: TestClient, question: str, session_id: str) -> Dict[str, Any]:
    response = client.post(
        "/chat",
        json={
            "question": question,
            "session_id": session_id,
        },
    )
    response.raise_for_status()
    return response.json()


def evaluate_case(case: Dict[str, Any]) -> Dict[str, Any]:
    client = TestClient(app)

    start_log_lines = count_log_lines()

    first_start = time.time()
    first_response = post_chat(
        client=client,
        question=case["question"],
        session_id=case["session_id"],
    )
    first_elapsed_ms = int((time.time() - first_start) * 1000)

    second_start = time.time()
    second_response = post_chat(
        client=client,
        question=case["question"],
        session_id=case["session_id"],
    )
    second_elapsed_ms = int((time.time() - second_start) * 1000)

    new_logs = read_new_logs(start_log_lines)

    case_logs = [
        item
        for item in new_logs
        if item.get("session_id") == case["session_id"]
        and item.get("query") == case["question"]
    ]

    first_log = case_logs[0] if len(case_logs) >= 1 else {}
    second_log = case_logs[1] if len(case_logs) >= 2 else {}

    first_cache_hit = first_log.get("cache_hit")
    second_cache_hit = second_log.get("cache_hit")

    answer = second_response.get("answer", "")
    hit_rate = keyword_hit_rate(answer, case.get("expected_keywords", []))

    pass_result = all(
        [
            first_response.get("refused") is False,
            second_response.get("refused") is False,
            first_cache_hit is False,
            second_cache_hit is True,
            bool(answer.strip()),
            hit_rate >= 0.5,
        ]
    )

    return {
        "case_id": case["case_id"],
        "question": case["question"],
        "session_id": case["session_id"],
        "first_refused": first_response.get("refused"),
        "second_refused": second_response.get("refused"),
        "first_cache_hit": first_cache_hit,
        "second_cache_hit": second_cache_hit,
        "first_response_latency_ms": first_response.get("latency_ms"),
        "second_response_latency_ms": second_response.get("latency_ms"),
        "first_measured_latency_ms": first_elapsed_ms,
        "second_measured_latency_ms": second_elapsed_ms,
        "latency_improved": (
            second_elapsed_ms <= first_elapsed_ms
            if first_elapsed_ms is not None and second_elapsed_ms is not None
            else False
        ),
        "keyword_hit_rate": hit_rate,
        "logs_found": len(case_logs),
        "pass": pass_result,
        "answer_preview": answer[:300].replace("\n", " "),
    }


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    passing = sum(1 for item in results if item["pass"])
    second_cache_hits = sum(1 for item in results if item["second_cache_hit"] is True)
    first_cache_misses = sum(1 for item in results if item["first_cache_hit"] is False)
    latency_improved = sum(1 for item in results if item["latency_improved"] is True)

    keyword_rates = [
        item["keyword_hit_rate"]
        for item in results
        if isinstance(item.get("keyword_hit_rate"), (int, float))
    ]

    avg_keyword_hit_rate = (
        round(sum(keyword_rates) / len(keyword_rates), 4)
        if keyword_rates
        else 0
    )

    return {
        "total_cases": total,
        "passing_count": passing,
        "pass_rate": round(passing / total, 4) if total else 0,
        "first_cache_miss_count": first_cache_misses,
        "first_cache_miss_rate": round(first_cache_misses / total, 4)
        if total
        else 0,
        "second_cache_hit_count": second_cache_hits,
        "second_cache_hit_rate": round(second_cache_hits / total, 4)
        if total
        else 0,
        "latency_improved_count": latency_improved,
        "latency_improved_rate": round(latency_improved / total, 4)
        if total
        else 0,
        "avg_keyword_hit_rate": avg_keyword_hit_rate,
        "prd_pass": passing == total,
    }


def write_csv(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    CSV_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "case_id",
        "question",
        "session_id",
        "first_refused",
        "second_refused",
        "first_cache_hit",
        "second_cache_hit",
        "first_response_latency_ms",
        "second_response_latency_ms",
        "first_measured_latency_ms",
        "second_measured_latency_ms",
        "latency_improved",
        "keyword_hit_rate",
        "logs_found",
        "pass",
        "answer_preview",
        "total_cases",
        "passing_count",
        "pass_rate",
        "first_cache_miss_count",
        "first_cache_miss_rate",
        "second_cache_hit_count",
        "second_cache_hit_rate",
        "latency_improved_count",
        "latency_improved_rate",
        "avg_keyword_hit_rate",
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
        "# Cache Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: Cache Behavior Evaluation",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passing cases: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
        f"- First cache miss rate: {summary['first_cache_miss_rate']}",
        f"- Second cache hit rate: {summary['second_cache_hit_rate']}",
        f"- Latency improved rate: {summary['latency_improved_rate']}",
        f"- Avg keyword hit rate: {summary['avg_keyword_hit_rate']}",
        f"- PRD pass: {summary['prd_pass']}",
        "",
        "## Method",
        "",
        "Each case sends the same question twice with the same session_id.",
        "The first request is expected to miss the cache.",
        "The second request is expected to hit the cache.",
        "The evaluator checks cache_hit values from structured JSONL logs.",
        "",
        "## Case Results",
        "",
    ]

    for result in results:
        lines.extend(
            [
                f"### {result['case_id']}",
                "",
                f"- Question: {result['question']}",
                f"- First cache hit: {result['first_cache_hit']}",
                f"- Second cache hit: {result['second_cache_hit']}",
                f"- First measured latency ms: {result['first_measured_latency_ms']}",
                f"- Second measured latency ms: {result['second_measured_latency_ms']}",
                f"- Latency improved: {result['latency_improved']}",
                f"- Keyword hit rate: {result['keyword_hit_rate']}",
                f"- Pass: {result['pass']}",
                "",
            ]
        )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    print(f"Total cache eval cases: {len(CACHE_CASES)}")
    print()

    results = []

    for index, case in enumerate(CACHE_CASES, start=1):
        print(f"[{index}/{len(CACHE_CASES)}] {case['case_id']}")

        result = evaluate_case(case)
        results.append(result)

        status = "✅" if result["pass"] else "❌"
        print(
            f"  {status} pass={result['pass']}, "
            f"first_cache_hit={result['first_cache_hit']}, "
            f"second_cache_hit={result['second_cache_hit']}, "
            f"first_latency={result['first_measured_latency_ms']}ms, "
            f"second_latency={result['second_measured_latency_ms']}ms"
        )

    summary = summarize(results)

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("CACHE EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:             {summary['total_cases']}")
    print(f"  Passing cases:           {summary['passing_count']}")
    print(f"  Pass rate:               {summary['pass_rate']}")
    print(f"  First cache miss rate:   {summary['first_cache_miss_rate']}")
    print(f"  Second cache hit rate:   {summary['second_cache_hit_rate']}")
    print(f"  Latency improved rate:   {summary['latency_improved_rate']}")
    print(f"  Avg keyword hit rate:    {summary['avg_keyword_hit_rate']}")
    print(f"  PRD Status:              {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
