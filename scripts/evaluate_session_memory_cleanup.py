import csv
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.session_memory import InMemorySessionMemory


OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
TODAY = time.strftime("%Y-%m-%d")
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_session_memory_cleanup_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_session_memory_cleanup_eval.md"


def evaluate_max_turns() -> Dict[str, Any]:
    memory = InMemorySessionMemory(max_turns=2, max_sessions=10)

    memory.add_turn("s1", "q1", "a1")
    memory.add_turn("s1", "q2", "a2")
    memory.add_turn("s1", "q3", "a3")

    turns = memory.get_recent_turns("s1")

    pass_result = (
        len(turns) == 2
        and turns[0]["question"] == "q2"
        and turns[1]["question"] == "q3"
    )

    return {
        "case_id": "max_turns_retains_recent_turns",
        "expected": "Only the latest 2 turns are retained.",
        "actual": str(turns),
        "pass": pass_result,
    }


def evaluate_ttl_cleanup() -> Dict[str, Any]:
    memory = InMemorySessionMemory(
        max_turns=3,
        max_sessions=10,
        ttl_seconds=60,
        cleanup_enabled=True,
    )

    memory.add_turn("expired", "old question", "old answer")
    memory.add_turn("active", "new question", "new answer")

    memory.session_updated_at["expired"] = time.time() - 120
    memory.session_updated_at["active"] = time.time()

    removed_count = memory.cleanup_expired_sessions()

    expired_removed = "expired" not in memory.sessions
    active_retained = "active" in memory.sessions

    return {
        "case_id": "ttl_cleanup_removes_expired_sessions",
        "expected": "Expired session is removed and active session is retained.",
        "actual": (
            f"removed_count={removed_count}; "
            f"sessions={list(memory.sessions.keys())}"
        ),
        "pass": removed_count == 1 and expired_removed and active_retained,
    }


def evaluate_cleanup_disabled() -> Dict[str, Any]:
    memory = InMemorySessionMemory(
        max_turns=3,
        max_sessions=10,
        ttl_seconds=60,
        cleanup_enabled=False,
    )

    memory.add_turn("expired", "old question", "old answer")
    memory.session_updated_at["expired"] = time.time() - 120

    removed_count = memory.cleanup_expired_sessions()

    return {
        "case_id": "cleanup_disabled_keeps_expired_sessions",
        "expected": "Expired session is retained when cleanup is disabled.",
        "actual": (
            f"removed_count={removed_count}; "
            f"sessions={list(memory.sessions.keys())}"
        ),
        "pass": removed_count == 0 and "expired" in memory.sessions,
    }


def evaluate_max_sessions() -> Dict[str, Any]:
    memory = InMemorySessionMemory(max_turns=2, max_sessions=2)

    memory.add_turn("s1", "q1", "a1")
    memory.session_updated_at["s1"] = time.time() - 30

    memory.add_turn("s2", "q2", "a2")
    memory.session_updated_at["s2"] = time.time() - 20

    memory.add_turn("s3", "q3", "a3")

    sessions = list(memory.sessions.keys())

    return {
        "case_id": "max_sessions_evicts_oldest_session",
        "expected": "Only 2 newest sessions remain and oldest session is evicted.",
        "actual": f"sessions={sessions}",
        "pass": len(sessions) == 2 and "s1" not in memory.sessions,
    }


def evaluate_json_compatibility_dict() -> Dict[str, Any]:
    memory = InMemorySessionMemory(
        max_turns=3,
        max_sessions=10,
        ttl_seconds=60,
        cleanup_enabled=True,
    )

    memory.add_turn("s1", "q1", "a1")
    exported = memory.to_dict()

    restored = InMemorySessionMemory()
    restored.load_dict(exported)

    turns = restored.get_recent_turns("s1")

    return {
        "case_id": "memory_state_export_import_compatible",
        "expected": "Memory can export and import state with TTL metadata.",
        "actual": str(turns),
        "pass": len(turns) == 1 and turns[0]["question"] == "q1",
    }


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    passing = sum(1 for item in results if item["pass"])

    return {
        "total_cases": total,
        "passing_count": passing,
        "pass_rate": round(passing / total, 4) if total else 0,
        "ttl_cleanup_pass": next(
            item["pass"]
            for item in results
            if item["case_id"] == "ttl_cleanup_removes_expired_sessions"
        ),
        "max_sessions_pass": next(
            item["pass"]
            for item in results
            if item["case_id"] == "max_sessions_evicts_oldest_session"
        ),
        "max_turns_pass": next(
            item["pass"]
            for item in results
            if item["case_id"] == "max_turns_retains_recent_turns"
        ),
        "prd_pass": passing == total,
    }


def write_csv(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "case_id",
        "expected",
        "actual",
        "pass",
        "total_cases",
        "passing_count",
        "pass_rate",
        "ttl_cleanup_pass",
        "max_sessions_pass",
        "max_turns_pass",
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
        "# Session Memory TTL and Cleanup Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: Session Memory TTL / Cleanup / Capacity Guard",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passing cases: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
        f"- TTL cleanup pass: {summary['ttl_cleanup_pass']}",
        f"- Max sessions pass: {summary['max_sessions_pass']}",
        f"- Max turns pass: {summary['max_turns_pass']}",
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
                f"- Expected: {result['expected']}",
                f"- Actual: {result['actual']}",
                f"- Pass: {result['pass']}",
                "",
            ]
        )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    results = [
        evaluate_max_turns(),
        evaluate_ttl_cleanup(),
        evaluate_cleanup_disabled(),
        evaluate_max_sessions(),
        evaluate_json_compatibility_dict(),
    ]

    summary = summarize(results)

    for index, result in enumerate(results, start=1):
        status = "✅" if result["pass"] else "❌"
        print(
            f"[{index}/{len(results)}] {result['case_id']} "
            f"{status} pass={result['pass']}"
        )
        if not result["pass"]:
            print(f"  Expected: {result['expected']}")
            print(f"  Actual: {result['actual']}")

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("SESSION MEMORY CLEANUP EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:       {summary['total_cases']}")
    print(f"  Passing cases:     {summary['passing_count']}")
    print(f"  Pass rate:         {summary['pass_rate']}")
    print(f"  TTL cleanup pass:  {summary['ttl_cleanup_pass']}")
    print(f"  Max sessions pass: {summary['max_sessions_pass']}")
    print(f"  Max turns pass:    {summary['max_turns_pass']}")
    print(f"  PRD Status:        {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
