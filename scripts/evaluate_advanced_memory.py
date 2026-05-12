import csv
import json
import tempfile
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.core.session_memory import PersistentSessionMemory
from app.rag.generator import create_generator
from app.rag.pii import redact_pii
from app.rag.query_rewriter import build_history_aware_retrieval_query
from app.rag.retriever_factory import create_retriever
from app.rag.safety import check_safety


OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
TODAY = time.strftime("%Y-%m-%d")
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_advanced_memory_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_advanced_memory_eval.md"

MEMORY_EVAL_DIR = Path(tempfile.gettempdir()) / "aia_rag_session_memory_eval" / time.strftime("%Y%m%d_%H%M%S")
MEMORY_EVAL_PATH = MEMORY_EVAL_DIR / "advanced_memory_eval.json"


ADVANCED_MEMORY_CASES = [
    {
        "case_id": "am_audit_log_retention",
        "category": "compliance",
        "session_id": "eval-advanced-memory-audit-001",
        "turns": [
            "What are the audit logging requirements?",
            "How long should they be retained?",
        ],
        "expected_source": "03_compliance_guide_en.txt",
        "expected_keywords": [
            "audit logs",
            "privileged operations",
            "one year",
        ],
    },
    {
        "case_id": "am_api_key_report_window",
        "category": "security_cn",
        "session_id": "eval-advanced-memory-apikey-001",
        "turns": [
            "API Key 泄露后应该怎么处理？",
            "多久内要报告？",
        ],
        "expected_source": "04_data_security_policy_cn.txt",
        "expected_keywords": [
            "24 小时",
            "Security Operations",
            "报告",
        ],
    },
]


