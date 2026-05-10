import csv
import json
import sys
import re
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


EVAL_SET_PATH = PROJECT_ROOT / "eval" / "faithfulness_eval_set.jsonl"
CSV_REPORT_PATH = PROJECT_ROOT / "reports" / "evaluations" / "2026-05-10_faithfulness_baseline.csv"
MD_REPORT_PATH = PROJECT_ROOT / "reports" / "evaluations" / "2026-05-10_faithfulness_baseline.md"


def load_eval_set(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Faithfulness evaluation set not found: {path}")

    records = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    return records


def normalize_text(value: str) -> str:
    value = value.lower()

    # Remove common Markdown formatting.
    value = value.replace("`", "")
    value = value.replace("*", "")
    value = value.replace("_", " ")

    # Normalize spaces.
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def contains_text(text: str, phrase: str) -> bool:
    normalized_text = normalize_text(text)
    normalized_phrase = normalize_text(phrase)

    return normalized_phrase in normalized_text


def run_pipeline(
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
            "sources": [],
            "retrieved_sources": [],
            "retrieved_context": "",
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "model_name": config.get("llm", {}).get("model"),
            "generator_type": config.get("generator", {}).get("type"),
            "retrieval_latency_ms": 0,
            "generation_latency_ms": 0,
            "total_latency_ms": total_latency_ms,
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

    context_chunks_used = generation_result.get("context_chunks_used")

    if isinstance(context_chunks_used, int) and context_chunks_used > 0:
        context_chunks = retrieved_chunks[:context_chunks_used]
    else:
        context_chunks = retrieved_chunks

    retrieved_context = "\n\n".join(
        [chunk.get("text", "") for chunk in context_chunks]
    )

    return {
        "answer": answer,
        "refused": generation_result["refused"],
        "refusal_reason": generation_result["refusal_reason"],
        "sources": generation_result["sources"],
        "retrieved_sources": [
            chunk.get("metadata", {}).get("filename") for chunk in retrieved_chunks
        ],
        "retrieved_context": retrieved_context,
        "input_tokens": generation_result.get("input_tokens"),
        "output_tokens": generation_result.get("output_tokens"),
        "total_tokens": generation_result.get("total_tokens"),
        "model_name": generation_result.get("model_name"),
        "generator_type": generation_result.get("generator_type"),
        "context_chunks_used": context_chunks_used,
        "retrieval_latency_ms": retrieval_latency_ms,
        "generation_latency_ms": generation_latency_ms,
        "total_latency_ms": total_latency_ms,
    }


def evaluate_supported_claims(
    answer: str,
    retrieved_context: str,
    expected_supported_claims: List[str],
) -> Dict[str, Any]:
    matched_in_answer = []
    missing_from_answer = []
    supported_by_context = []
    missing_from_context = []

    for claim in expected_supported_claims:
        if contains_text(answer, claim):
            matched_in_answer.append(claim)
        else:
            missing_from_answer.append(claim)

        if contains_text(retrieved_context, claim):
            supported_by_context.append(claim)
        else:
            missing_from_context.append(claim)

    total = len(expected_supported_claims)

    answer_coverage_rate = len(matched_in_answer) / total if total else 1.0
    context_support_rate = len(supported_by_context) / total if total else 1.0

    return {
        "expected_claims_total": total,
        "claims_matched_in_answer": len(matched_in_answer),
        "answer_claim_coverage_rate": round(answer_coverage_rate, 4),
        "claims_supported_by_context": len(supported_by_context),
        "context_claim_support_rate": round(context_support_rate, 4),
        "missing_claims_from_answer": "|".join(missing_from_answer),
        "missing_claims_from_context": "|".join(missing_from_context),
    }


def evaluate_forbidden_claims(
    answer: str,
    forbidden_unsupported_claims: List[str],
) -> Dict[str, Any]:
    found = []

    for claim in forbidden_unsupported_claims:
        if contains_text(answer, claim):
            found.append(claim)

    return {
        "unsupported_claims_found": "|".join(found),
        "unsupported_claims_clean": len(found) == 0,
    }


def evaluate_record(
    record: Dict[str, Any],
    pipeline_result: Dict[str, Any],
) -> Dict[str, Any]:
    question = record["question"]
    category = record.get("category", "")
    expected_source = record.get("expected_source")
    expected_refused = record.get("expected_refused", False)
    expected_refusal_reason = record.get("expected_refusal_reason")
    expected_supported_claims = record.get("expected_supported_claims", [])
    forbidden_unsupported_claims = record.get("forbidden_unsupported_claims", [])

    answer = pipeline_result.get("answer") or ""
    retrieved_context = pipeline_result.get("retrieved_context") or ""
    refused = pipeline_result.get("refused")
    refusal_reason = pipeline_result.get("refusal_reason")
    retrieved_sources = pipeline_result.get("retrieved_sources", [])

    answer_not_empty = bool(answer.strip())

    expected_refusal_match = refused == expected_refused

    if expected_refusal_reason:
        refusal_reason_match = refusal_reason == expected_refusal_reason
    else:
        refusal_reason_match = refusal_reason in [None, ""]

    source_hit = True
    if expected_source:
        source_hit = expected_source in retrieved_sources

    supported_result = evaluate_supported_claims(
        answer=answer,
        retrieved_context=retrieved_context,
        expected_supported_claims=expected_supported_claims,
    )

    forbidden_result = evaluate_forbidden_claims(
        answer=answer,
        forbidden_unsupported_claims=forbidden_unsupported_claims,
    )

    answer_claim_coverage_pass = (
        supported_result["answer_claim_coverage_rate"] >= 0.5
    )

    context_claim_support_pass = (
        supported_result["context_claim_support_rate"] >= 0.5
    )

    if expected_refused:
        faithfulness_pass = all(
            [
                answer_not_empty,
                expected_refusal_match,
                refusal_reason_match,
                forbidden_result["unsupported_claims_clean"],
            ]
        )
    else:
        faithfulness_pass = all(
            [
                answer_not_empty,
                expected_refusal_match,
                refusal_reason_match,
                source_hit,
                answer_claim_coverage_pass,
                context_claim_support_pass,
                forbidden_result["unsupported_claims_clean"],
            ]
        )

    return {
        "question": question,
        "category": category,
        "expected_source": expected_source,
        "expected_refused": expected_refused,
        "actual_refused": refused,
        "expected_refusal_reason": expected_refusal_reason,
        "actual_refusal_reason": refusal_reason,
        "answer_not_empty": answer_not_empty,
        "expected_refusal_match": expected_refusal_match,
        "refusal_reason_match": refusal_reason_match,
        "source_hit": source_hit,
        "expected_claims_total": supported_result["expected_claims_total"],
        "claims_matched_in_answer": supported_result["claims_matched_in_answer"],
        "answer_claim_coverage_rate": supported_result["answer_claim_coverage_rate"],
        "claims_supported_by_context": supported_result["claims_supported_by_context"],
        "context_claim_support_rate": supported_result["context_claim_support_rate"],
        "missing_claims_from_answer": supported_result["missing_claims_from_answer"],
        "missing_claims_from_context": supported_result["missing_claims_from_context"],
        "unsupported_claims_found": forbidden_result["unsupported_claims_found"],
        "unsupported_claims_clean": forbidden_result["unsupported_claims_clean"],
        "faithfulness_pass": faithfulness_pass,
        "retrieved_sources": "|".join([src or "" for src in retrieved_sources]),
        "input_tokens": pipeline_result.get("input_tokens"),
        "output_tokens": pipeline_result.get("output_tokens"),
        "total_tokens": pipeline_result.get("total_tokens"),
        "model_name": pipeline_result.get("model_name"),
        "generator_type": pipeline_result.get("generator_type"),
        "context_chunks_used": pipeline_result.get("context_chunks_used"),
        "retrieval_latency_ms": pipeline_result.get("retrieval_latency_ms"),
        "generation_latency_ms": pipeline_result.get("generation_latency_ms"),
        "total_latency_ms": pipeline_result.get("total_latency_ms"),
        "answer_preview": answer[:300].replace("\n", " "),
    }


def summarize(details: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(details)

    if total == 0:
        return {
            "total_questions": 0,
            "faithfulness_pass_rate": 0,
            "answer_not_empty_rate": 0,
            "expected_refusal_match_rate": 0,
            "source_hit_rate": 0,
            "unsupported_claims_clean_rate": 0,
            "avg_answer_claim_coverage_rate": 0,
            "avg_context_claim_support_rate": 0,
            "avg_total_latency_ms": 0,
            "avg_total_tokens": "N/A",
        }

    def true_rate(field: str) -> float:
        return round(
            sum(1 for item in details if item.get(field) is True) / total,
            4,
        )

    answer_coverage_rates = [
        item["answer_claim_coverage_rate"]
        for item in details
        if isinstance(item.get("answer_claim_coverage_rate"), (int, float))
    ]

    context_support_rates = [
        item["context_claim_support_rate"]
        for item in details
        if isinstance(item.get("context_claim_support_rate"), (int, float))
    ]

    latencies = [
        item["total_latency_ms"]
        for item in details
        if isinstance(item.get("total_latency_ms"), (int, float))
    ]

    total_tokens = [
        item["total_tokens"]
        for item in details
        if isinstance(item.get("total_tokens"), (int, float))
    ]

    return {
        "total_questions": total,
        "faithfulness_pass_rate": true_rate("faithfulness_pass"),
        "answer_not_empty_rate": true_rate("answer_not_empty"),
        "expected_refusal_match_rate": true_rate("expected_refusal_match"),
        "source_hit_rate": true_rate("source_hit"),
        "unsupported_claims_clean_rate": true_rate("unsupported_claims_clean"),
        "avg_answer_claim_coverage_rate": round(
            sum(answer_coverage_rates) / len(answer_coverage_rates),
            4,
        )
        if answer_coverage_rates
        else 0,
        "avg_context_claim_support_rate": round(
            sum(context_support_rates) / len(context_support_rates),
            4,
        )
        if context_support_rates
        else 0,
        "avg_total_latency_ms": round(sum(latencies) / len(latencies), 2)
        if latencies
        else 0,
        "avg_total_tokens": round(sum(total_tokens) / len(total_tokens), 2)
        if total_tokens
        else "N/A",
    }


def write_csv_report(
    details: List[Dict[str, Any]],
    summary: Dict[str, Any],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "question",
        "category",
        "expected_source",
        "expected_refused",
        "actual_refused",
        "expected_refusal_reason",
        "actual_refusal_reason",
        "answer_not_empty",
        "expected_refusal_match",
        "refusal_reason_match",
        "source_hit",
        "expected_claims_total",
        "claims_matched_in_answer",
        "answer_claim_coverage_rate",
        "claims_supported_by_context",
        "context_claim_support_rate",
        "missing_claims_from_answer",
        "missing_claims_from_context",
        "unsupported_claims_found",
        "unsupported_claims_clean",
        "faithfulness_pass",
        "retrieved_sources",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "model_name",
        "generator_type",
        "context_chunks_used",
        "retrieval_latency_ms",
        "generation_latency_ms",
        "total_latency_ms",
        "answer_preview",
        "total_questions",
        "faithfulness_pass_rate",
        "answer_not_empty_rate",
        "expected_refusal_match_rate",
        "source_hit_rate",
        "unsupported_claims_clean_rate",
        "avg_answer_claim_coverage_rate",
        "avg_context_claim_support_rate",
        "avg_total_latency_ms",
        "avg_total_tokens",
    ]

    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        summary_row = {field: "" for field in fieldnames}
        summary_row.update(
            {
                "row_type": "summary",
                "total_questions": summary["total_questions"],
                "faithfulness_pass_rate": summary["faithfulness_pass_rate"],
                "answer_not_empty_rate": summary["answer_not_empty_rate"],
                "expected_refusal_match_rate": summary["expected_refusal_match_rate"],
                "source_hit_rate": summary["source_hit_rate"],
                "unsupported_claims_clean_rate": summary["unsupported_claims_clean_rate"],
                "avg_answer_claim_coverage_rate": summary["avg_answer_claim_coverage_rate"],
                "avg_context_claim_support_rate": summary["avg_context_claim_support_rate"],
                "avg_total_latency_ms": summary["avg_total_latency_ms"],
                "avg_total_tokens": summary["avg_total_tokens"],
            }
        )
        writer.writerow(summary_row)

        for detail in details:
            row = {field: "" for field in fieldnames}
            row.update(detail)
            row["row_type"] = "detail"
            writer.writerow(row)


def write_markdown_report(summary: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# Faithfulness Evaluation Report: Baseline

Date: 2026-05-10  
Project: AIA RAG Case Study Service  
Evaluation Type: Faithfulness Evaluation  
Version: v1  
Supporting CSV: reports/evaluations/2026-05-10_faithfulness_baseline.csv

---

## 1. Objective

This evaluation checks whether generated answers are supported by retrieved context.

The goal is to detect whether the LLM answer:

- covers expected supported claims
- avoids known unsupported claims
- uses retrieved context rather than external knowledge
- handles out-of-scope questions as refusals

---

## 2. Evaluation Dataset

Evaluation set:

    eval/faithfulness_eval_set.jsonl

Total questions:

    {summary["total_questions"]}

The dataset covers:

- compliance
- data security
- technical specification
- HR policy
- architecture
- out-of-scope refusal

---

## 3. Metrics

Metrics:

- faithfulness_pass_rate
- answer_not_empty_rate
- expected_refusal_match_rate
- source_hit_rate
- unsupported_claims_clean_rate
- avg_answer_claim_coverage_rate
- avg_context_claim_support_rate
- avg_total_latency_ms
- avg_total_tokens

This is a rule-based baseline faithfulness evaluation.

---

## 4. Summary Results

| Metric | Value |
|---|---:|
| Total Questions | {summary["total_questions"]} |
| Faithfulness Pass Rate | {summary["faithfulness_pass_rate"]} |
| Answer Not Empty Rate | {summary["answer_not_empty_rate"]} |
| Expected Refusal Match Rate | {summary["expected_refusal_match_rate"]} |
| Source Hit Rate | {summary["source_hit_rate"]} |
| Unsupported Claims Clean Rate | {summary["unsupported_claims_clean_rate"]} |
| Avg Answer Claim Coverage Rate | {summary["avg_answer_claim_coverage_rate"]} |
| Avg Context Claim Support Rate | {summary["avg_context_claim_support_rate"]} |
| Avg Total Latency ms | {summary["avg_total_latency_ms"]} |
| Avg Total Tokens | {summary["avg_total_tokens"]} |

---

## 5. Interpretation

This baseline checks whether expected claims appear in the answer and whether those claims are supported by the selected context chunks.

A high faithfulness pass rate means the answer is likely grounded in the retrieved context under the current rule-based criteria.

---

## 6. Limitations

Current limitations:

1. This is rule-based, not semantic.
2. Claim matching is based on text containment.
3. Correct paraphrases may be missed.
4. Some unsupported claims may not be detected unless they are listed.
5. Future work should add LLM-as-judge faithfulness evaluation.

---

## 7. Next Steps

Recommended next steps:

1. Review failed cases in the CSV.
2. Improve prompts or context assembly if unsupported claims appear.
3. Expand the faithfulness evaluation set.
4. Add semantic or LLM-as-judge faithfulness scoring.
"""

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def main():
    config = load_config()
    eval_set = load_eval_set(EVAL_SET_PATH)

    retriever = create_retriever(config)
    generator = create_generator(config)

    details = []

    for index, record in enumerate(eval_set, start=1):
        print(f"Evaluating faithfulness {index}/{len(eval_set)}: {record['question']}")

        pipeline_result = run_pipeline(
            question=record["question"],
            config=config,
            retriever=retriever,
            generator=generator,
        )

        detail = evaluate_record(record, pipeline_result)
        details.append(detail)

        print(
            f"  pass={detail['faithfulness_pass']}, "
            f"refused={detail['actual_refused']}, "
            f"answer_claim_coverage={detail['answer_claim_coverage_rate']}, "
            f"context_support={detail['context_claim_support_rate']}"
        )

    summary = summarize(details)

    write_csv_report(details, summary, CSV_REPORT_PATH)
    write_markdown_report(summary, MD_REPORT_PATH)

    print()
    print("Faithfulness evaluation completed.")
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")
    print()
    print("Summary:")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()