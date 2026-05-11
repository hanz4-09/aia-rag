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


REPORT_JSON_PATH = PROJECT_ROOT / "reports" / "ingestion" / "scanned_pdf_detection_report.json"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
TODAY = time.strftime("%Y-%m-%d")
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_pdf_ingestion_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_pdf_ingestion_eval.md"


EXPECTED_CASES = [
    {
        "case_id": "text_based_pdf_loaded",
        "filename": "98_text_pdf_detection_test.pdf",
        "expected_status": "loaded",
        "expected_scanned_pdf_candidate": False,
        "expected_ocr_performed": False,
        "expected_ocr_succeeded": False,
        "min_pages_with_text": 1,
        "min_extracted_chars": 20,
        "retrieval_query": "Audit logs should be retained for at least one year",
        "expected_retrieval_filename": "98_text_pdf_detection_test.pdf",
    },
    {
        "case_id": "scanned_pdf_ocr_extracted",
        "filename": "99_scanned_pdf_detection_test.pdf",
        "expected_status": "loaded_with_ocr",
        "expected_scanned_pdf_candidate": True,
        "expected_ocr_performed": True,
        "expected_ocr_succeeded": True,
        "min_pages_without_text": 1,
        "min_extracted_chars": 20,
        "retrieval_query": "API Key incidents must be reported within 24 hours",
        "expected_retrieval_filename": "99_scanned_pdf_detection_test.pdf",
    },
]


def load_ingestion_report() -> Dict[str, Any]:
    if not REPORT_JSON_PATH.exists():
        raise FileNotFoundError(
            f"Ingestion PDF detection/OCR report not found: {REPORT_JSON_PATH}. "
            "Run `python scripts/ingest.py` first."
        )

    with REPORT_JSON_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_pdf_result(report: Dict[str, Any], filename: str) -> Dict[str, Any]:
    for item in report.get("pdf_detection_results", []):
        if item.get("filename") == filename:
            return item
    return {}


def evaluate_retrieval(case: Dict[str, Any]) -> Dict[str, Any]:
    config = load_config()
    retriever = create_retriever(config)

    query = case.get("retrieval_query", "")
    expected_filename = case.get("expected_retrieval_filename", "")

    if not query or not expected_filename:
        return {
            "retrieval_query": query,
            "expected_retrieval_filename": expected_filename,
            "retrieval_hit": True,
            "retrieval_rank": "",
            "retrieved_sources": "",
        }

    chunks = retriever.retrieve(query)
    retrieved_sources = [
        chunk.get("metadata", {}).get("filename")
        for chunk in chunks
    ]

    retrieval_rank = ""
    retrieval_hit = False

    for index, filename in enumerate(retrieved_sources, start=1):
        if filename == expected_filename:
            retrieval_hit = True
            retrieval_rank = index
            break

    return {
        "retrieval_query": query,
        "expected_retrieval_filename": expected_filename,
        "retrieval_hit": retrieval_hit,
        "retrieval_rank": retrieval_rank,
        "retrieved_sources": "|".join([source or "" for source in retrieved_sources]),
    }


