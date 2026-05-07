import re


EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[-\s]?)?(?:\d{3,4}[-\s]?\d{4}[-\s]?\d{4}|\d{10,11})(?!\d)"
)

API_KEY_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|secret|token|access[_-]?token)\b\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"
)

ID_PATTERN = re.compile(
    r"(?<!\d)\d{15,18}(?!\d)"
)


def redact_pii(text: str) -> str:
    """
    Redact basic PII and secrets from text.
    """
    if not text:
        return text

    redacted = text

    redacted = EMAIL_PATTERN.sub("[EMAIL]", redacted)
    redacted = PHONE_PATTERN.sub("[PHONE]", redacted)

    # Keep the key name but redact the value.
    redacted = API_KEY_PATTERN.sub(
        lambda match: match.group(0).split("=")[0].split(":")[0] + "=[REDACTED_SECRET]",
        redacted,
    )

    redacted = ID_PATTERN.sub("[ID_NUMBER]", redacted)

    return redacted