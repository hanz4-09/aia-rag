import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Sequence


@dataclass
class SecretFinding:
    filename: str
    relative_path: str
    pattern_name: str
    line_number: int
    matched_preview: str
    severity: str


SECRET_PATTERNS = [
    {
        "name": "openai_api_key",
        "regex": r"sk-[A-Za-z0-9_\-]{20,}",
        "severity": "high",
    },
    {
        "name": "aws_access_key_id",
        "regex": r"AKIA[0-9A-Z]{16}",
        "severity": "high",
    },
    {
        "name": "private_key_block",
        "regex": r"-----BEGIN\s+(RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE KEY-----",
        "severity": "high",
    },
    {
        "name": "generic_api_key_assignment",
        "regex": r"(?i)\b(api[_-]?key|apikey)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}",
        "severity": "medium",
    },
    {
        "name": "generic_access_token_assignment",
        "regex": r"(?i)\b(access[_-]?token|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{12,}",
        "severity": "medium",
    },
    {
        "name": "generic_secret_assignment",
        "regex": r"(?i)\b(secret|client[_-]?secret)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{12,}",
        "severity": "medium",
    },
    {
        "name": "generic_password_assignment",
        "regex": r"(?i)\b(password|passwd|pwd)\s*[:=]\s*['\"]?[^'\"\s]{8,}",
        "severity": "medium",
    },
]


SECRET_SCAN_IGNORE_MARKER = "secret-scan-ignore"


SUPPORTED_SCAN_SUFFIXES = {
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".env",
    ".csv",
    ".py",
    ".java",
    ".properties",
    ".ini",
}


def mask_secret(value: str, visible_prefix: int = 6, visible_suffix: int = 4) -> str:
    clean_value = value.strip()

    if len(clean_value) <= visible_prefix + visible_suffix:
        return "[REDACTED_SECRET]"

    return (
        clean_value[:visible_prefix]
        + "...[REDACTED]..."
        + clean_value[-visible_suffix:]
    )


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def scan_text_file(path: Path, root_dir: Path) -> Dict[str, List[SecretFinding]]:
    findings: List[SecretFinding] = []
    ignored_findings: List[SecretFinding] = []
    ignored_findings: List[SecretFinding] = []
    text = _safe_read_text(path)
    relative_path = str(path.relative_to(root_dir))

    for line_number, line in enumerate(text.splitlines(), start=1):
        ignore_line = SECRET_SCAN_IGNORE_MARKER in line

        for pattern in SECRET_PATTERNS:
            match = re.search(pattern["regex"], line)
            if not match:
                continue

            finding = SecretFinding(
                filename=path.name,
                relative_path=relative_path,
                pattern_name=pattern["name"],
                line_number=line_number,
                matched_preview=mask_secret(match.group(0)),
                severity=pattern["severity"],
            )

            if ignore_line:
                ignored_findings.append(finding)
            else:
                findings.append(finding)

    return {
        "findings": findings,
        "ignored_findings": ignored_findings,
    }


def scan_directory(
    root_dir: str | Path,
    supported_suffixes: Sequence[str] | None = None,
) -> Dict:
    root = Path(root_dir)
    suffixes = set(supported_suffixes or SUPPORTED_SCAN_SUFFIXES)

    scanned_files = 0
    skipped_files = 0
    findings: List[SecretFinding] = []
    ignored_findings: List[SecretFinding] = []

    if not root.exists():
        return {
            "root_dir": str(root),
            "scanned_files": 0,
            "skipped_files": 0,
            "findings_count": 0,
            "ignored_findings_count": 0,
            "high_severity_count": 0,
            "medium_severity_count": 0,
            "findings": [],
            "ignored_findings": [],
        }

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in suffixes:
            skipped_files += 1
            continue

        scanned_files += 1
        file_scan_result = scan_text_file(path, root)
        findings.extend(file_scan_result["findings"])
        ignored_findings.extend(file_scan_result["ignored_findings"])

    high_count = sum(1 for item in findings if item.severity == "high")
    medium_count = sum(1 for item in findings if item.severity == "medium")

    return {
        "root_dir": str(root),
        "scanned_files": scanned_files,
        "skipped_files": skipped_files,
        "findings_count": len(findings),
        "ignored_findings_count": len(ignored_findings),
        "high_severity_count": high_count,
        "medium_severity_count": medium_count,
        "findings": [asdict(item) for item in findings],
        "ignored_findings": [asdict(item) for item in ignored_findings],
    }


def write_scan_reports(report: Dict, json_path: str | Path, markdown_path: str | Path) -> None:
    json_output = Path(json_path)
    markdown_output = Path(markdown_path)

    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)

    json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# Secrets Scan Report",
        "",
        "Project: AIA RAG Case Study Service",
        "Report Type: Ingestion Safety / Secrets Scan",
        "",
        "## Summary",
        "",
        f"- Root directory: {report['root_dir']}",
        f"- Scanned files: {report['scanned_files']}",
        f"- Skipped files: {report['skipped_files']}",
        f"- Findings count: {report['findings_count']}",
        f"- Ignored findings count: {report.get('ignored_findings_count', 0)}",
        f"- High severity count: {report['high_severity_count']}",
        f"- Medium severity count: {report['medium_severity_count']}",
        "",
        "## Findings",
        "",
    ]

    if not report["findings"]:
        lines.append("No unignored secret-like patterns were detected.")
    else:
        for finding in report["findings"]:
            lines.extend(
                [
                    f"### {finding['relative_path']}:{finding['line_number']}",
                    "",
                    f"- Pattern: {finding['pattern_name']}",
                    f"- Severity: {finding['severity']}",
                    f"- Matched preview: `{finding['matched_preview']}`",
                    "",
                ]
            )

    lines.extend(
        [
            "",
            "## Ignored Findings",
            "",
        ]
    )

    ignored_findings = report.get("ignored_findings", [])

    if not ignored_findings:
        lines.append("No findings were ignored.")
    else:
        for finding in ignored_findings:
            lines.extend(
                [
                    f"### {finding['relative_path']}:{finding['line_number']}",
                    "",
                    f"- Pattern: {finding['pattern_name']}",
                    f"- Severity: {finding['severity']}",
                    f"- Matched preview: `{finding['matched_preview']}`",
                    f"- Ignore marker: `{SECRET_SCAN_IGNORE_MARKER}`",
                    "",
                ]
            )

    markdown_output.write_text("\n".join(lines), encoding="utf-8")
