"""
Context Precision Evaluation Script

Evaluates context precision using a hybrid approach:
1. Source Accuracy: Does the top-1 retrieved chunk match the expected source?
2. Keyword Coverage: Does the retrieved context contain expected keywords?

Context Precision = 0.5 * source_accuracy + 0.5 * keyword_coverage

PRD Target: Context Precision >= 0.70
"""

import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.rag.retriever_factory import create_retriever
from app.rag.safety import check_safety


EVAL_SET_PATH = PROJECT_ROOT / "eval" / "answer_eval_set.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"


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


def evaluate_context_precision(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    expected_source: str = None,
    expected_keywords: List[str] = None,
) -> Dict[str, Any]:
    """
    Evaluate context precision using hybrid metrics.

    1. Source Accuracy: Does the top-1 chunk match the expected source?
    2. Keyword Coverage: What fraction of expected keywords appear in the context?
    """
    if not retrieved_chunks:
        return {
            "context_precision": 0.0,
            "source_accuracy": 0.0,
            "keyword_coverage": 0.0,
            "total_chunks": 0,
            "top1_source": "",
            "expected_source": expected_source or "",
            "keywords_found": 0,
            "keywords_total": 0,
        }

    # Build context text from all chunks
    context_text = " ".join(chunk.get("text", "") for chunk in retrieved_chunks)

    # 1. Source Accuracy
    top1_metadata = retrieved_chunks[0].get("metadata", {})
    top1_source = top1_metadata.get("filename", "unknown")

    source_accuracy = 0.0
    if expected_source:
        # Check if expected source appears in any retrieved chunk
        all_sources = [
            chunk.get("metadata", {}).get("filename", "")
            for chunk in retrieved_chunks
        ]
        source_accuracy = 1.0 if expected_source in all_sources else 0.0

    # 2. Keyword Coverage
    keywords_total = len(expected_keywords) if expected_keywords else 0
    keywords_found = 0
    if expected_keywords:
        context_lower = context_text.lower()
        for keyword in expected_keywords:
            if keyword.lower() in context_lower:
                keywords_found += 1

    keyword_coverage = keywords_found / keywords_total if keywords_total > 0 else 1.0

    # Combined score
    context_precision = 0.5 * source_accuracy + 0.5 * keyword_coverage

    return {
        "context_precision": round(context_precision, 4),
        "source_accuracy": round(source_accuracy, 4),
        "keyword_coverage": round(keyword_coverage, 4),
        "total_chunks": len(retrieved_chunks),
        "top1_source": top1_source,
        "expected_source": expected_source or "",
        "keywords_found": keywords_found,
        "keywords_total": keywords_total,
    }


def main():
    config = load_config()
    eval_set = load_eval_set(EVAL_SET_PATH)

    retriever = create_retriever(config)

    # Filter to non-refusal questions with expected_source
    answerable_records = [
        r for r in eval_set
        if not r.get("expected_refused", False) and r.get("expected_source")
    ]

    print(f"Total eval questions: {len(eval_set)}")
    print(f"Answerable questions with expected_source: {len(answerable_records)}")
    print()

    results = []

    for index, record in enumerate(answerable_records, start=1):
        question = record["question"]
        category = record.get("category", "")
        expected_source = record.get("expected_source", "")
        expected_keywords = record.get("expected_keywords", [])

        print(f"[{index}/{len(answerable_records)}] {question}")

        safety_result = check_safety(question)
        if not safety_result["safe"]:
            print(f"  SKIPPED (safety refusal)")
            results.append({
                "question": question,
                "category": category,
                "skipped": True,
                "context_precision": None,
                "source_accuracy": None,
                "keyword_coverage": None,
                "total_chunks": None,
                "top1_source": "",
                "expected_source": expected_source,
                "keywords_found": 0,
                "keywords_total": 0,
            })
            continue

        retrieved_chunks = retriever.retrieve(question)

        if not retrieved_chunks:
            print(f"  SKIPPED (no chunks)")
            results.append({
                "question": question,
                "category": category,
                "skipped": True,
                "context_precision": 0.0,
                "source_accuracy": 0.0,
                "keyword_coverage": 0.0,
                "total_chunks": 0,
                "top1_source": "",
                "expected_source": expected_source,
                "keywords_found": 0,
                "keywords_total": len(expected_keywords),
            })
            continue

        precision = evaluate_context_precision(
            question=question,
            retrieved_chunks=retrieved_chunks,
            expected_source=expected_source,
            expected_keywords=expected_keywords,
        )

        score = precision["context_precision"]
        src_acc = precision["source_accuracy"]
        kw_cov = precision["keyword_coverage"]

        status = "✅" if score >= 0.7 else "❌"
        print(f"  {status} Precision: {score} (source_acc={src_acc}, kw_cov={kw_cov}, "
              f"chunks={precision['total_chunks']})")

        results.append({
            "question": question,
            "category": category,
            "skipped": False,
            **precision,
        })

    # Summary
    scored = [r for r in results if r.get("context_precision") is not None]

    if scored:
        avg_precision = sum(r["context_precision"] for r in scored) / len(scored)
        avg_source_acc = sum(r["source_accuracy"] for r in scored) / len(scored)
        avg_kw_cov = sum(r["keyword_coverage"] for r in scored) / len(scored)
        passing = sum(1 for r in scored if r["context_precision"] >= 0.7)
    else:
        avg_precision = 0
        avg_source_acc = 0
        avg_kw_cov = 0
        passing = 0

    summary = {
        "total_answerable": len(answerable_records),
        "total_evaluated": len(scored),
        "avg_context_precision": round(avg_precision, 4),
        "avg_source_accuracy": round(avg_source_acc, 4),
        "avg_keyword_coverage": round(avg_kw_cov, 4),
        "passing_count": passing,
        "passing_rate": round(passing / len(scored), 4) if scored else 0,
        "prd_target": 0.70,
        "prd_pass": avg_precision >= 0.70,
    }

    print()
    print("=" * 60)
    print("CONTEXT PRECISION EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Method:              Hybrid (Source Accuracy + Keyword Coverage)")
    print(f"  Answerable questions: {summary['total_answerable']}")
    print(f"  Evaluated questions:  {summary['total_evaluated']}")
    print(f"  Avg Context Precision:{summary['avg_context_precision']}")
    print(f"  Avg Source Accuracy:  {summary['avg_source_accuracy']}")
    print(f"  Avg Keyword Coverage: {summary['avg_keyword_coverage']}")
    print(f"  Passing (>=0.70):     {summary['passing_count']}/{summary['total_evaluated']}")
    print(f"  PRD Target:           >= {summary['prd_target']}")
    print(f"  PRD Status:           {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)

    # Write CSV
    timestamp = time.strftime("%Y-%m-%d")
    csv_path = OUTPUT_DIR / f"{timestamp}_context_precision_eval.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type", "question", "category", "skipped",
        "context_precision", "source_accuracy", "keyword_coverage",
        "total_chunks", "top1_source", "expected_source",
        "keywords_found", "keywords_total",
        "total_answerable", "total_evaluated", "avg_context_precision",
        "avg_source_accuracy", "avg_keyword_coverage",
        "passing_count", "passing_rate", "prd_target", "prd_pass",
    ]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        summary_row = {field: "" for field in fieldnames}
        summary_row.update({"row_type": "summary", **summary})
        writer.writerow(summary_row)

        for r in results:
            row = {field: "" for field in fieldnames}
            row["row_type"] = "detail"
            row.update(r)
            writer.writerow(row)

    print(f"\nCSV report: {csv_path}")

    return results, summary


if __name__ == "__main__":
    main()
