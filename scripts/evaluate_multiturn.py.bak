import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.core.session_memory import InMemorySessionMemory
from app.rag.generator import create_generator
from app.rag.pii import redact_pii
from app.rag.retriever_factory import create_retriever
from app.rag.safety import check_safety


OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
TODAY = time.strftime("%Y-%m-%d")
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_multiturn_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_multiturn_eval.md"


MULTITURN_CASES = [
    {
        "case_id": "mt_audit_log_retention",
        "category": "compliance",
        "session_id": "eval-multiturn-audit-001",
        "turns": [
            "What are the audit logging requirements?",
            "How long should they be retained?",
        ],
        "expected_keywords": [
            "audit logs",
            "privileged operations",
            "one year",
        ],
        "expected_source": "03_compliance_guide_en.txt",
    },
    {
        "case_id": "mt_api_key_incident_report",
        "category": "security_cn",
        "session_id": "eval-multiturn-apikey-001",
        "turns": [
            "API Key 泄露后应该怎么处理？",
            "多久内要报告？",
        ],
        "expected_keywords": [
            "24 小时",
            "Security Operations",
            "报告",
        ],
        "expected_source": "04_data_security_policy_cn.txt",
    },
    {
        "case_id": "mt_annual_leave_approval",
        "category": "hr_policy",
        "session_id": "eval-multiturn-leave-001",
        "turns": [
            "What is the annual leave policy?",
            "How long does the manager have to review it?",
        ],
        "expected_keywords": [
            "three working days",
            "Managers",
            "leave requests",
        ],
        "expected_source": "01_employee_handbook_en.txt",
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


def run_single_turn(
    question: str,
    session_id: str,
    memory: InMemorySessionMemory,
    retriever,
    generator,
) -> Dict[str, Any]:
    start_time = time.time()

    redacted_question = redact_pii(question)
    safety_result = check_safety(redacted_question)

    if not safety_result["safe"]:
        return {
            "question": question,
            "answer": safety_result["message"],
            "refused": True,
            "refusal_reason": safety_result["reason"],
            "sources": [],
            "retrieved_sources": [],
            "latency_ms": int((time.time() - start_time) * 1000),
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "model_name": None,
            "generator_type": None,
            "history_turns_used": len(memory.get_history(session_id)),
        }

    retrieved_chunks = retriever.retrieve(redacted_question)
    conversation_history = memory.get_history(session_id)

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
        "latency_ms": int((time.time() - start_time) * 1000),
        "input_tokens": generation_result.get("input_tokens"),
        "output_tokens": generation_result.get("output_tokens"),
        "total_tokens": generation_result.get("total_tokens"),
        "model_name": generation_result.get("model_name"),
        "generator_type": generation_result.get("generator_type"),
        "history_turns_used": len(conversation_history),
    }


def evaluate_case(
    case: Dict[str, Any],
    retriever,
    generator,
) -> Dict[str, Any]:
    memory = InMemorySessionMemory(max_turns=3)

    session_id = case["session_id"]
    turns = case["turns"]

    first_result = run_single_turn(
        question=turns[0],
        session_id=session_id,
        memory=memory,
        retriever=retriever,
        generator=generator,
    )

    second_result = run_single_turn(
        question=turns[1],
        session_id=session_id,
        memory=memory,
        retriever=retriever,
        generator=generator,
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

    pass_result = all(
        [
            history_used,
            not second_result["refused"],
            keyword_result["keyword_hit_rate"] >= 0.5,
            second_source_hit,
        ]
    )

    return {
        "case_id": case["case_id"],
        "category": case.get("category", ""),
        "session_id": session_id,
        "turn_1_question": turns[0],
        "turn_2_question": turns[1],
        "turn_1_refused": first_result["refused"],
        "turn_2_refused": second_result["refused"],
        "turn_2_refusal_reason": second_result["refusal_reason"],
        "history_turns_used": second_result["history_turns_used"],
        "history_used": history_used,
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
    history_used_count = sum(1 for item in results if item["history_used"])
    source_hit_count = sum(1 for item in results if item["source_hit"])

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
        "history_used_count": history_used_count,
        "history_used_rate": round(history_used_count / total, 4) if total else 0,
        "source_hit_count": source_hit_count,
        "source_hit_rate": round(source_hit_count / total, 4) if total else 0,
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
        "history_turns_used",
        "history_used",
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
        "history_used_count",
        "history_used_rate",
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
        "# Multi-turn Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: Multi-turn QA Evaluation",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passing cases: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
        f"- History used rate: {summary['history_used_rate']}",
        f"- Source hit rate: {summary['source_hit_rate']}",
        f"- Avg keyword hit rate: {summary['avg_keyword_hit_rate']}",
        f"- PRD pass: {summary['prd_pass']}",
        "",
        "## Method",
        "",
        "Each case contains two turns with the same session_id.",
        "The second turn is a follow-up question.",
        "The evaluator checks whether conversation history was used,",
        "whether the answer was not refused, whether expected source was hit,",
        "and whether expected keywords appeared in the second-turn answer.",
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
                f"- History turns used: {result['history_turns_used']}",
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

    print(f"Total multi-turn eval cases: {len(MULTITURN_CASES)}")
    print()

    results = []

    for index, case in enumerate(MULTITURN_CASES, start=1):
        print(f"[{index}/{len(MULTITURN_CASES)}] {case['case_id']}")

        result = evaluate_case(
            case=case,
            retriever=retriever,
            generator=generator,
        )
        results.append(result)

        status = "✅" if result["pass"] else "❌"
        print(
            f"  {status} pass={result['pass']}, "
            f"history_used={result['history_used']}, "
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
    print("MULTI-TURN EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:          {summary['total_cases']}")
    print(f"  Passing cases:        {summary['passing_count']}")
    print(f"  Pass rate:            {summary['pass_rate']}")
    print(f"  History used rate:    {summary['history_used_rate']}")
    print(f"  Source hit rate:      {summary['source_hit_rate']}")
    print(f"  Avg keyword hit rate: {summary['avg_keyword_hit_rate']}")
    print(f"  PRD Status:           {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
