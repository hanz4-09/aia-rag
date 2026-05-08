import re
from typing import Dict


PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+the\s+above\s+instructions",
    r"disregard\s+(all\s+)?previous\s+instructions",
    r"forget\s+(all\s+)?previous\s+instructions",
    r"bypass\s+(the\s+)?rules",
    r"override\s+(the\s+)?system",
    r"忽略.*(之前|以上|上面).*指令",
    r"无视.*(之前|以上|上面).*规则",
]


SYSTEM_PROMPT_EXTRACTION_PATTERNS = [
    r"(show|reveal|print|display|tell\s+me)\s+.*system\s+prompt",
    r"(show|reveal|print|display|tell\s+me)\s+.*developer\s+message",
    r"(show|reveal|print|display|tell\s+me)\s+.*system\s+message",
    r"(系统提示词|系统指令|开发者消息|system prompt).*(是什么|给我|显示|打印|透露)",
    r"(给我|显示|打印|透露).*(系统提示词|系统指令|开发者消息|system prompt)",
]


SECRET_EXTRACTION_PATTERNS = [
    # English secret extraction attempts.
    # Block: "show me your API key", "reveal the access token", "give me the password"
    r"(show|reveal|print|display|tell\s+me|give\s+me)\s+.*(api\s*key|secret\s*key|access\s*token|password|credential)",
    r"(api\s*key|secret\s*key|access\s*token|password|credential)\s+.*(show|reveal|print|display|tell\s+me|give\s+me)",

    # Chinese secret extraction attempts.
    # Block: "给我 API Key", "显示访问令牌", "打印密码", "透露密钥", "导出 token"
    # Do NOT block normal policy questions like "API Key 泄露后应该怎么处理？"
    r"(给我|显示|打印|透露|导出).*(api\s*key|密钥|访问令牌|token|密码|凭证)",
    r"(api\s*key|密钥|访问令牌|token|密码|凭证).*(给我|显示|打印|透露|导出)",
]


def check_safety(question: str) -> Dict:
    """
    Basic safety check for prompt injection and secret extraction attempts.

    This function blocks attempts to reveal system instructions or actual secrets,
    but allows normal security policy questions, such as:
    - API Key 泄露后应该怎么处理？
    - What is the API key handling policy?
    - Can logs store API keys?
    """
    normalized_question = question.lower().strip()

    all_patterns = (
        PROMPT_INJECTION_PATTERNS
        + SYSTEM_PROMPT_EXTRACTION_PATTERNS
        + SECRET_EXTRACTION_PATTERNS
    )

    for pattern in all_patterns:
        if re.search(pattern, normalized_question, flags=re.IGNORECASE):
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