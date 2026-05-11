import csv
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.rag.pii import redact_pii


OUTPUT_DIR = PROJECT_ROOT / "reports" / "evaluations"
TODAY = time.strftime("%Y-%m-%d")
CSV_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_pii_redaction_eval.csv"
MD_REPORT_PATH = OUTPUT_DIR / f"{TODAY}_pii_redaction_eval.md"


PII_CASES = [
    {
        "case_id": "email_redaction",
        "input_text": "My email is ziwei@example.com.",
        "forbidden_values": ["ziwei@example.com"],
        "expected_placeholders": ["[EMAIL]"],
    },
    {
        "case_id": "phone_redaction",
        "input_text": "My phone number is 13812345678.",
        "forbidden_values": ["13812345678"],
        "expected_placeholders": ["[PHONE]"],
    },
    {
        "case_id": "api_key_redaction",
        "input_text": "The api_key=abc123secret should not be logged.",
        "forbidden_values": ["abc123secret"],
        "expected_placeholders": ["[REDACTED_SECRET]"],
    },
    {
        "case_id": "token_redaction",
        "input_text": "access_token=tok_live_123456789 must be hidden.",
        "forbidden_values": ["tok_live_123456789"],
        "expected_placeholders": ["[REDACTED_SECRET]"],
    },
    {
        "case_id": "secret_redaction",
        "input_text": "secret=my_private_secret_value should be redacted.",
        "forbidden_values": ["my_private_secret_value"],
        "expected_placeholders": ["[REDACTED_SECRET]"],
    },
    {
        "case_id": "id_number_redaction",
        "input_text": "My ID number is 310101199001011234.",
        "forbidden_values": ["310101199001011234"],
        "expected_placeholders": ["[ID_NUMBER]"],
    },
    {
        "case_id": "mixed_pii_redaction",
        "input_text": (
            "Contact me at test.user@example.com or 13800138000. "
            "api_key=test_secret_123 should not appear."
        ),
        "forbidden_values": [
            "test.user@example.com",
            "13800138000",
            "test_secret_123",
        ],
        "expected_placeholders": [
            "[EMAIL]",
            "[PHONE]",
            "[REDACTED_SECRET]",
        ],
    },
]


def contains_case_insensitive(text: str, value: str) -> bool:
    return value.lower() in text.lower()


def evaluate_case(case: Dict[str, Any]) -> Dict[str, Any]:
    input_text = case["input_text"]
    redacted_text = redact_pii(input_text)

    forbidden_values = case.get("forbidden_values", [])
    expected_placeholders = case.get("expected_placeholders", [])

    leaked_values = [
        value for value in forbidden_values
        if contains_case_insensitive(redacted_text, value)
    ]

    missing_placeholders = [
        placeholder for placeholder in expected_placeholders
        if placeholder not in redacted_text
    ]

    forbidden_clean = len(leaked_values) == 0
    placeholders_present = len(missing_placeholders) == 0

    pass_result = forbidden_clean and placeholders_present

    return {
        "case_id": case["case_id"],
        "input_text": input_text,
        "redacted_text": redacted_text,
        "forbidden_values": "|".join(forbidden_values),
        "expected_placeholders": "|".join(expected_placeholders),
        "leaked_values": "|".join(leaked_values),
        "missing_placeholders": "|".join(missing_placeholders),
        "forbidden_clean": forbidden_clean,
        "placeholders_present": placeholders_present,
        "pass": pass_result,
    }


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    passing = sum(1 for item in results if item["pass"])
    forbidden_clean = sum(1 for item in results if item["forbidden_clean"])
    placeholders_present = sum(
        1 for item in results if item["placeholders_present"]
    )

    return {
        "total_cases": total,
        "passing_count": passing,
        "pass_rate": round(passing / total, 4) if total else 0,
        "forbidden_clean_count": forbidden_clean,
        "forbidden_clean_rate": round(forbidden_clean / total, 4) if total else 0,
        "placeholder_present_count": placeholders_present,
        "placeholder_present_rate": round(placeholders_present / total, 4)
        if total
        else 0,
        "prd_pass": passing == total,
    }


def write_csv(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    CSV_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "case_id",
        "input_text",
        "redacted_text",
        "forbidden_values",
        "expected_placeholders",
        "leaked_values",
        "missing_placeholders",
        "forbidden_clean",
        "placeholders_present",
        "pass",
        "total_cases",
        "passing_count",
        "pass_rate",
        "forbidden_clean_count",
        "forbidden_clean_rate",
        "placeholder_present_count",
        "placeholder_present_rate",
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
        "# PII Redaction Evaluation Report",
        "",
        f"Date: {TODAY}",
        "Project: AIA RAG Case Study Service",
        "Evaluation Type: PII Redaction Evaluation",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passing cases: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
        f"- Forbidden clean rate: {summary['forbidden_clean_rate']}",
        f"- Placeholder present rate: {summary['placeholder_present_rate']}",
        f"- PRD pass: {summary['prd_pass']}",
        "",
        "## Method",
        "",
        "Each case sends text containing one or more PII-like values into the redaction function.",
        "The evaluator checks that raw sensitive values are removed and expected placeholders are present.",
        "",
        "## Case Results",
        "",
    ]

    for result in results:
        lines.extend(
            [
                f"### {result['case_id']}",
                "",
                f"- Input: {result['input_text']}",
                f"- Redacted: {result['redacted_text']}",
                f"- Forbidden clean: {result['forbidden_clean']}",
                f"- Placeholders present: {result['placeholders_present']}",
                f"- Leaked values: {result['leaked_values'] or 'None'}",
                f"- Missing placeholders: {result['missing_placeholders'] or 'None'}",
                f"- Pass: {result['pass']}",
                "",
            ]
        )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    print(f"Total PII redaction eval cases: {len(PII_CASES)}")
    print()

    results = []

    for index, case in enumerate(PII_CASES, start=1):
        result = evaluate_case(case)
        results.append(result)

        status = "✅" if result["pass"] else "❌"
        print(
            f"[{index}/{len(PII_CASES)}] {case['case_id']} "
            f"{status} pass={result['pass']}, "
            f"forbidden_clean={result['forbidden_clean']}, "
            f"placeholders_present={result['placeholders_present']}"
        )

        if result["leaked_values"]:
            print(f"  Leaked values: {result['leaked_values']}")

        if result["missing_placeholders"]:
            print(f"  Missing placeholders: {result['missing_placeholders']}")

    summary = summarize(results)

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("PII REDACTION EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:              {summary['total_cases']}")
    print(f"  Passing cases:            {summary['passing_count']}")
    print(f"  Pass rate:                {summary['pass_rate']}")
    print(f"  Forbidden clean rate:     {summary['forbidden_clean_rate']}")
    print(f"  Placeholder present rate: {summary['placeholder_present_rate']}")
    print(f"  PRD Status:               {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
