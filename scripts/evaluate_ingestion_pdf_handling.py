import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

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
        "min_pages_with_text": 1,
        "min_extracted_chars": 20,
    },
    {
        "case_id": "scanned_pdf_detected_and_skipped",
        "filename": "99_scanned_pdf_detection_test.pdf",
        "expected_status": "skipped_no_extractable_text",
        "expected_scanned_pdf_candidate": True,
        "expected_ocr_performed": False,
        "min_pages_without_text": 1,
        "max_extracted_chars": 0,
    },
]


def load_ingestion_report() -> Dict[str, Any]:
    if not REPORT_JSON_PATH.exists():
        raise FileNotFoundError(
            f"Ingestion PDF detection report not found: {REPORT_JSON_PATH}. "
            "Run `python scripts/ingest.py` first."
        )

    with REPORT_JSON_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_pdf_result(report: Dict[str, Any], filename: str) -> Dict[str, Any]:
    for item in report.get("pdf_detection_results", []):
        if item.get("filename") == filename:
            return item
    return {}


def evaluate_case(case: Dict[str, Any], report: Dict[str, Any]) -> Dict[str, Any]:
    item = find_pdf_result(report, case["filename"])

    found = bool(item)

    status_match = item.get("status") == case.get("expected_status")
    scanned_match = (
        item.get("scanned_pdf_candidate")
        == case.get("expected_scanned_pdf_candidate")
    )
    ocr_match = item.get("ocr_performed") == case.get("expected_ocr_performed")

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

    extracted_chars_min_pass = True
    if "min_extracted_chars" in case:
        extracted_chars_min_pass = extracted_chars >= case["min_extracted_chars"]

    extracted_chars_max_pass = True
    if "max_extracted_chars" in case:
        extracted_chars_max_pass = extracted_chars <= case["max_extracted_chars"]

    pass_result = all(
        [
            found,
            status_match,
            scanned_match,
            ocr_match,
            pages_with_text_pass,
            pages_without_text_pass,
            extracted_chars_min_pass,
            extracted_chars_max_pass,
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
        "ocr_match": ocr_match,
        "total_pages": item.get("total_pages"),
        "pages_with_text": pages_with_text,
        "pages_without_text": pages_without_text,
        "extracted_chars": extracted_chars,
        "pages_with_text_pass": pages_with_text_pass,
        "pages_without_text_pass": pages_without_text_pass,
        "extracted_chars_min_pass": extracted_chars_min_pass,
        "extracted_chars_max_pass": extracted_chars_max_pass,
        "pass": pass_result,
    }


def summarize(results: List[Dict[str, Any]], report: Dict[str, Any]) -> Dict[str, Any]:
    total = len(results)
    passing = sum(1 for item in results if item["pass"])

    pdf_results = report.get("pdf_detection_results", [])
    scanned_candidates = [
        item for item in pdf_results if item.get("scanned_pdf_candidate")
    ]

    return {
        "total_cases": total,
        "passing_count": passing,
        "pass_rate": round(passing / total, 4) if total else 0,
        "pdf_files_checked": len(pdf_results),
        "scanned_pdf_candidates": len(scanned_candidates),
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
        "ocr_match",
        "total_pages",
        "pages_with_text",
        "pages_without_text",
        "extracted_chars",
        "pages_with_text_pass",
        "pages_without_text_pass",
        "extracted_chars_min_pass",
        "extracted_chars_max_pass",
        "pass",
        "total_cases",
        "passing_count",
        "pass_rate",
        "pdf_files_checked",
        "scanned_pdf_candidates",
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
        "# PDF Ingestion Handling Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: PDF Ingestion / Scanned PDF Detection",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passing cases: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
        f"- PDF files checked: {summary['pdf_files_checked']}",
        f"- Scanned PDF candidates: {summary['scanned_pdf_candidates']}",
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
        "The evaluator checks that:",
        "",
        "- text-based PDFs are loaded",
        "- scanned/no-text PDFs are detected",
        "- scanned/no-text PDFs are skipped gracefully",
        "- OCR is explicitly marked as not performed",
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
                f"- Pages with text: {result['pages_with_text']}",
                f"- Pages without text: {result['pages_without_text']}",
                f"- Extracted characters: {result['extracted_chars']}",
                f"- Pass: {result['pass']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Notes",
            "",
            "OCR extraction is not implemented in this phase.",
            "This evaluation validates detection and graceful handling only.",
            "",
        ]
    )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    report = load_ingestion_report()

    print(f"Loaded ingestion report: {REPORT_JSON_PATH}")
    print(f"Total PDF eval cases: {len(EXPECTED_CASES)}")
    print()

    results = []

    for index, case in enumerate(EXPECTED_CASES, start=1):
        print(f"[{index}/{len(EXPECTED_CASES)}] {case['case_id']}")

        result = evaluate_case(case, report)
        results.append(result)

        status = "✅" if result["pass"] else "❌"
        print(
            f"  {status} pass={result['pass']}, "
            f"found={result['found']}, "
            f"status={result['actual_status']}, "
            f"scanned={result['actual_scanned_pdf_candidate']}, "
            f"ocr={result['actual_ocr_performed']}"
        )

    summary = summarize(results, report)

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("PDF INGESTION EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:             {summary['total_cases']}")
    print(f"  Passing cases:           {summary['passing_count']}")
    print(f"  Pass rate:               {summary['pass_rate']}")
    print(f"  PDF files checked:       {summary['pdf_files_checked']}")
    print(f"  Scanned PDF candidates:  {summary['scanned_pdf_candidates']}")
    print(f"  Loaded documents:        {summary['loaded_documents']}")
    print(f"  Skipped empty documents: {summary['skipped_empty_documents']}")
    print(f"  PRD Status:              {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
