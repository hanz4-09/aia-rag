import csv
import json
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.rag.retriever_factory import create_retriever


EVAL_SET_PATH = PROJECT_ROOT / "eval" / "context_precision_eval_set.jsonl"
CSV_REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "evaluations"
    / "2026-05-09_context_assembly_topn_comparison.csv"
)
MD_REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "evaluations"
    / "2026-05-09_context_assembly_topn_comparison.md"
)


TOP_N_VALUES = [5, 3, 2]


def load_eval_set(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Context precision evaluation set not found: {path}")

    records = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    return records


def contains_keyword(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def is_chunk_relevant(
    chunk: Dict[str, Any],
    expected_source: str,
    relevant_keywords: List[str],
) -> bool:
    metadata = chunk.get("metadata", {})
    filename = metadata.get("filename", "")
    text = chunk.get("text", "")

    source_match = filename == expected_source

    keyword_match = False
    if relevant_keywords:
        keyword_match = any(
            contains_keyword(text, keyword)
            for keyword in relevant_keywords
        )

    return source_match and keyword_match


def build_retriever_config(base_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Keep retrieval candidate size at top_k = 5.

    This simulates:
    - retrieve 5 candidates
    - only use top N candidates for context assembly
    """
    config = deepcopy(base_config)
    config["retrieval"]["mode"] = "hybrid"
    config["retrieval"]["enable_reranker"] = True
    config["retrieval"]["top_k"] = 5
    return config


def evaluate_record_for_top_n(
    record: Dict[str, Any],
    retrieved_chunks: List[Dict[str, Any]],
    retrieval_latency_ms: int,
    top_n: int,
) -> Dict[str, Any]:
    question = record["question"]
    expected_source = record["expected_source"]
    category = record.get("category", "")
    relevant_keywords = record.get("relevant_keywords", [])

    selected_chunks = retrieved_chunks[:top_n]

    retrieved_sources = [
        item.get("metadata", {}).get("filename")
        for item in selected_chunks
    ]

    top1_source = retrieved_sources[0] if retrieved_sources else None
    source_hit = expected_source in retrieved_sources
    top1_source_match = top1_source == expected_source

    relevant_flags = [
        is_chunk_relevant(item, expected_source, relevant_keywords)
        for item in selected_chunks
    ]

    relevant_count = sum(1 for flag in relevant_flags if flag)
    total_chunks = len(selected_chunks)
    irrelevant_count = total_chunks - relevant_count

    context_precision_at_n = (
        relevant_count / total_chunks
        if total_chunks
        else 0
    )

    relevant_ranks = [
        index + 1
        for index, flag in enumerate(relevant_flags)
        if flag
    ]

    first_relevant_rank = relevant_ranks[0] if relevant_ranks else None

    irrelevant_sources = [
        source or ""
        for source, is_relevant in zip(retrieved_sources, relevant_flags)
        if not is_relevant
    ]

    return {
        "top_n_context_chunks": top_n,
        "question": question,
        "category": category,
        "expected_source": expected_source,
        "retrieved_sources": "|".join([src or "" for src in retrieved_sources]),
        "top1_source": top1_source,
        "source_hit": source_hit,
        "top1_source_match": top1_source_match,
        "total_chunks": total_chunks,
        "relevant_chunks": relevant_count,
        "irrelevant_chunks": irrelevant_count,
        "context_precision_at_n": round(context_precision_at_n, 4),
        "first_relevant_rank": first_relevant_rank,
        "irrelevant_sources": "|".join(irrelevant_sources),
        "retrieval_latency_ms": retrieval_latency_ms,
    }


def summarize(details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summaries = []

    for top_n in TOP_N_VALUES:
        items = [
            item for item in details
            if item["top_n_context_chunks"] == top_n
        ]

        total = len(items)

        if total == 0:
            summaries.append(
                {
                    "top_n_context_chunks": top_n,
                    "total_questions": 0,
                    "source_hit_rate": 0,
                    "top1_source_accuracy": 0,
                    "avg_context_precision_at_n": 0,
                    "avg_relevant_chunks": 0,
                    "avg_irrelevant_chunks": 0,
                    "avg_total_chunks": 0,
                    "avg_retrieval_latency_ms": 0,
                }
            )
            continue

        def true_rate(field: str) -> float:
            return round(
                sum(1 for item in items if item.get(field) is True) / total,
                4,
            )

        context_precisions = [
            item["context_precision_at_n"]
            for item in items
            if isinstance(item.get("context_precision_at_n"), (int, float))
        ]

        relevant_chunks = [
            item["relevant_chunks"]
            for item in items
            if isinstance(item.get("relevant_chunks"), (int, float))
        ]

        irrelevant_chunks = [
            item["irrelevant_chunks"]
            for item in items
            if isinstance(item.get("irrelevant_chunks"), (int, float))
        ]

        total_chunks = [
            item["total_chunks"]
            for item in items
            if isinstance(item.get("total_chunks"), (int, float))
        ]

        latencies = [
            item["retrieval_latency_ms"]
            for item in items
            if isinstance(item.get("retrieval_latency_ms"), (int, float))
        ]

        summaries.append(
            {
                "top_n_context_chunks": top_n,
                "total_questions": total,
                "source_hit_rate": true_rate("source_hit"),
                "top1_source_accuracy": true_rate("top1_source_match"),
                "avg_context_precision_at_n": round(
                    sum(context_precisions) / len(context_precisions),
                    4,
                )
                if context_precisions
                else 0,
                "avg_relevant_chunks": round(
                    sum(relevant_chunks) / len(relevant_chunks),
                    2,
                )
                if relevant_chunks
                else 0,
                "avg_irrelevant_chunks": round(
                    sum(irrelevant_chunks) / len(irrelevant_chunks),
                    2,
                )
                if irrelevant_chunks
                else 0,
                "avg_total_chunks": round(
                    sum(total_chunks) / len(total_chunks),
                    2,
                )
                if total_chunks
                else 0,
                "avg_retrieval_latency_ms": round(
                    sum(latencies) / len(latencies),
                    2,
                )
                if latencies
                else 0,
            }
        )

    return summaries


def write_csv_report(
    details: List[Dict[str, Any]],
    summaries: List[Dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "top_n_context_chunks",
        "question",
        "category",
        "expected_source",
        "retrieved_sources",
        "top1_source",
        "source_hit",
        "top1_source_match",
        "total_chunks",
        "relevant_chunks",
        "irrelevant_chunks",
        "context_precision_at_n",
        "first_relevant_rank",
        "irrelevant_sources",
        "retrieval_latency_ms",
        "total_questions",
        "source_hit_rate",
        "top1_source_accuracy",
        "avg_context_precision_at_n",
        "avg_relevant_chunks",
        "avg_irrelevant_chunks",
        "avg_total_chunks",
        "avg_retrieval_latency_ms",
    ]

    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for summary in summaries:
            row = {field: "" for field in fieldnames}
            row.update(summary)
            row["row_type"] = "summary"
            writer.writerow(row)

        for detail in details:
            row = {field: "" for field in fieldnames}
            row.update(detail)
            row["row_type"] = "detail"
            writer.writerow(row)


def write_markdown_report(summaries: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = "\n".join(
        [
            (
                f"| Top {item['top_n_context_chunks']} | "
                f"{item['total_questions']} | "
                f"{item['source_hit_rate']} | "
                f"{item['top1_source_accuracy']} | "
                f"{item['avg_context_precision_at_n']} | "
                f"{item['avg_relevant_chunks']} | "
                f"{item['avg_irrelevant_chunks']} | "
                f"{item['avg_total_chunks']} | "
                f"{item['avg_retrieval_latency_ms']} ms |"
            )
            for item in summaries
        ]
    )

    content = f"""# Context Assembly Top-N Comparison Report

Date: 2026-05-09  
Project: AIA RAG Case Study Service  
Evaluation Type: Context Assembly Simulation  
Version: v1  
Supporting CSV: reports/evaluations/2026-05-09_context_assembly_topn_comparison.csv

---

## 1. Objective

This evaluation simulates different context assembly strategies before changing the production RAG flow.

The current retriever returns top 5 chunks.

This simulation compares what happens if the generator only uses:

- top 5 chunks
- top 3 chunks
- top 2 chunks

The goal is to check whether reducing context chunks can improve context precision without significantly hurting source coverage.

---

## 2. Evaluation Dataset

Evaluation set:

    eval/context_precision_eval_set.jsonl

The dataset includes 10 representative questions across:

- compliance
- data security
- technical specification
- HR policy
- architecture

---

## 3. Method

For each question:

1. Retrieve top 5 chunks using hybrid + rerank.
2. Simulate context assembly with top N chunks.
3. Calculate source hit and context precision for each N.

A chunk is considered relevant when:

    chunk filename == expected_source
    and
    chunk text contains at least one relevant keyword

This is a rule-based approximation.

---

## 4. Summary Results

| Context Strategy | Total Questions | Source Hit Rate | Top-1 Source Accuracy | Avg Context Precision | Avg Relevant Chunks | Avg Irrelevant Chunks | Avg Total Chunks | Avg Retrieval Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{summary_rows}

---

## 5. Interpretation

This report should be used to decide whether the system should reduce the number of chunks passed to the LLM.

A good context assembly strategy should:

- keep source_hit_rate high
- keep top1_source_accuracy high
- improve avg_context_precision
- reduce avg_irrelevant_chunks
- reduce expected input tokens and generation latency

If top 3 maintains source coverage while improving context precision, it is a strong candidate for the next context assembly configuration.

---

## 6. Limitations

Current limitations:

1. This is a simulation, not yet a production behavior change.
2. Relevance is rule-based.
3. Keyword matching may undercount semantic relevance.
4. It does not directly measure final answer faithfulness.
5. Token reduction is inferred, not directly measured here.

---

## 7. Next Steps

Recommended next steps:

1. Review the top-N comparison results.
2. If top 3 gives a good tradeoff, add a configurable context.max_context_chunks setting.
3. Update LLMGenerator to use only selected context chunks.
4. Rerun answer quality and operations reports.
5. Generate a follow-up formal evaluation report after the change.
"""

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def main():
    base_config = load_config()
    config = build_retriever_config(base_config)
    eval_set = load_eval_set(EVAL_SET_PATH)

    retriever = create_retriever(config)

    details = []

    for index, record in enumerate(eval_set, start=1):
        print(f"Evaluating top-N context {index}/{len(eval_set)}: {record['question']}")

        start_time = time.time()
        retrieved_chunks = retriever.retrieve(record["question"])
        retrieval_latency_ms = int((time.time() - start_time) * 1000)

        for top_n in TOP_N_VALUES:
            detail = evaluate_record_for_top_n(
                record=record,
                retrieved_chunks=retrieved_chunks,
                retrieval_latency_ms=retrieval_latency_ms,
                top_n=top_n,
            )
            details.append(detail)

            print(
                f"  top_n={top_n}, "
                f"source_hit={detail['source_hit']}, "
                f"precision={detail['context_precision_at_n']}, "
                f"relevant={detail['relevant_chunks']}/{detail['total_chunks']}"
            )

    summaries = summarize(details)

    write_csv_report(details, summaries, CSV_REPORT_PATH)
    write_markdown_report(summaries, MD_REPORT_PATH)

    print()
    print("Context assembly top-N comparison completed.")
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")
    print()
    print("Summary:")
    for item in summaries:
        print(
            f"top_n={item['top_n_context_chunks']}, "
            f"source_hit_rate={item['source_hit_rate']}, "
            f"top1_source_accuracy={item['top1_source_accuracy']}, "
            f"avg_context_precision_at_n={item['avg_context_precision_at_n']}, "
            f"avg_relevant_chunks={item['avg_relevant_chunks']}, "
            f"avg_irrelevant_chunks={item['avg_irrelevant_chunks']}"
        )


if __name__ == "__main__":
    main()