def evaluate_case(case: Dict[str, Any], report: Dict[str, Any]) -> Dict[str, Any]:
    item = find_pdf_result(report, case["filename"])

    found = bool(item)

    status_match = item.get("status") == case.get("expected_status")
    scanned_match = (
        item.get("scanned_pdf_candidate")
        == case.get("expected_scanned_pdf_candidate")
    )
    ocr_performed_match = (
        item.get("ocr_performed") == case.get("expected_ocr_performed")
    )
    ocr_succeeded_match = (
        item.get("ocr_succeeded") == case.get("expected_ocr_succeeded")
    )

    pages_with_text = item.get("pages_with_text", 0) or 0
    pages_without_text = item.get("pages_without_text", 0) or 0
    extracted_chars = item.get("extracted_chars", 0) or 0

    pages_with_text_pass = True
    if "min_pages_with_text" in case:
        pages_with_text_pass = pages_with_text >= case["min_pages_with_text"]

    pages_without_text_pass = True
    if "min_pages_without_text" in case:
        pages_without_text_pass = (
            pages_without_text >= case["min_pages_without_text"]
        )

    extracted_chars_pass = True
    if "min_extracted_chars" in case:
        extracted_chars_pass = extracted_chars >= case["min_extracted_chars"]

    retrieval_result = evaluate_retrieval(case)

    pass_result = all(
        [
            found,
            status_match,
            scanned_match,
            ocr_performed_match,
            ocr_succeeded_match,
            pages_with_text_pass,
            pages_without_text_pass,
            extracted_chars_pass,
            retrieval_result["retrieval_hit"],
        ]
    )

    return {
        "case_id": case["case_id"],
        "filename": case["filename"],
        "found": found,
        "expected_status": case.get("expected_status"),
        "actual_status": item.get("status"),
        "status_match": status_match,
        "expected_scanned_pdf_candidate": case.get(
            "expected_scanned_pdf_candidate"
        ),
        "actual_scanned_pdf_candidate": item.get("scanned_pdf_candidate"),
        "scanned_match": scanned_match,
        "expected_ocr_performed": case.get("expected_ocr_performed"),
        "actual_ocr_performed": item.get("ocr_performed"),
        "ocr_performed_match": ocr_performed_match,
        "expected_ocr_succeeded": case.get("expected_ocr_succeeded"),
        "actual_ocr_succeeded": item.get("ocr_succeeded"),
        "ocr_succeeded_match": ocr_succeeded_match,
        "total_pages": item.get("total_pages"),
        "pages_with_text": pages_with_text,
        "pages_without_text": pages_without_text,
        "extracted_chars": extracted_chars,
        "pages_with_text_pass": pages_with_text_pass,
        "pages_without_text_pass": pages_without_text_pass,
        "extracted_chars_pass": extracted_chars_pass,
        "retrieval_query": retrieval_result["retrieval_query"],
        "expected_retrieval_filename": retrieval_result[
            "expected_retrieval_filename"
        ],
        "retrieval_hit": retrieval_result["retrieval_hit"],
        "retrieval_rank": retrieval_result["retrieval_rank"],
        "retrieved_sources": retrieval_result["retrieved_sources"],
        "pass": pass_result,
    }


def summarize(results: List[Dict[str, Any]], report: Dict[str, Any]) -> Dict[str, Any]:
    total = len(results)
    passing = sum(1 for item in results if item["pass"])

    pdf_results = report.get("pdf_detection_results", [])
    scanned_candidates = [
        item for item in pdf_results if item.get("scanned_pdf_candidate")
    ]
    ocr_performed = [
        item for item in pdf_results if item.get("ocr_performed")
    ]
    ocr_succeeded = [
        item for item in pdf_results if item.get("ocr_succeeded")
    ]
    retrieval_hits = sum(1 for item in results if item["retrieval_hit"])

    return {
        "total_cases": total,
        "passing_count": passing,
        "pass_rate": round(passing / total, 4) if total else 0,
        "pdf_files_checked": len(pdf_results),
        "scanned_pdf_candidates": len(scanned_candidates),
        "pdfs_with_ocr_performed": len(ocr_performed),
        "pdfs_with_ocr_succeeded": len(ocr_succeeded),
        "retrieval_hit_count": retrieval_hits,
        "retrieval_hit_rate": round(retrieval_hits / total, 4) if total else 0,
        "loaded_documents": report.get("loaded_documents", 0),
        "skipped_empty_documents": report.get("skipped_empty_documents", 0),
        "prd_pass": passing == total,
    }