def contains_keyword(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def evaluate_keywords(answer: str, expected_keywords: List[str]) -> Dict[str, Any]:
    matched = []
    missing = []

    for keyword in expected_keywords:
        if contains_keyword(answer, keyword):
            matched.append(keyword)
        else:
            missing.append(keyword)

    total = len(expected_keywords)
    hit_rate = len(matched) / total if total else 1.0

    return {
        "expected_keywords_total": total,
        "expected_keywords_matched": len(matched),
        "keyword_hit_rate": round(hit_rate, 4),
        "missing_keywords": "|".join(missing),
    }


def source_hit(sources: List[Dict[str, Any]], expected_source: str) -> bool:
    if not expected_source:
        return True

    filenames = [source.get("filename") for source in sources]
    return expected_source in filenames


def load_memory_file() -> Dict[str, Any]:
    if not MEMORY_EVAL_PATH.exists():
        return {}

    return json.loads(MEMORY_EVAL_PATH.read_text(encoding="utf-8"))


def session_persisted(session_id: str, expected_turn_count: int) -> bool:
    payload = load_memory_file()
    sessions = payload.get("sessions", {})
    turns = sessions.get(session_id, [])

    return len(turns) >= expected_turn_count


def run_turn(
    question: str,
    session_id: str,
    memory: PersistentSessionMemory,
    retriever,
    generator,
) -> Dict[str, Any]:
    start_time = time.time()

    redacted_question = redact_pii(question)
    safety_result = check_safety(redacted_question)

    conversation_history = memory.get_history(session_id)
    rewrite_result = build_history_aware_retrieval_query(
        question=redacted_question,
        conversation_history=conversation_history,
    )

    retrieval_query = str(rewrite_result["retrieval_query"])

    if not safety_result["safe"]:
        return {
            "question": question,
            "answer": safety_result["message"],
            "refused": True,
            "refusal_reason": safety_result["reason"],
            "sources": [],
            "retrieved_sources": [],
            "history_turns_used": len(conversation_history),
            "retrieval_query": retrieval_query,
            "memory_rewrite_applied": rewrite_result["memory_rewrite_applied"],
            "memory_rewrite_strategy": rewrite_result["rewrite_strategy"],
            "latency_ms": int((time.time() - start_time) * 1000),
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "model_name": None,
            "generator_type": None,
        }

    retrieved_chunks = retriever.retrieve(retrieval_query)

    generation_result = generator.generate(
        question=redacted_question,
        retrieved_chunks=retrieved_chunks,
        conversation_history=conversation_history,
    )

    answer = redact_pii(generation_result["answer"])

    if not generation_result["refused"]:
        memory.add_turn(
            session_id=session_id,
            question=redacted_question,
            answer=answer,
        )

    return {
        "question": question,
        "answer": answer,
        "refused": generation_result["refused"],
        "refusal_reason": generation_result["refusal_reason"],
        "sources": generation_result["sources"],
        "retrieved_sources": [
            chunk.get("metadata", {}).get("filename")
            for chunk in retrieved_chunks
        ],
        "history_turns_used": len(conversation_history),
        "retrieval_query": retrieval_query,
        "memory_rewrite_applied": rewrite_result["memory_rewrite_applied"],
        "memory_rewrite_strategy": rewrite_result["rewrite_strategy"],
        "latency_ms": int((time.time() - start_time) * 1000),
        "input_tokens": generation_result.get("input_tokens"),
        "output_tokens": generation_result.get("output_tokens"),
        "total_tokens": generation_result.get("total_tokens"),
        "model_name": generation_result.get("model_name"),
        "generator_type": generation_result.get("generator_type"),
    }


def evaluate_case(
    case: Dict[str, Any],
    retriever,
    generator,
) -> Dict[str, Any]:
    memory = PersistentSessionMemory(
        max_turns=3,
        storage_path=str(MEMORY_EVAL_PATH),
        max_sessions=100,
    )

    session_id = case["session_id"]
    turn_1_question = case["turns"][0]
    turn_2_question = case["turns"][1]

    first_result = run_turn(
        question=turn_1_question,
        session_id=session_id,
        memory=memory,
        retriever=retriever,
        generator=generator,
    )

    first_turn_persisted = session_persisted(
        session_id=session_id,
        expected_turn_count=1,
    )

    second_result = run_turn(
        question=turn_2_question,
        session_id=session_id,
        memory=memory,
        retriever=retriever,
        generator=generator,
    )

    second_turn_persisted = session_persisted(
        session_id=session_id,
        expected_turn_count=2,
    )

    keyword_result = evaluate_keywords(
        answer=second_result["answer"],
        expected_keywords=case.get("expected_keywords", []),
    )

    second_source_hit = source_hit(
        sources=second_result["sources"],
        expected_source=case.get("expected_source", ""),
    )

    history_used = second_result["history_turns_used"] > 0
    rewrite_applied = second_result["memory_rewrite_applied"] is True
    retrieval_query = second_result["retrieval_query"]

    previous_question_in_retrieval_query = (
        turn_1_question in retrieval_query
        and turn_2_question in retrieval_query
    )

    pass_result = all(
        [
            first_turn_persisted,
            second_turn_persisted,
            history_used,
            rewrite_applied,
            previous_question_in_retrieval_query,
            not second_result["refused"],
            second_source_hit,
            keyword_result["keyword_hit_rate"] >= 0.5,
        ]
    )

    return {
        "case_id": case["case_id"],
        "category": case.get("category", ""),
        "session_id": session_id,
        "turn_1_question": turn_1_question,
        "turn_2_question": turn_2_question,
        "turn_1_refused": first_result["refused"],
        "turn_2_refused": second_result["refused"],
        "turn_2_refusal_reason": second_result["refusal_reason"],
        "first_turn_persisted": first_turn_persisted,
        "second_turn_persisted": second_turn_persisted,
        "history_turns_used": second_result["history_turns_used"],
        "history_used": history_used,
        "memory_rewrite_applied": rewrite_applied,
        "memory_rewrite_strategy": second_result["memory_rewrite_strategy"],
        "previous_question_in_retrieval_query": previous_question_in_retrieval_query,
        "retrieval_query": retrieval_query.replace("\n", "\\n"),
        "expected_source": case.get("expected_source", ""),
        "source_hit": second_source_hit,
        "retrieved_sources": "|".join(
            [source or "" for source in second_result["retrieved_sources"]]
        ),
        "expected_keywords_total": keyword_result["expected_keywords_total"],
        "expected_keywords_matched": keyword_result["expected_keywords_matched"],
        "keyword_hit_rate": keyword_result["keyword_hit_rate"],
        "missing_keywords": keyword_result["missing_keywords"],
        "turn_1_latency_ms": first_result["latency_ms"],
        "turn_2_latency_ms": second_result["latency_ms"],
        "turn_2_input_tokens": second_result["input_tokens"],
        "turn_2_output_tokens": second_result["output_tokens"],
        "turn_2_total_tokens": second_result["total_tokens"],
        "model_name": second_result["model_name"],
        "generator_type": second_result["generator_type"],
        "pass": pass_result,
        "turn_2_answer_preview": second_result["answer"][:300].replace("\n", " "),
    }


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)

    passing = sum(1 for item in results if item["pass"])
    persisted = sum(1 for item in results if item["second_turn_persisted"])
    rewrite_applied = sum(1 for item in results if item["memory_rewrite_applied"])
    retrieval_query_resolved = sum(
        1 for item in results if item["previous_question_in_retrieval_query"]
    )
    source_hits = sum(1 for item in results if item["source_hit"])

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
        "persistent_memory_pass_count": persisted,
        "persistent_memory_pass_rate": round(persisted / total, 4) if total else 0,
        "query_rewrite_applied_count": rewrite_applied,
        "query_rewrite_applied_rate": round(rewrite_applied / total, 4)
        if total
        else 0,
        "retrieval_query_resolution_count": retrieval_query_resolved,
        "retrieval_query_resolution_rate": round(
            retrieval_query_resolved / total,
            4,
        )
        if total
        else 0,
        "source_hit_count": source_hits,
        "source_hit_rate": round(source_hits / total, 4) if total else 0,
        "avg_keyword_hit_rate": avg_keyword_hit_rate,
        "prd_pass": passing == total,
    }


