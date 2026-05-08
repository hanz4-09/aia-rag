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


EVAL_SET_PATH = PROJECT_ROOT / "eval" / "retrieval_eval_set.jsonl"
REPORT_PATH = PROJECT_ROOT / "reports" / "retrieval_evaluation_report.csv"


def load_eval_set(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Evaluation set not found: {path}")

    records = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            records.append(json.loads(line))

    return records


def build_config_for_mode(base_config: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """
    Build config for each evaluation mode.

    Supported modes:
    - vector
    - hybrid
    - hybrid_rerank
    """
    config = deepcopy(base_config)

    if mode == "vector":
        config["retrieval"]["mode"] = "vector"
        config["retrieval"]["enable_reranker"] = False
        return config

    if mode == "hybrid":
        config["retrieval"]["mode"] = "hybrid"
        config["retrieval"]["enable_reranker"] = False
        return config

    if mode == "hybrid_rerank":
        config["retrieval"]["mode"] = "hybrid"
        config["retrieval"]["enable_reranker"] = True
        return config

    raise ValueError(f"Unsupported evaluation mode: {mode}")


def evaluate_mode(
    base_config: Dict[str, Any],
    mode: str,
    eval_set: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Evaluate one retrieval mode against the retrieval evaluation set.
    """
    config = build_config_for_mode(base_config, mode)
    retriever = create_retriever(config)

    total = len(eval_set)
    hit_count = 0
    top1_count = 0
    latencies = []

    detailed_results = []

    for record in eval_set:
        question = record["question"]
        expected_source = record["expected_source"]

        start_time = time.time()
        results = retriever.retrieve(question)
        latency_ms = int((time.time() - start_time) * 1000)
        latencies.append(latency_ms)

        retrieved_sources = [
            item.get("metadata", {}).get("filename")
            for item in results
        ]

        top1_source = retrieved_sources[0] if retrieved_sources else None

        hit = expected_source in retrieved_sources
        top1_hit = top1_source == expected_source

        expected_rank = None
        reciprocal_rank = 0.0

        if hit:
            hit_count += 1
            expected_rank = retrieved_sources.index(expected_source) + 1
            reciprocal_rank = 1.0 / expected_rank

        if top1_hit:
            top1_count += 1

        detailed_results.append(
            {
                "mode": mode,
                "question": question,
                "category": record.get("category"),
                "expected_source": expected_source,
                "top1_source": top1_source,
                "retrieved_sources": "|".join([src or "" for src in retrieved_sources]),
                "hit": hit,
                "top1_hit": top1_hit,
                "expected_rank": expected_rank,
                "reciprocal_rank": round(reciprocal_rank, 4),
                "latency_ms": latency_ms,
            }
        )

    mrr = (
        sum(item["reciprocal_rank"] for item in detailed_results) / total
        if total
        else 0
    )

    summary = {
        "mode": mode,
        "total_questions": total,
        "hit_rate": round(hit_count / total, 4) if total else 0,
        "top1_accuracy": round(top1_count / total, 4) if total else 0,
        "mrr": round(mrr, 4),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "details": detailed_results,
    }

    return summary


def write_report(summaries: List[Dict[str, Any]], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for summary in summaries:
        rows.append(
            {
                "row_type": "summary",
                "mode": summary["mode"],
                "question": "",
                "category": "",
                "expected_source": "",
                "top1_source": "",
                "retrieved_sources": "",
                "hit": "",
                "top1_hit": "",
                "expected_rank": "",
                "reciprocal_rank": "",
                "latency_ms": "",
                "total_questions": summary["total_questions"],
                "hit_rate": summary["hit_rate"],
                "top1_accuracy": summary["top1_accuracy"],
                "mrr": summary["mrr"],
                "avg_latency_ms": summary["avg_latency_ms"],
            }
        )

        for detail in summary["details"]:
            rows.append(
                {
                    "row_type": "detail",
                    "mode": detail["mode"],
                    "question": detail["question"],
                    "category": detail["category"],
                    "expected_source": detail["expected_source"],
                    "top1_source": detail["top1_source"],
                    "retrieved_sources": detail["retrieved_sources"],
                    "hit": detail["hit"],
                    "top1_hit": detail["top1_hit"],
                    "expected_rank": detail["expected_rank"],
                    "reciprocal_rank": detail["reciprocal_rank"],
                    "latency_ms": detail["latency_ms"],
                    "total_questions": "",
                    "hit_rate": "",
                    "top1_accuracy": "",
                    "mrr": "",
                    "avg_latency_ms": "",
                }
            )

    fieldnames = [
        "row_type",
        "mode",
        "question",
        "category",
        "expected_source",
        "top1_source",
        "retrieved_sources",
        "hit",
        "top1_hit",
        "expected_rank",
        "reciprocal_rank",
        "latency_ms",
        "total_questions",
        "hit_rate",
        "top1_accuracy",
        "mrr",
        "avg_latency_ms",
    ]

    with open(report_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    base_config = load_config()
    eval_set = load_eval_set(EVAL_SET_PATH)

    modes = ["vector", "hybrid", "hybrid_rerank"]

    summaries = []

    for mode in modes:
        print(f"Evaluating retrieval mode: {mode}")

        summary = evaluate_mode(
            base_config=base_config,
            mode=mode,
            eval_set=eval_set,
        )

        summaries.append(summary)

        print(
            f"mode={mode}, "
            f"hit_rate={summary['hit_rate']}, "
            f"top1_accuracy={summary['top1_accuracy']}, "
            f"mrr={summary['mrr']}, "
            f"avg_latency_ms={summary['avg_latency_ms']}"
        )

    write_report(summaries, REPORT_PATH)

    print()
    print("Retrieval evaluation report generated.")
    print(f"Report path: {REPORT_PATH}")


if __name__ == "__main__":
    main()