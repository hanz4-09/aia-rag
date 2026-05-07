from typing import Dict


INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore the above instructions",
    "reveal your system prompt",
    "show me your system prompt",
    "print your system prompt",
    "developer message",
    "system message",
    "api key",
    "secret key",
    "access token",
    "password",
]


def check_safety(question: str) -> Dict:
    """
    Basic safety check for prompt injection and secret extraction attempts.
    """
    normalized_question = question.lower()

    for keyword in INJECTION_KEYWORDS:
        if keyword in normalized_question:
            return {
                "safe": False,
                "reason": "SAFETY_RULE_TRIGGERED",
                "message": (
                    "I cannot help with requests to reveal system instructions, "
                    "secrets, passwords, API keys, or access tokens."
                ),
            }

    return {
        "safe": True,
        "reason": None,
        "message": None,
    }