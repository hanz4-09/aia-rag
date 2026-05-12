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
    # True-positive / false-negative cases:
    # These inputs contain sensitive values and must be redacted.
    {
        "case_id": "email_redaction",
        "case_type": "true_positive",
        "input_text": "My email is ziwei@example.com.",
        "forbidden_values": ["ziwei@example.com"],
        "expected_placeholders": ["[EMAIL]"],
        "unexpected_placeholders": [],
    },
    {
        "case_id": "phone_redaction",
        "case_type": "true_positive",
        "input_text": "My phone number is 13812345678.",
        "forbidden_values": ["13812345678"],
        "expected_placeholders": ["[PHONE]"],
        "unexpected_placeholders": [],
    },
    {
        "case_id": "api_key_redaction",
        "case_type": "true_positive",
        "input_text": "The api_key=abc123secret should not be logged.",
        "forbidden_values": ["abc123secret"],
        "expected_placeholders": ["[REDACTED_SECRET]"],
        "unexpected_placeholders": [],
    },
    {
        "case_id": "token_redaction",
        "case_type": "true_positive",
        "input_text": "access_token=tok_live_123456789 must be hidden.",
        "forbidden_values": ["tok_live_123456789"],
        "expected_placeholders": ["[REDACTED_SECRET]"],
        "unexpected_placeholders": [],
    },
    {
        "case_id": "secret_redaction",
        "case_type": "true_positive",
        "input_text": "secret=my_private_secret_value should be redacted.",
        "forbidden_values": ["my_private_secret_value"],
        "expected_placeholders": ["[REDACTED_SECRET]"],
        "unexpected_placeholders": [],
    },
    {
        "case_id": "id_number_redaction",
        "case_type": "true_positive",
        "input_text": "My ID number is 310101199001011234.",
        "forbidden_values": ["310101199001011234"],
        "expected_placeholders": ["[ID_NUMBER]"],
        "unexpected_placeholders": [],
    },
    {
        "case_id": "mixed_pii_redaction",
        "case_type": "true_positive",
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
        "unexpected_placeholders": [],
    },

    # False-positive cases:
    # These inputs do not contain raw PII values and should not be over-redacted.
    {
        "case_id": "normal_year_not_id",
        "case_type": "false_positive",
        "input_text": "The retention policy was updated in 2026 and reviewed in 2025.",
        "forbidden_values": [],
        "expected_placeholders": [],
        "unexpected_placeholders": ["[ID_NUMBER]", "[PHONE]", "[EMAIL]", "[REDACTED_SECRET]"],
    },
    {
        "case_id": "normal_latency_numbers_not_phone",
        "case_type": "false_positive",
        "input_text": "The p50 latency is 751 ms and the p95 latency is 3355 ms.",
        "forbidden_values": [],
        "expected_placeholders": [],
        "unexpected_placeholders": ["[PHONE]", "[ID_NUMBER]"],
    },
    {
        "case_id": "api_key_policy_concept_not_secret",
        "case_type": "false_positive",
        "input_text": "API Key leakage must be reported within 24 hours.",
        "forbidden_values": [],
        "expected_placeholders": [],
        "unexpected_placeholders": ["[REDACTED_SECRET]"],
    },
    {
        "case_id": "token_policy_concept_not_secret",
        "case_type": "false_positive",
        "input_text": "Access token values must not be stored in plain text logs.",
        "forbidden_values": [],
        "expected_placeholders": [],
        "unexpected_placeholders": ["[REDACTED_SECRET]"],
    },
    {
        "case_id": "employee_policy_numbers_not_phone",
        "case_type": "false_positive",
        "input_text": "Employees must complete 2 trainings within 30 days.",
        "forbidden_values": [],
        "expected_placeholders": [],
        "unexpected_placeholders": ["[PHONE]", "[ID_NUMBER]"],
    },
    {
        "case_id": "technical_endpoint_not_email",
        "case_type": "false_positive",
        "input_text": "The service exposes /health and /chat endpoints.",
        "forbidden_values": [],
        "expected_placeholders": [],
        "unexpected_placeholders": ["[EMAIL]", "[REDACTED_SECRET]"],
    },
]


