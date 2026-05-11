from typing import Dict, List


FOLLOW_UP_MARKERS_EN = [
    "they",
    "them",
    "it",
    "that",
    "this",
    "those",
    "these",
    "he",
    "she",
    "how long",
    "what about",
    "what if",
    "and",
]

FOLLOW_UP_MARKERS_CN = [
    "它",
    "它们",
    "这个",
    "那个",
    "这些",
    "那些",
    "多久",
    "多少",
    "怎么办",
    "呢",
    "如果",
    "还有",
]


def is_follow_up_question(question: str) -> bool:
    normalized = question.strip().lower()

    if not normalized:
        return False

    # Short questions are often follow-ups.
    if len(normalized.split()) <= 8 and len(normalized) <= 80:
        return True

    if any(marker in normalized for marker in FOLLOW_UP_MARKERS_EN):
        return True

    if any(marker in question for marker in FOLLOW_UP_MARKERS_CN):
        return True

    return False


def build_history_aware_retrieval_query(
    question: str,
    conversation_history: List[Dict[str, str]],
) -> Dict[str, object]:
    """
    Build a retrieval query using recent conversation history.

    This is a deterministic v1 query-rewrite strategy:
    - if there is no history, use the current question
    - if the current question looks like a follow-up, prepend the previous question
    - otherwise use the current question

    It avoids additional LLM calls and keeps latency/cost predictable.
    """
    current_question = question.strip()

    if not conversation_history:
        return {
            "retrieval_query": current_question,
            "memory_rewrite_applied": False,
            "rewrite_strategy": "no_history",
        }

    if not is_follow_up_question(current_question):
        return {
            "retrieval_query": current_question,
            "memory_rewrite_applied": False,
            "rewrite_strategy": "not_follow_up",
        }

    previous_turn = conversation_history[-1]
    previous_question = previous_turn.get("question", "").strip()

    if not previous_question:
        return {
            "retrieval_query": current_question,
            "memory_rewrite_applied": False,
            "rewrite_strategy": "empty_previous_question",
        }

    retrieval_query = (
        "Previous question: "
        f"{previous_question}\n"
        "Current follow-up question: "
        f"{current_question}"
    )

    return {
        "retrieval_query": retrieval_query,
        "memory_rewrite_applied": True,
        "rewrite_strategy": "previous_question_plus_current_follow_up",
    }
