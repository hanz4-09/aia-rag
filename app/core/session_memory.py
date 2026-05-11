from collections import deque
from threading import Lock
from typing import Deque, Dict, List


class InMemorySessionMemory:
    """
    Lightweight in-memory session memory for multi-turn QA.

    This is an MVP implementation:
    - stores recent turns by session_id
    - keeps only the latest N turns
    - resets when the service restarts
    - is not shared across multiple service instances
    """

    def __init__(self, max_turns: int = 3):
        self.max_turns = max_turns
        self._store: Dict[str, Deque[Dict[str, str]]] = {}
        self._lock = Lock()

    def get_history(self, session_id: str | None) -> List[Dict[str, str]]:
        if not session_id:
            return []

        with self._lock:
            history = self._store.get(session_id)
            if not history:
                return []
            return list(history)

    def add_turn(
        self,
        session_id: str | None,
        question: str,
        answer: str,
    ) -> None:
        if not session_id:
            return

        if not question.strip() or not answer.strip():
            return

        with self._lock:
            if session_id not in self._store:
                self._store[session_id] = deque(maxlen=self.max_turns)

            self._store[session_id].append(
                {
                    "question": question,
                    "answer": answer,
                }
            )

    def clear(self, session_id: str | None) -> None:
        if not session_id:
            return

        with self._lock:
            self._store.pop(session_id, None)
