import csv
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.core.config import load_config
from app.rag.retriever_factory import create_retriever


OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
TODAY = time.strftime("%Y-%m-%d")
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_corpus_regression_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_corpus_regression_eval.md"


GOLDEN_RETRIEVAL_CASES = [
    {
        "case_id": "golden_audit_logging_requirements",
        "category": "compliance_en",
        "query": "What are the audit logging requirements?",
        "expected_source": "03_compliance_guide_en.txt",
        "expected_keywords": [
            "Audit Logging Requirements",
            "timestamp",
            "user identity",
            "request ID",
        ],
        "required_top_k": 3,
    },
    {
        "case_id": "golden_audit_log_retention",
        "category": "compliance_en",
        "query": "How long should audit logs for privileged operations be retained?",
        "expected_source": "03_compliance_guide_en.txt",
        "expected_keywords": [
            "privileged operations",
            "one year",
        ],
        "required_top_k": 3,
    },
    {
        "case_id": "golden_api_key_leak_cn",
        "category": "security_cn",
        "query": "API Key 泄露后应该怎么处理？",
        "expected_source": "04_data_security_policy_cn.txt",
        "expected_keywords": [
            "API Key",
            "24 小时",
            "安全事件报告",
        ],
        "required_top_k": 3,
    },
    {
        "case_id": "golden_api_key_employee_report_cn",
        "category": "security_cn",
        "query": "员工怀疑 API Key 泄露后应该多久内报告？",
        "expected_source": "02_employee_handbook_cn.txt",
        "expected_keywords": [
            "24 小时",
            "Security Operations",
        ],
        "required_top_k": 5,
    },
    {
        "case_id": "golden_annual_leave_policy",
        "category": "hr_policy",
        "query": "What is the annual leave policy and manager review time?",
        "expected_source": "01_employee_handbook_en.txt",
        "expected_keywords": [
            "annual leave",
            "three working days",
        ],
        "required_top_k": 5,
    },
    {
        "case_id": "golden_ocr_api_key_incident",
        "category": "ocr_en",
        "query": "API Key incidents must be reported within 24 hours",
        "expected_source": "99_scanned_pdf_detection_test.pdf",
        "expected_keywords": [
            "API Key incidents",
            "24 hours",
        ],
        "required_top_k": 3,
    },
    {
        "case_id": "golden_pii_redaction_format_cn",
        "category": "privacy_cn",
        "query": "敏感数据脱敏的格式是什么？",
        "expected_source": "08_pii_redaction_spec_cn.txt",
        "expected_keywords": [
            "[EMAIL]",
            "[PHONE]",
            "[REDACTED_SECRET]",
        ],
        "required_top_k": 5,
    },
]