def contains_case_insensitive(text: str, value: str) -> bool:
    return value.lower() in text.lower()


def evaluate_case(case: Dict[str, Any]) -> Dict[str, Any]:
    input_text = case["input_text"]
    redacted_text = redact_pii(input_text)

    forbidden_values = case.get("forbidden_values", [])
    expected_placeholders = case.get("expected_placeholders", [])
    unexpected_placeholders = case.get("unexpected_placeholders", [])
    case_type = case.get("case_type", "true_positive")

    leaked_values = [
        value for value in forbidden_values
        if contains_case_insensitive(redacted_text, value)
    ]

    missing_placeholders = [
        placeholder for placeholder in expected_placeholders
        if placeholder not in redacted_text
    ]

    unexpected_present = [
        placeholder for placeholder in unexpected_placeholders
        if placeholder in redacted_text
    ]

    forbidden_clean = len(leaked_values) == 0
    placeholders_present = len(missing_placeholders) == 0
    false_positive_clean = len(unexpected_present) == 0

    if case_type == "true_positive":
        pass_result = forbidden_clean and placeholders_present
    elif case_type == "false_positive":
        pass_result = false_positive_clean and redacted_text == input_text
    else:
        pass_result = forbidden_clean and placeholders_present and false_positive_clean

    return {
        "case_id": case["case_id"],
        "case_type": case_type,
        "input_text": input_text,
        "redacted_text": redacted_text,
        "forbidden_values": "|".join(forbidden_values),
        "expected_placeholders": "|".join(expected_placeholders),
        "unexpected_placeholders": "|".join(unexpected_placeholders),
        "leaked_values": "|".join(leaked_values),
        "missing_placeholders": "|".join(missing_placeholders),
        "unexpected_present": "|".join(unexpected_present),
        "forbidden_clean": forbidden_clean,
        "placeholders_present": placeholders_present,
        "false_positive_clean": false_positive_clean,
        "redacted_changed": redacted_text != input_text,
        "pass": pass_result,
    }


