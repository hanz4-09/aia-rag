import csv
import json
import re
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
CSV_REPORT_PATH = PROJECT_ROOT / "reports" / "evaluations" / "2026-05-11_answer_compliance_eval.csv"
MD_REPORT_PATH = PROJECT_ROOT / "reports" / "evaluations" / "2026-05-11_answer_compliance_eval.md"


def load_eval_set(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Answer evaluation set not found: {path}")

    records = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    return records


def normalize_text(value: str) -> str:
    """
    Normalize text for rule-based keyword matching.

    This helps cases such as:
    - GET `/health` matching /health
    - Markdown bold/code formatting
    - repeated whitespace
    """
    if not value:
        return ""

    value = value.lower()

    # Remove common Markdown formatting.
    value = value.replace("`", "")
    value = value.replace("*", "")
    value = value.replace("_", " ")

    # Normalize punctuation spacing lightly.
    value = value.replace("：", ":")
    value = value.replace("，", ",")
    value = value.replace("。", ".")

    # Normalize whitespace.
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def contains_expected_keyword(text: str, keyword: str) -> bool:
    """
    Check whether an expected keyword appears in the answer.

    This is intentionally simple, but more robust than raw substring matching.
    """
    normalized_text = normalize_text(text)
    normalized_keyword = normalize_text(keyword)

    return normalized_keyword in normalized_text


def is_negated_forbidden_keyword(answer: str, keyword: str) -> bool:
    """
    Detect simple negated contexts for forbidden keywords.

    This prevents false failures such as:
    - 不可以 matching forbidden keyword 可以
    - 不得将其写入源代码 matching forbidden keyword 写入源代码
    - must not write to source code matching forbidden phrase write to source code
    """
    normalized_answer = normalize_text(answer)
    normalized_keyword = normalize_text(keyword)

    if not normalized_keyword:
        return False

    start = 0

    while True:
        index = normalized_answer.find(normalized_keyword, start)
        if index == -1:
            break

        prefix_window = normalized_answer[max(0, index - 12): index]
        suffix_window = normalized_answer[index: index + len(normalized_keyword) + 12]

        chinese_negation_markers = [
            "不",
            "不得",
            "不能",
            "不应",
            "不应该",
            "禁止",
            "严禁",
            "不可",
            "不允许",
            "避免",
            "不得将其",
            "不能将其",
            "不应将其",
            "不应该将其",
        ]

        if any(marker in prefix_window for marker in chinese_negation_markers):
            return True

        # Special case: forbidden keyword is "可以", but answer says "不可以".
        if normalized_keyword == "可以" and "不可以" in suffix_window:
            return True

        english_negation_markers = [
            "not",
            "must not",
            "should not",
            "cannot",
            "can't",
            "do not",
            "does not",
            "never",
            "forbidden",
            "prohibited",
            "not allowed",
        ]

        if any(marker in prefix_window for marker in english_negation_markers):
            return True

        start = index + len(normalized_keyword)

    return False


def contains_forbidden_keyword(answer: str, keyword: str) -> bool:
    """
    Return True only when a forbidden keyword appears in a non-negated context.
    """
    normalized_answer = normalize_text(answer)
    normalized_keyword = normalize_text(keyword)

    if normalized_keyword not in normalized_answer:
        return False

    if is_negated_forbidden_keyword(answer, keyword):
        return False

    return True


def evaluate_keywords(answer: str, expected_keywords: List[str]) -> Dict[str, Any]:
    if not expected_keywords:
        return {
            "expected_keywords_total": 0,
            "expected_keywords_matched": 0,
            "expected_keywords_hit_rate": 1.0,
            "missing_expected_keywords": "",
        }

    matched = []
    missing = []

    for keyword in expected_keywords:
        if contains_expected_keyword(answer, keyword):
            matched.append(keyword)
        else:
            missing.append(keyword)

    hit_rate = len(matched) / len(expected_keywords)

    return {
        "expected_keywords_total": len(expected_keywords),
        "expected_keywords_matched": len(matched),
        "expected_keywords_hit_rate": round(hit_rate, 4),
        "missing_expected_keywords": "|".join(missing),
    }


def evaluate_forbidden_keywords(answer: str, forbidden_keywords: List[str]) -> Dict[str, Any]:
    found = []

    for keyword in forbidden_keywords:
        if contains_forbidden_keyword(answer, keyword):
            found.append(keyword)

    return {
        "forbidden_keywords_found": "|".join(found),
        "forbidden_keywords_clean": len(found) == 0,
    }


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
            "sources": [],
            "retrieved_sources": [],
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

    return {
        "answer": answer,
        "refused": generation_result["refused"],
        "refusal_reason": generation_result["refusal_reason"],
        "sources": generation_result["sources"],
        "retrieved_sources": [
            chunk.get("metadata", {}).get("filename") for chunk in retrieved_chunks
        ],
        "input_tokens": generation_result.get("input_tokens"),
        "output_tokens": generation_result.get("output_tokens"),
        "total_tokens": generation_result.get("total_tokens"),
        "model_name": generation_result.get("model_name"),
        "generator_type": generation_result.get("generator_type"),
        "retrieval_latency_ms": retrieval_latency_ms,
        "generation_latency_ms": generation_latency_ms,
        "total_latency_ms": total_latency_ms,
    }


def evaluate_record(
    record: Dict[str, Any],
    pipeline_result: Dict[str, Any],
) -> Dict[str, Any]:
    question = record["question"]
    category = record.get("category", "")
    expected_refused = record.get("expected_refused", False)
    expected_refusal_reason = record.get("expected_refusal_reason")
    expected_source = record.get("expected_source")
    expected_keywords = record.get("expected_keywords", [])
    forbidden_keywords = record.get("forbidden_keywords", [])

    answer = pipeline_result["answer"] or ""
    refused = pipeline_result["refused"]
    refusal_reason = pipeline_result["refusal_reason"]
    sources = pipeline_result.get("sources", [])
    retrieved_sources = pipeline_result.get("retrieved_sources", [])

    answer_not_empty = bool(answer.strip())
    expected_refusal_match = refused == expected_refused

    if expected_refusal_reason:
        refusal_reason_match = refusal_reason == expected_refusal_reason
    else:
        refusal_reason_match = refusal_reason in [None, ""]

    has_sources = True
    if not expected_refused:
        has_sources = len(sources) > 0

    source_hit = True
    if expected_source:
        source_filenames = [
            source.get("filename") for source in sources
        ]
        source_hit = expected_source in source_filenames or expected_source in retrieved_sources

    keyword_result = evaluate_keywords(answer, expected_keywords)
    forbidden_result = evaluate_forbidden_keywords(answer, forbidden_keywords)

    expected_keywords_pass = keyword_result["expected_keywords_hit_rate"] >= 0.5

    rule_based_pass = all(
        [
            answer_not_empty,
            expected_refusal_match,
            refusal_reason_match,
            has_sources,
            source_hit,
            expected_keywords_pass,
            forbidden_result["forbidden_keywords_clean"],
        ]
    )

    return {
        "question": question,
        "category": category,
        "expected_refused": expected_refused,
        "actual_refused": refused,
        "expected_refusal_reason": expected_refusal_reason,
        "actual_refusal_reason": refusal_reason,
        "answer_not_empty": answer_not_empty,
        "expected_refusal_match": expected_refusal_match,
        "refusal_reason_match": refusal_reason_match,
        "has_sources": has_sources,
        "expected_source": expected_source,
        "source_hit": source_hit,
        "retrieved_sources": "|".join([src or "" for src in retrieved_sources]),
        "expected_keywords_total": keyword_result["expected_keywords_total"],
        "expected_keywords_matched": keyword_result["expected_keywords_matched"],
        "expected_keywords_hit_rate": keyword_result["expected_keywords_hit_rate"],
        "missing_expected_keywords": keyword_result["missing_expected_keywords"],
        "forbidden_keywords_found": forbidden_result["forbidden_keywords_found"],
        "forbidden_keywords_clean": forbidden_result["forbidden_keywords_clean"],
        "rule_based_pass": rule_based_pass,
        "input_tokens": pipeline_result.get("input_tokens"),
        "output_tokens": pipeline_result.get("output_tokens"),
        "total_tokens": pipeline_result.get("total_tokens"),
        "model_name": pipeline_result.get("model_name"),
        "generator_type": pipeline_result.get("generator_type"),
        "retrieval_latency_ms": pipeline_result.get("retrieval_latency_ms"),
        "generation_latency_ms": pipeline_result.get("generation_latency_ms"),
        "total_latency_ms": pipeline_result.get("total_latency_ms"),
        "answer_preview": answer[:300].replace("\n", " "),
    }


def summarize_results(details: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(details)

    if total == 0:
        return {
            "total_questions": 0,
            "answer_compliance_rate": 0,
            "rule_based_pass_rate": 0,
            "answer_not_empty_rate": 0,
            "expected_refusal_match_rate": 0,
            "refusal_reason_match_rate": 0,
            "source_hit_rate": 0,
            "forbidden_keywords_clean_rate": 0,
            "avg_expected_keywords_hit_rate": 0,
            "avg_total_latency_ms": 0,
            "avg_generation_latency_ms": 0,
            "avg_total_tokens": "N/A",
        }

    def rate(field: str) -> float:
        return round(
            sum(1 for item in details if item.get(field) is True) / total,
            4,
        )

    keyword_rates = [
        item.get("expected_keywords_hit_rate", 0)
        for item in details
        if isinstance(item.get("expected_keywords_hit_rate"), (int, float))
    ]

    total_latencies = [
        item.get("total_latency_ms")
        for item in details
        if isinstance(item.get("total_latency_ms"), (int, float))
    ]

    generation_latencies = [
        item.get("generation_latency_ms")
        for item in details
        if isinstance(item.get("generation_latency_ms"), (int, float))
    ]

    total_tokens = [
        item.get("total_tokens")
        for item in details
        if isinstance(item.get("total_tokens"), (int, float))
    ]

    rule_based_pass_rate = rate("rule_based_pass")

    return {
        "total_questions": total,
        "answer_compliance_rate": rule_based_pass_rate,
        "rule_based_pass_rate": rule_based_pass_rate,
        "answer_not_empty_rate": rate("answer_not_empty"),
        "expected_refusal_match_rate": rate("expected_refusal_match"),
        "refusal_reason_match_rate": rate("refusal_reason_match"),
        "source_hit_rate": rate("source_hit"),
        "forbidden_keywords_clean_rate": rate("forbidden_keywords_clean"),
        "avg_expected_keywords_hit_rate": round(sum(keyword_rates) / len(keyword_rates), 4)
        if keyword_rates
        else 0,
        "avg_total_latency_ms": round(sum(total_latencies) / len(total_latencies), 2)
        if total_latencies
        else 0,
        "avg_generation_latency_ms": round(
            sum(generation_latencies) / len(generation_latencies),
            2,
        )
        if generation_latencies
        else 0,
        "avg_total_tokens": round(sum(total_tokens) / len(total_tokens), 2)
        if total_tokens
        else "N/A",
    }


def write_csv_report(details: List[Dict[str, Any]], summary: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "question",
        "category",
        "expected_refused",
        "actual_refused",
        "expected_refusal_reason",
        "actual_refusal_reason",
        "answer_not_empty",
        "expected_refusal_match",
        "refusal_reason_match",
        "has_sources",
        "expected_source",
        "source_hit",
        "retrieved_sources",
        "expected_keywords_total",
        "expected_keywords_matched",
        "expected_keywords_hit_rate",
        "missing_expected_keywords",
        "forbidden_keywords_found",
        "forbidden_keywords_clean",
        "rule_based_pass",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "model_name",
        "generator_type",
        "retrieval_latency_ms",
        "generation_latency_ms",
        "total_latency_ms",
        "answer_preview",
        "total_questions",
        "answer_compliance_rate",
        "rule_based_pass_rate",
        "answer_not_empty_rate",
        "expected_refusal_match_rate",
        "refusal_reason_match_rate",
        "source_hit_rate",
        "forbidden_keywords_clean_rate",
        "avg_expected_keywords_hit_rate",
        "avg_total_latency_ms",
        "avg_generation_latency_ms",
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
                "answer_compliance_rate": summary["answer_compliance_rate"],
                "rule_based_pass_rate": summary["rule_based_pass_rate"],
                "answer_not_empty_rate": summary["answer_not_empty_rate"],
                "expected_refusal_match_rate": summary["expected_refusal_match_rate"],
                "refusal_reason_match_rate": summary["refusal_reason_match_rate"],
                "source_hit_rate": summary["source_hit_rate"],
                "forbidden_keywords_clean_rate": summary["forbidden_keywords_clean_rate"],
                "avg_expected_keywords_hit_rate": summary["avg_expected_keywords_hit_rate"],
                "avg_total_latency_ms": summary["avg_total_latency_ms"],
                "avg_generation_latency_ms": summary["avg_generation_latency_ms"],
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

    content = f"""# Answer Compliance Evaluation Report

Date: 2026-05-11  
Project: AIA RAG Case Study Service  
Evaluation Type: Answer Compliance Evaluation  
Version: v1  
Supporting CSV: reports/evaluations/2026-05-11_answer_compliance_eval.csv

---

## 1. Objective

This evaluation validates whether the generated answers comply with the expected answer behavior defined in the evaluation set.

The goal is to verify that the system can:

- Generate non-empty answers
- Respect expected refusal behavior
- Return the expected refusal reason when applicable
- Return sources for answerable questions
- Retrieve the expected source
- Include expected answer keywords
- Avoid forbidden answer keywords
- Record token usage and latency

---

## 2. Evaluation Dataset

Evaluation set:

    eval/answer_eval_set.jsonl

The dataset covers:

- Compliance questions
- Data security questions
- Technical specification questions
- HR policy questions
- Architecture questions
- Safety refusal
- Out-of-scope refusal

Total questions:

    {summary["total_questions"]}

---

## 3. Metrics

Main PRD metric:

    answer_compliance_rate = rule_based_pass_rate

A record passes when all of the following checks pass:

- answer_not_empty
- expected_refusal_match
- refusal_reason_match
- has_sources
- source_hit
- expected_keywords_hit_rate >= 0.5
- forbidden_keywords_clean

Supporting metrics:

- answer_not_empty_rate
- expected_refusal_match_rate
- refusal_reason_match_rate
- source_hit_rate
- forbidden_keywords_clean_rate
- avg_expected_keywords_hit_rate
- avg_total_latency_ms
- avg_generation_latency_ms
- avg_total_tokens

This is a rule-based compliance evaluation, not an LLM-as-judge evaluation.

---

## 4. Summary Results

| Metric | Value |
|---|---:|
| Total Questions | {summary["total_questions"]} |
| Answer Compliance Rate | {summary["answer_compliance_rate"]} |
| Rule-based Pass Rate | {summary["rule_based_pass_rate"]} |
| Answer Not Empty Rate | {summary["answer_not_empty_rate"]} |
| Expected Refusal Match Rate | {summary["expected_refusal_match_rate"]} |
| Refusal Reason Match Rate | {summary["refusal_reason_match_rate"]} |
| Source Hit Rate | {summary["source_hit_rate"]} |
| Forbidden Keywords Clean Rate | {summary["forbidden_keywords_clean_rate"]} |
| Avg Expected Keywords Hit Rate | {summary["avg_expected_keywords_hit_rate"]} |
| Avg Total Latency ms | {summary["avg_total_latency_ms"]} |
| Avg Generation Latency ms | {summary["avg_generation_latency_ms"]} |
| Avg Total Tokens | {summary["avg_total_tokens"]} |

---

## 5. PRD Status

PRD target:

    Answer Compliance >= 0.80

Advanced target:

    Answer Compliance >= 0.90

Current result:

    Answer Compliance Rate = {summary["answer_compliance_rate"]}

Status:

    {"PASS" if summary["answer_compliance_rate"] >= 0.8 else "FAIL"}

---

## 6. Interpretation

This report formalizes the answer-level rule-based evaluation as Answer Compliance Evaluation.

It checks whether the final answer follows expected behavior, including refusal correctness, source coverage, expected keyword coverage, and forbidden keyword avoidance.

---

## 7. Limitations

Current limitations:

1. This is not a semantic faithfulness evaluation.
2. This does not replace LLM-as-Judge faithfulness evaluation.
3. Keyword matching may still miss some paraphrases.
4. Some correct answers may fail if they use different wording.
5. Some incorrect answers may pass if they contain expected keywords.
6. Forbidden keyword matching only supports simple negation handling.

---

## 8. Next Steps

Recommended next steps:

1. Review any failed cases in the CSV.
2. Expand the evaluation set if needed.
3. Add style consistency evaluation.
4. Integrate answer_compliance_rate into the operations report.
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
        print(f"Evaluating answer {index}/{len(eval_set)}: {record['question']}")

        pipeline_result = run_answer_pipeline(
            question=record["question"],
            config=config,
            retriever=retriever,
            generator=generator,
        )

        detail = evaluate_record(record, pipeline_result)
        details.append(detail)

        print(
            f"  pass={detail['rule_based_pass']}, "
            f"refused={detail['actual_refused']}, "
            f"keyword_hit_rate={detail['expected_keywords_hit_rate']}, "
            f"latency_ms={detail['total_latency_ms']}"
        )

    summary = summarize_results(details)

    write_csv_report(details, summary, CSV_REPORT_PATH)
    write_markdown_report(summary, MD_REPORT_PATH)

    print()
    print("Answer compliance evaluation completed.")
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")
    print()
    print("Summary:")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()