def write_csv(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    CSV_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "case_id",
        "category",
        "session_id",
        "turn_1_question",
        "turn_2_question",
        "turn_1_refused",
        "turn_2_refused",
        "turn_2_refusal_reason",
        "first_turn_persisted",
        "second_turn_persisted",
        "history_turns_used",
        "history_used",
        "memory_rewrite_applied",
        "memory_rewrite_strategy",
        "previous_question_in_retrieval_query",
        "retrieval_query",
        "expected_source",
        "source_hit",
        "retrieved_sources",
        "expected_keywords_total",
        "expected_keywords_matched",
        "keyword_hit_rate",
        "missing_keywords",
        "turn_1_latency_ms",
        "turn_2_latency_ms",
        "turn_2_input_tokens",
        "turn_2_output_tokens",
        "turn_2_total_tokens",
        "model_name",
        "generator_type",
        "pass",
        "turn_2_answer_preview",
        "total_cases",
        "passing_count",
        "pass_rate",
        "persistent_memory_pass_count",
        "persistent_memory_pass_rate",
        "query_rewrite_applied_count",
        "query_rewrite_applied_rate",
        "retrieval_query_resolution_count",
        "retrieval_query_resolution_rate",
        "source_hit_count",
        "source_hit_rate",
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
        "# Advanced Memory Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: Advanced Memory v1 Evaluation",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passing cases: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
        f"- Persistent memory pass rate: {summary['persistent_memory_pass_rate']}",
        f"- Query rewrite applied rate: {summary['query_rewrite_applied_rate']}",
        f"- Retrieval query resolution rate: {summary['retrieval_query_resolution_rate']}",
        f"- Source hit rate: {summary['source_hit_rate']}",
        f"- Avg keyword hit rate: {summary['avg_keyword_hit_rate']}",
        f"- PRD pass: {summary['prd_pass']}",
        "",
        "## Method",
        "",
        "Each case contains two turns with the same session_id.",
        "The evaluator validates persistent memory, history-aware retrieval query rewriting,",
        "source hit, and keyword coverage on the second turn.",
        "",
        "## Case Results",
        "",
    ]

    for result in results:
        lines.extend(
            [
                f"### {result['case_id']}",
                "",
                f"- Category: {result['category']}",
                f"- Turn 1: {result['turn_1_question']}",
                f"- Turn 2: {result['turn_2_question']}",
                f"- First turn persisted: {result['first_turn_persisted']}",
                f"- Second turn persisted: {result['second_turn_persisted']}",
                f"- History turns used: {result['history_turns_used']}",
                f"- Memory rewrite applied: {result['memory_rewrite_applied']}",
                f"- Rewrite strategy: {result['memory_rewrite_strategy']}",
                f"- Previous question in retrieval query: {result['previous_question_in_retrieval_query']}",
                f"- Source hit: {result['source_hit']}",
                f"- Keyword hit rate: {result['keyword_hit_rate']}",
                f"- Pass: {result['pass']}",
                f"- Answer preview: {result['turn_2_answer_preview']}",
                "",
            ]
        )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():

    config = load_config()
    retriever = create_retriever(config)
    generator = create_generator(config)

    print(f"Total advanced memory eval cases: {len(ADVANCED_MEMORY_CASES)}")
    print(f"Memory eval file: {MEMORY_EVAL_PATH}")
    print()

    results = []

    for index, case in enumerate(ADVANCED_MEMORY_CASES, start=1):
        print(f"[{index}/{len(ADVANCED_MEMORY_CASES)}] {case['case_id']}")

        result = evaluate_case(
            case=case,
            retriever=retriever,
            generator=generator,
        )
        results.append(result)

        status = "✅" if result["pass"] else "❌"
        print(
            f"  {status} pass={result['pass']}, "
            f"persisted={result['second_turn_persisted']}, "
            f"rewrite={result['memory_rewrite_applied']}, "
            f"source_hit={result['source_hit']}, "
            f"keyword_hit_rate={result['keyword_hit_rate']}"
        )

        if result["missing_keywords"]:
            print(f"     Missing keywords: {result['missing_keywords']}")

    summary = summarize(results)

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("ADVANCED MEMORY EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:                     {summary['total_cases']}")
    print(f"  Passing cases:                   {summary['passing_count']}")
    print(f"  Pass rate:                       {summary['pass_rate']}")
    print(f"  Persistent memory pass rate:     {summary['persistent_memory_pass_rate']}")
    print(f"  Query rewrite applied rate:      {summary['query_rewrite_applied_rate']}")
    print(f"  Retrieval query resolution rate: {summary['retrieval_query_resolution_rate']}")
    print(f"  Source hit rate:                 {summary['source_hit_rate']}")
    print(f"  Avg keyword hit rate:            {summary['avg_keyword_hit_rate']}")
    print(f"  PRD Status:                      {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