def write_csv(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    CSV_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "case_id",
        "filename",
        "found",
        "expected_status",
        "actual_status",
        "status_match",
        "expected_scanned_pdf_candidate",
        "actual_scanned_pdf_candidate",
        "scanned_match",
        "expected_ocr_performed",
        "actual_ocr_performed",
        "ocr_performed_match",
        "expected_ocr_succeeded",
        "actual_ocr_succeeded",
        "ocr_succeeded_match",
        "total_pages",
        "pages_with_text",
        "pages_without_text",
        "extracted_chars",
        "pages_with_text_pass",
        "pages_without_text_pass",
        "extracted_chars_pass",
        "retrieval_query",
        "expected_retrieval_filename",
        "retrieval_hit",
        "retrieval_rank",
        "retrieved_sources",
        "pass",
        "total_cases",
        "passing_count",
        "pass_rate",
        "pdf_files_checked",
        "scanned_pdf_candidates",
        "pdfs_with_ocr_performed",
        "pdfs_with_ocr_succeeded",
        "retrieval_hit_count",
        "retrieval_hit_rate",
        "loaded_documents",
        "skipped_empty_documents",
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
        "# PDF Ingestion and OCR Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: PDF Ingestion / OCR Extraction / Retrieval",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passing cases: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
        f"- PDF files checked: {summary['pdf_files_checked']}",
        f"- Scanned PDF candidates: {summary['scanned_pdf_candidates']}",
        f"- PDFs with OCR performed: {summary['pdfs_with_ocr_performed']}",
        f"- PDFs with OCR succeeded: {summary['pdfs_with_ocr_succeeded']}",
        f"- Retrieval hit rate: {summary['retrieval_hit_rate']}",
        f"- Loaded documents: {summary['loaded_documents']}",
        f"- Skipped empty documents: {summary['skipped_empty_documents']}",
        f"- PRD pass: {summary['prd_pass']}",
        "",
        "## Method",
        "",
        "This evaluation reads the ingestion diagnostic report generated by:",
        "",
        "    python scripts/ingest.py",
        "",
        "It verifies that:",
        "",
        "- text-based PDFs are loaded",
        "- scanned/image-only PDFs are processed with OCR",
        "- OCR-extracted text is written to the vector store",
        "- OCR-extracted text can be retrieved",
        "",
        "## Case Results",
        "",
    ]

    for result in results:
        lines.extend(
            [
                f"### {result['case_id']}",
                "",
                f"- Filename: {result['filename']}",
                f"- Found: {result['found']}",
                f"- Expected status: {result['expected_status']}",
                f"- Actual status: {result['actual_status']}",
                f"- Scanned PDF candidate: {result['actual_scanned_pdf_candidate']}",
                f"- OCR performed: {result['actual_ocr_performed']}",
                f"- OCR succeeded: {result['actual_ocr_succeeded']}",
                f"- Pages with text: {result['pages_with_text']}",
                f"- Pages without text: {result['pages_without_text']}",
                f"- Extracted characters: {result['extracted_chars']}",
                f"- Retrieval hit: {result['retrieval_hit']}",
                f"- Retrieval rank: {result['retrieval_rank']}",
                f"- Pass: {result['pass']}",
                "",
            ]
        )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    report = load_ingestion_report()

    print(f"Loaded ingestion report: {REPORT_JSON_PATH}")
    print(f"Total PDF/OCR eval cases: {len(EXPECTED_CASES)}")
    print()

    results = []

    for index, case in enumerate(EXPECTED_CASES, start=1):
        print(f"[{index}/{len(EXPECTED_CASES)}] {case['case_id']}")

        result = evaluate_case(case, report)
        results.append(result)

        status = "✅" if result["pass"] else "❌"
        print(
            f"  {status} pass={result['pass']}, "
            f"status={result['actual_status']}, "
            f"ocr_performed={result['actual_ocr_performed']}, "
            f"ocr_succeeded={result['actual_ocr_succeeded']}, "
            f"retrieval_hit={result['retrieval_hit']}, "
            f"retrieval_rank={result['retrieval_rank']}"
        )

    summary = summarize(results, report)

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("PDF/OCR INGESTION EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:              {summary['total_cases']}")
    print(f"  Passing cases:            {summary['passing_count']}")
    print(f"  Pass rate:                {summary['pass_rate']}")
    print(f"  PDF files checked:        {summary['pdf_files_checked']}")
    print(f"  Scanned PDF candidates:   {summary['scanned_pdf_candidates']}")
    print(f"  PDFs with OCR performed:  {summary['pdfs_with_ocr_performed']}")
    print(f"  PDFs with OCR succeeded:  {summary['pdfs_with_ocr_succeeded']}")
    print(f"  Retrieval hit rate:       {summary['retrieval_hit_rate']}")
    print(f"  Loaded documents:         {summary['loaded_documents']}")
    print(f"  Skipped empty documents:  {summary['skipped_empty_documents']}")
    print(f"  PRD Status:               {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
