import json
from collections import deque
from pathlib import Path
from threading import Lock
from typing import Deque, Dict, List, Optional


class InMemorySessionMemory:
    """
    Backward-compatible in-memory session memory.
    """

    def __init__(self, max_turns: int = 3):
        self.max_turns = max_turns
        self._store: Dict[str, Deque[Dict[str, str]]] = {}
        self._lock = Lock()

    def get_history(self, session_id: Optional[str]) -> List[Dict[str, str]]:
        if not session_id:
            return []

        with self._lock:
            history = self._store.get(session_id)
            if not history:
                return []
            return list(history)

    def add_turn(
        self,
        session_id: Optional[str],
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

    def clear(self, session_id: Optional[str]) -> None:
        if not session_id:
            return

        with self._lock:
            self._store.pop(session_id, None)


class PersistentSessionMemory:
    """
    File-backed session memory for Advanced Memory v1.

    Features:
    - keeps recent turns by session_id
    - persists memory to a local JSON file
    - restores memory when service restarts
    - caps both max_turns per session and max_sessions globally

    This is still a local MVP persistence layer, not a production distributed
    memory store.
    """

    def __init__(
        self,
        max_turns: int = 3,
        storage_path: str = "data/session_memory/session_memory.json",
        max_sessions: int = 1000,
    ):
        self.max_turns = max_turns
        self.storage_path = Path(storage_path)
        self.max_sessions = max_sessions
        self._store: Dict[str, Deque[Dict[str, str]]] = {}
        self._lock = Lock()

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_from_disk()

    def get_history(self, session_id: Optional[str]) -> List[Dict[str, str]]:
        if not session_id:
            return []

        with self._lock:
            history = self._store.get(session_id)
            if not history:
                return []
            return list(history)

    def add_turn(
        self,
        session_id: Optional[str],
        question: str,
        answer: str,
    ) -> None:
        if not session_id:
            return

        if not question.strip() or not answer.strip():
            return

        with self._lock:
            self._evict_if_needed(session_id)

            if session_id not in self._store:
                self._store[session_id] = deque(maxlen=self.max_turns)

            self._store[session_id].append(
                {
                    "question": question.strip(),
                    "answer": answer.strip(),
                }
            )

            self._save_to_disk()

    def clear(self, session_id: Optional[str]) -> None:
        if not session_id:
            return

        with self._lock:
            self._store.pop(session_id, None)
            self._save_to_disk()

    def clear_all(self) -> None:
        with self._lock:
            self._store.clear()
            self._save_to_disk()

    def _evict_if_needed(self, incoming_session_id: str) -> None:
        if incoming_session_id in self._store:
            return

        if len(self._store) < self.max_sessions:
            return

        # Dicts preserve insertion order in modern Python.
        oldest_session_id = next(iter(self._store))
        self._store.pop(oldest_session_id, None)

    def _load_from_disk(self) -> None:
        if not self.storage_path.exists():
            return

        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self._store = {}
            return

        sessions = raw.get("sessions", {})

        for session_id, turns in sessions.items():
            self._store[session_id] = deque(
                [
                    {
                        "question": str(turn.get("question", "")),
                        "answer": str(turn.get("answer", "")),
                    }
                    for turn in turns
                    if turn.get("question") or turn.get("answer")
                ],
                maxlen=self.max_turns,
            )

    def _save_to_disk(self) -> None:
        payload = {
            "max_turns": self.max_turns,
            "max_sessions": self.max_sessions,
            "sessions": {
                session_id: list(turns)
                for session_id, turns in self._store.items()
            },
        }

        tmp_path = self.storage_path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(self.storage_path)


def create_session_memory(config: Dict) -> object:
    memory_config = config.get("memory", {})

    memory_type = memory_config.get("type", "in_memory").lower()
    max_turns = memory_config.get("max_turns", 3)

    if memory_type == "persistent":
        return PersistentSessionMemory(
            max_turns=max_turns,
            storage_path=memory_config.get(
                "storage_path",
                "data/session_memory/session_memory.json",
            ),
            max_sessions=memory_config.get("max_sessions", 1000),
        )

    return InMemorySessionMemory(max_turns=max_turns)