def rate(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    passing = sum(1 for item in results if item["pass"])

    true_positive_cases = [
        item for item in results if item["case_type"] == "true_positive"
    ]
    false_positive_cases = [
        item for item in results if item["case_type"] == "false_positive"
    ]

    true_positive_total = len(true_positive_cases)
    false_positive_total = len(false_positive_cases)

    true_positive_passing = sum(1 for item in true_positive_cases if item["pass"])
    false_positive_passing = sum(1 for item in false_positive_cases if item["pass"])

    forbidden_clean = sum(1 for item in results if item["forbidden_clean"])
    placeholders_present = sum(
        1 for item in true_positive_cases if item["placeholders_present"]
    )
    false_positive_clean = sum(
        1 for item in false_positive_cases if item["false_positive_clean"]
    )

    return {
        "total_cases": total,
        "passing_count": passing,
        "pass_rate": rate(passing, total),
        "true_positive_cases": true_positive_total,
        "true_positive_passing": true_positive_passing,
        "true_positive_pass_rate": rate(true_positive_passing, true_positive_total),
        "false_positive_cases": false_positive_total,
        "false_positive_passing": false_positive_passing,
        "false_positive_clean_rate": rate(false_positive_passing, false_positive_total),
        "forbidden_clean_count": forbidden_clean,
        "forbidden_clean_rate": rate(forbidden_clean, total),
        "placeholder_present_count": placeholders_present,
        "placeholder_present_rate": rate(placeholders_present, true_positive_total),
        "unexpected_placeholder_clean_count": false_positive_clean,
        "unexpected_placeholder_clean_rate": rate(
            false_positive_clean,
            false_positive_total,
        ),
        "prd_pass": passing == total,
    }


def write_csv(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    CSV_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "row_type",
        "case_id",
        "case_type",
        "input_text",
        "redacted_text",
        "forbidden_values",
        "expected_placeholders",
        "unexpected_placeholders",
        "leaked_values",
        "missing_placeholders",
        "unexpected_present",
        "forbidden_clean",
        "placeholders_present",
        "false_positive_clean",
        "redacted_changed",
        "pass",
        "total_cases",
        "passing_count",
        "pass_rate",
        "true_positive_cases",
        "true_positive_passing",
        "true_positive_pass_rate",
        "false_positive_cases",
        "false_positive_passing",
        "false_positive_clean_rate",
        "forbidden_clean_count",
        "forbidden_clean_rate",
        "placeholder_present_count",
        "placeholder_present_rate",
        "unexpected_placeholder_clean_count",
        "unexpected_placeholder_clean_rate",
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
        "Evaluation Type: PII Redaction / False Positive / False Negative Benchmark",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Passing cases: {summary['passing_count']}",
        f"- Pass rate: {summary['pass_rate']}",
        f"- True-positive cases: {summary['true_positive_cases']}",
        f"- True-positive pass rate: {summary['true_positive_pass_rate']}",
        f"- False-positive cases: {summary['false_positive_cases']}",
        f"- False-positive clean rate: {summary['false_positive_clean_rate']}",
        f"- Forbidden clean rate: {summary['forbidden_clean_rate']}",
        f"- Placeholder present rate: {summary['placeholder_present_rate']}",
        f"- Unexpected placeholder clean rate: {summary['unexpected_placeholder_clean_rate']}",
        f"- PRD pass: {summary['prd_pass']}",
        "",
        "## Method",
        "",
        "The evaluation includes two case types:",
        "",
        "1. True-positive cases: inputs contain sensitive values and must be redacted.",
        "2. False-positive cases: inputs do not contain raw PII and should not be over-redacted.",
        "",
        "The evaluator checks that raw sensitive values are removed, expected placeholders are present,",
        "and non-sensitive policy or technical text is not incorrectly redacted.",
        "",
        "## Case Results",
        "",
    ]

    for result in results:
        lines.extend(
            [
                f"### {result['case_id']}",
                "",
                f"- Case type: {result['case_type']}",
                f"- Input: {result['input_text']}",
                f"- Redacted: {result['redacted_text']}",
                f"- Forbidden clean: {result['forbidden_clean']}",
                f"- Placeholders present: {result['placeholders_present']}",
                f"- False-positive clean: {result['false_positive_clean']}",
                f"- Redacted changed: {result['redacted_changed']}",
                f"- Leaked values: {result['leaked_values'] or 'None'}",
                f"- Missing placeholders: {result['missing_placeholders'] or 'None'}",
                f"- Unexpected placeholders: {result['unexpected_present'] or 'None'}",
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
            f"type={result['case_type']}, "
            f"forbidden_clean={result['forbidden_clean']}, "
            f"placeholders_present={result['placeholders_present']}, "
            f"false_positive_clean={result['false_positive_clean']}"
        )

        if result["leaked_values"]:
            print(f"  Leaked values: {result['leaked_values']}")

        if result["missing_placeholders"]:
            print(f"  Missing placeholders: {result['missing_placeholders']}")

        if result["unexpected_present"]:
            print(f"  Unexpected placeholders: {result['unexpected_present']}")

    summary = summarize(results)

    write_csv(results, summary)
    write_markdown(results, summary)

    print()
    print("=" * 60)
    print("PII REDACTION EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total cases:                       {summary['total_cases']}")
    print(f"  Passing cases:                     {summary['passing_count']}")
    print(f"  Pass rate:                         {summary['pass_rate']}")
    print(f"  True-positive pass rate:           {summary['true_positive_pass_rate']}")
    print(f"  False-positive clean rate:         {summary['false_positive_clean_rate']}")
    print(f"  Forbidden clean rate:              {summary['forbidden_clean_rate']}")
    print(f"  Placeholder present rate:          {summary['placeholder_present_rate']}")
    print(f"  Unexpected placeholder clean rate: {summary['unexpected_placeholder_clean_rate']}")
    print(f"  PRD Status:                        {'✅ PASS' if summary['prd_pass'] else '❌ FAIL'}")
    print("=" * 60)
    print()
    print(f"CSV report: {CSV_REPORT_PATH}")
    print(f"Markdown report: {MD_REPORT_PATH}")


if __name__ == "__main__":
    main()
