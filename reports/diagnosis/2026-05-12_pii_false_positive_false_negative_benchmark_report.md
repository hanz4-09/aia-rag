# Evaluation Report: PII False Positive / False Negative Benchmark

Date: 2026-05-12  
Project: AIA RAG Case Study Service  
Report Type: Privacy Evaluation Enhancement  
Evaluation Area: PII Redaction / False Positive / False Negative Benchmark  
Related Components: `app/rag/pii.py`, `scripts/evaluate_pii_redaction.py`

---

## 1. Purpose

This report documents the enhancement of the PII redaction evaluation.

The project already had basic PII redaction and a formal PII evaluation. This enhancement expands the evaluation to cover both:

1. true-positive / false-negative cases, where sensitive values must be redacted
2. false-positive cases, where normal non-sensitive text must not be over-redacted

---

## 2. Evaluation Scope

The enhanced benchmark covers 13 cases.

True-positive cases:

- email redaction
- phone number redaction
- API key value redaction
- access token value redaction
- secret value redaction
- ID number redaction
- mixed PII redaction

False-positive cases:

- normal years should not be treated as ID numbers
- normal latency numbers should not be treated as phone numbers
- API Key policy concept should not be treated as a secret value
- access token policy concept should not be treated as a secret value
- employee policy numbers should not be treated as phone numbers
- technical endpoint paths should not be treated as email or secrets

---

## 3. Evaluation Method

Script:

    scripts/evaluate_pii_redaction.py

The evaluator checks:

1. Raw sensitive values do not remain after redaction.
2. Expected placeholders appear for true-positive PII cases.
3. Unexpected placeholders do not appear for false-positive cases.
4. Non-sensitive text remains unchanged in false-positive cases.

Outputs:

    reports/evaluations/2026-05-12_pii_redaction_eval.csv
    reports/evaluations/2026-05-12_pii_redaction_eval.md

---

## 4. Final Result

Final command:

    python scripts/evaluate_pii_redaction.py

Final result:

    total_cases = 13
    passing_count = 13
    pass_rate = 1.0
    true_positive_pass_rate = 1.0
    false_positive_clean_rate = 1.0
    forbidden_clean_rate = 1.0
    placeholder_present_rate = 1.0
    unexpected_placeholder_clean_rate = 1.0
    PRD Status = PASS

---

## 5. PRD Impact

The PRD requires basic PII handling.

Before this enhancement, PII redaction was formally evaluated for sensitive-value removal and placeholder presence.

After this enhancement, the evaluation also verifies that normal policy, technical, and numeric text is not over-redacted.

This strengthens the privacy requirement by checking both false negatives and false positives.

---

## 6. Limitations

Current PII handling is still rule-based.

Known limitations:

- The benchmark is still small.
- It does not cover names, addresses, passport numbers, bank card numbers, or other locale-specific identifiers.
- It does not calculate entity-level precision, recall, or F1.
- It does not use ML-based named entity recognition.
- It does not yet perform full end-to-end answer/log redaction validation through the `/chat` API.

---

## 7. Future Work

Future improvements may include:

- richer PII pattern coverage
- larger false-positive and false-negative benchmark set
- multilingual PII detection
- entity-level precision / recall / F1 metrics
- end-to-end API-level PII redaction tests
- privacy policy integration for logs and session memory

---

## 8. Conclusion

PII False Positive / False Negative Benchmark is completed.

Final status:

    PASS

The project now has stronger reproducible privacy evaluation coverage for both missed redaction and over-redaction risk.