def contains_keyword(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def evaluate_keywords(text: str, expected_keywords: List[str]) -> Dict[str, Any]:
    matched = []
    missing = []

    for keyword in expected_keywords:
        if contains_keyword(text, keyword):
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


def evaluate_case(case: Dict[str, Any], retriever) -> Dict[str, Any]:
    query = case["query"]
    expected_source = case["expected_source"]
    required_top_k = case.get("required_top_k", 5)

    chunks = retriever.retrieve(query)

    retrieved_sources = [
        chunk.get("metadata", {}).get("filename", "")
        for chunk in chunks
    ]

    expected_rank = None
    matched_text = ""

    for index, chunk in enumerate(chunks, start=1):
        filename = chunk.get("metadata", {}).get("filename", "")
        if filename == expected_source:
            expected_rank = index
            matched_text = chunk.get("text", "") or ""
            break

    top1_hit = expected_rank == 1
    top3_hit = expected_rank is not None and expected_rank <= 3
    top5_hit = expected_rank is not None and expected_rank <= 5
    required_top_k_hit = (
        expected_rank is not None
        and expected_rank <= required_top_k
    )

    keyword_metrics = evaluate_keywords(
        matched_text,
        case.get("expected_keywords", []),
    )

    keyword_pass = keyword_metrics["keyword_hit_rate"] >= 0.5
    pass_result = required_top_k_hit and keyword_pass

    return {
        "case_id": case["case_id"],
        "category": case.get("category", ""),
        "query": query,
        "expected_source": expected_source,
        "required_top_k": required_top_k,
        "expected_source_rank": expected_rank if expected_rank is not None else "",
        "top1_hit": top1_hit,
        "top3_hit": top3_hit,
        "top5_hit": top5_hit,
        "required_top_k_hit": required_top_k_hit,
        "retrieved_sources": "|".join(retrieved_sources),
        "retrieved_text_preview": matched_text[:300].replace("\n", " "),
        **keyword_metrics,
        "pass": pass_result,
    }


def rate(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    passing = sum(1 for item in results if item["pass"])
    top1 = sum(1 for item in results if item["top1_hit"])
    top3 = sum(1 for item in results if item["top3_hit"])
    top5 = sum(1 for item in results if item["top5_hit"])
    required_top_k = sum(1 for item in results if item["required_top_k_hit"])

    ranks = [
        int(item["expected_source_rank"])
        for item in results
        if item["expected_source_rank"] != ""
    ]

    avg_rank = round(statistics.mean(ranks), 4) if ranks else 0.0
    max_rank = max(ranks) if ranks else 0

    avg_keyword_hit_rate = round(
        statistics.mean([item["keyword_hit_rate"] for item in results]),
        4,
    ) if results else 0.0

    return {
        "total_cases": total,
        "passing_count": passing,
        "pass_rate": rate(passing, total),
        "top1_hit_count": top1,
        "top1_hit_rate": rate(top1, total),
        "top3_hit_count": top3,
        "top3_hit_rate": rate(top3, total),
        "top5_hit_count": top5,
        "top5_hit_rate": rate(top5, total),
        "required_top_k_hit_count": required_top_k,
        "required_top_k_hit_rate": rate(required_top_k, total),
        "avg_expected_source_rank": avg_rank,
        "max_expected_source_rank": max_rank,
        "avg_keyword_hit_rate": avg_keyword_hit_rate,
        "prd_pass": passing == total,
    }


def write_csv(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "case_id",
        "category",
        "query",
        "expected_source",
        "required_top_k",
        "expected_source_rank",
        "top1_hit",
        "top3_hit",
        "top5_hit",
        "required_top_k_hit",
        "retrieved_sources",
        "retrieved_text_preview",
        "expected_keywords_total",
        "expected_keywords_matched",
        "keyword_hit_rate",
        "missing_keywords",
        "pass",
        "total_cases",
        "passing_count",
        "pass_rate",
        "top1_hit_count",
        "top1_hit_rate",
        "top3_hit_count",
        "top3_hit_rate",
        "top5_hit_count",
        "top5_hit_rate",
        "required_top_k_hit_count",
        "required_top_k_hit_rate",
        "avg_expected_source_rank",
        "max_expected_source_rank",
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
        "# Corpus Growth Regression Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: Corpus Growth / Golden Retrieval Regression",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passing cases: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
        f"- Top-1 hit rate: {summary['top1_hit_rate']}",
        f"- Top-3 hit rate: {summary['top3_hit_rate']}",
        f"- Top-5 hit rate: {summary['top5_hit_rate']}",
        f"- Required Top-K hit rate: {summary['required_top_k_hit_rate']}",
        f"- Average expected source rank: {summary['avg_expected_source_rank']}",
        f"- Max expected source rank: {summary['max_expected_source_rank']}",
        f"- Average keyword hit rate: {summary['avg_keyword_hit_rate']}",
        f"- PRD pass: {summary['prd_pass']}",
        "",
        "## Method",
        "",
        "This evaluation runs a fixed set of golden retrieval queries after ingestion.",
        "It verifies whether important expected sources still appear within the required Top-K range.",
        "",
        "This is intended as a regression guard for future corpus growth.",
        "When new files are added to `data/raw/`, the vector store should be rebuilt and this script should be rerun.",
        "",
        "Recommended workflow:",
        "",
        "    python scripts/ingest.py",
        "    python scripts/evaluate_corpus_regression.py",
        "    python scripts/evaluate_context_precision.py",
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
                f"- Query: {result['query']}",
                f"- Expected source: {result['expected_source']}",
                f"- Expected source rank: {result['expected_source_rank']}",
                f"- Required Top-K: {result['required_top_k']}",
                f"- Top-1 hit: {result['top1_hit']}",
                f"- Top-3 hit: {result['top3_hit']}",
                f"- Top-5 hit: {result['top5_hit']}",
                f"- Required Top-K hit: {result['required_top_k_hit']}",
                f"- Keyword hit rate: {result['keyword_hit_rate']}",
                f"- Missing keywords: {result['missing_keywords'] or 'None'}",
                f"- Pass: {result['pass']}",
                f"- Retrieved sources: {result['retrieved_sources']}",
                "",
            ]
        )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config = load_config()
    retriever = create_retriever(config)

    print(f"Total corpus regression eval cases: {len(GOLDEN_RETRIEVAL_CASES)}")
    print()

    results = []

    for index, case in enumerate(GOLDEN_RETRIEVAL_CASES, start=1):
        result = evaluate_case(case, retriever)
        results.append(result)

        status = "✅" if result["pass"] else "❌"
        print(
            f"[{index}/{len(GOLDEN_RETRIEVAL_CASES)}] {case['case_id']} "
            f"{status} pass={result['pass']}, "
            f"rank={result['expected_source_rank']}, "
            f"required_top_k={result['required_top_k']}, "
            f"keyword_hit_rate={result['keyword_hit_rate']}"
        )

        if result["missing_keywords"]:
            print(f"  Missing keywords: {result['missing_keywords']}")

    summary = summarize(results)

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("CORPUS GROWTH REGRESSION EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:                 {summary['total_cases']}")
    print(f"  Passing cases:               {summary['passing_count']}")
    print(f"  Pass rate:                   {summary['pass_rate']}")
    print(f"  Top-1 hit rate:              {summary['top1_hit_rate']}")
    print(f"  Top-3 hit rate:              {summary['top3_hit_rate']}")
    print(f"  Top-5 hit rate:              {summary['top5_hit_rate']}")
    print(f"  Required Top-K hit rate:     {summary['required_top_k_hit_rate']}")
    print(f"  Avg expected source rank:    {summary['avg_expected_source_rank']}")
    print(f"  Max expected source rank:    {summary['max_expected_source_rank']}")
    print(f"  Avg keyword hit rate:        {summary['avg_keyword_hit_rate']}")
    print(f"  PRD Status:                  {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
