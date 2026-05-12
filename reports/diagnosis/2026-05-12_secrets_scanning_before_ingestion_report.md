# Optimization Report: Secrets Scanning Before Ingestion

Date: 2026-05-12  
Project: AIA RAG Case Study Service  
Report Type: Production Hardening Report  
Optimization Area: Ingestion Safety / Secrets Scanning / RAG Data Protection  
Related Components: `app/ingestion/secrets_scanner.py`, `scripts/ingest.py`, `scripts/evaluate_secrets_scan.py`

---

## 1. Purpose

This report documents the addition of secrets scanning before ingestion.

RAG systems can accidentally ingest sensitive credentials if raw documents contain API keys, access tokens, passwords, private keys, or secret configuration values. Once embedded into a vector store, these values may become harder to audit and remove.

This optimization adds a pre-ingestion secrets scan to reduce the risk of storing sensitive credentials in Chroma.

---

## 2. Change

Added:

    app/ingestion/secrets_scanner.py
    scripts/evaluate_secrets_scan.py

Enhanced:

    scripts/ingest.py
    configs/app.yaml

The scanner checks supported raw files before ingestion and generates reports under:

    reports/ingestion/secrets_scan_report.json
    reports/ingestion/secrets_scan_report.md

Configured behavior:

    secrets_scan:
      enabled: true
      fail_on_detected: false

Current mode is warning-only. It does not block ingestion unless `fail_on_detected` is set to true.

---

## 3. Detection Coverage

The scanner checks for secret-like patterns including:

- OpenAI-style API keys
- AWS access key IDs
- private key blocks
- generic API key assignments
- generic access token assignments
- generic secret assignments
- generic password assignments

Supported scanned file types include:

- `.txt`
- `.md`
- `.json`
- `.yaml`
- `.yml`
- `.env`
- `.csv`
- `.py`
- `.java`
- `.properties`
- `.ini`

---

## 4. Ignore Marker Support

A controlled ignore marker was added:

    secret-scan-ignore

This allows documentation examples to be explicitly ignored while still being recorded as ignored findings.

The scanner now distinguishes:

- active findings
- ignored findings

This avoids confusing reviewer-facing reports when safe example values are intentionally included in documentation.

---

## 5. Evaluation Result

Final command:

    python scripts/evaluate_secrets_scan.py

Expected final result:

    total_cases = 1
    passing_count = 1
    pass_rate = 1.0
    PRD Status = PASS

The evaluation validates that:

- actual secret-like values are detected
- safe policy text is not falsely flagged
- ignored example secrets are not counted as active findings
- ignored example secrets are still recorded in ignored findings

Output reports:

    reports/evaluations/2026-05-12_secrets_scan_eval.csv
    reports/evaluations/2026-05-12_secrets_scan_eval.md

---

## 6. Real Ingestion Validation

Final command:

    python scripts/ingest.py

Observed real ingestion result:

    Secrets scan findings = 0
    Findings count = 0
    Ignored findings count = 2
    Loaded documents = 10
    Generated chunks = 32
    Total chunks stored = 32
    Ingestion completed

The two ignored findings are documented example values in:

    data/raw/08_pii_redaction_spec_cn.txt

They are explicitly marked with:

    secret-scan-ignore

---

## 7. PRD / Production Impact

This optimization improves production readiness by adding a safety gate before documents enter the RAG index.

It reduces the risk of:

- embedding real credentials
- retrieving secret-like values
- leaking sensitive configuration through generated answers
- polluting the vector store with private tokens or keys

It complements the existing PII redaction and prompt injection defenses.

---

## 8. Limitations

Current limitations:

- The scanner is regex-based.
- It may still produce false positives or false negatives.
- It does not scan binary files deeply.
- It does not currently scan extracted OCR text before vector insertion.
- It does not integrate with enterprise secret scanning tools.
- It runs in warning-only mode by default.

---

## 9. Future Work

Future improvements may include:

- fail-on-secret mode in CI
- entropy-based secret detection
- integration with tools such as Gitleaks or TruffleHog
- OCR text secret scanning
- PDF/docx extracted text secret scanning before chunking
- per-finding allowlist file
- severity-based blocking policy
- ingestion quarantine workflow

---

## 10. Conclusion

Secrets Scanning Before Ingestion is completed.

Final status:

    PASS

The project now scans raw files before ingestion, reports active and ignored findings, supports controlled ignore markers, and prevents documentation examples from being misclassified as active secret findings.
