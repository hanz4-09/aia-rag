import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class InMemorySessionMemory:
    """
    Lightweight session memory for multi-turn RAG.

    Features:
    - keep recent turns per session
    - enforce max_turns per session
    - enforce max_sessions globally
    - optional TTL cleanup
    """

    def __init__(
        self,
        max_turns: int = 3,
        max_sessions: int = 1000,
        ttl_seconds: Optional[int] = None,
        cleanup_enabled: bool = True,
    ):
        self.max_turns = max_turns
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds
        self.cleanup_enabled = cleanup_enabled
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.session_updated_at: Dict[str, float] = {}

    def add_turn(self, session_id: Optional[str], question: str, answer: str) -> None:
        if not session_id:
            return

        self.cleanup_expired_sessions()

        turns = self.sessions.setdefault(session_id, [])
        turns.append(
            {
                "question": question,
                "answer": answer,
            }
        )

        self.sessions[session_id] = turns[-self.max_turns :]
        self.session_updated_at[session_id] = time.time()

        self.enforce_max_sessions()

    def get_recent_turns(
        self,
        session_id: Optional[str],
        max_turns: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        if not session_id:
            return []

        self.cleanup_expired_sessions()

        turns = self.sessions.get(session_id, [])
        limit = max_turns or self.max_turns
        return turns[-limit:]

    def get_history(
        self,
        session_id: Optional[str],
        max_turns: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """
        Backward-compatible alias used by existing multi-turn evaluators.
        """
        return self.get_recent_turns(session_id, max_turns=max_turns)

    def clear_session(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)
        self.session_updated_at.pop(session_id, None)

    def cleanup_expired_sessions(self) -> int:
        if not self.cleanup_enabled or not self.ttl_seconds:
            return 0

        now = time.time()
        expired_session_ids = [
            session_id
            for session_id, updated_at in self.session_updated_at.items()
            if now - updated_at > self.ttl_seconds
        ]

        for session_id in expired_session_ids:
            self.clear_session(session_id)

        return len(expired_session_ids)

    def enforce_max_sessions(self) -> int:
        if self.max_sessions <= 0:
            return 0

        removed_count = 0

        while len(self.sessions) > self.max_sessions:
            oldest_session_id = min(
                self.session_updated_at,
                key=self.session_updated_at.get,
            )
            self.clear_session(oldest_session_id)
            removed_count += 1

        return removed_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_turns": self.max_turns,
            "max_sessions": self.max_sessions,
            "ttl_seconds": self.ttl_seconds,
            "cleanup_enabled": self.cleanup_enabled,
            "sessions": self.sessions,
            "session_updated_at": self.session_updated_at,
        }

    def load_dict(self, data: Dict[str, Any]) -> None:
        self.max_turns = int(data.get("max_turns", self.max_turns))
        self.max_sessions = int(data.get("max_sessions", self.max_sessions))
        self.ttl_seconds = data.get("ttl_seconds", self.ttl_seconds)
        self.cleanup_enabled = bool(data.get("cleanup_enabled", self.cleanup_enabled))

        self.sessions = data.get("sessions", {}) or {}

        loaded_updated_at = data.get("session_updated_at", {}) or {}
        now = time.time()

        self.session_updated_at = {
            session_id: float(loaded_updated_at.get(session_id, now))
            for session_id in self.sessions
        }

        self.cleanup_expired_sessions()
        self.enforce_max_sessions()


class JsonSessionMemory(InMemorySessionMemory):
    """
    JSON-backed lightweight session memory.

    This is not a distributed production memory store, but it provides simple
    local persistence for demo and evaluation scenarios.
    """

    def __init__(
        self,
        path: str | Path,
        max_turns: int = 3,
        max_sessions: int = 1000,
        ttl_seconds: Optional[int] = None,
        cleanup_enabled: bool = True,
    ):
        super().__init__(
            max_turns=max_turns,
            max_sessions=max_sessions,
            ttl_seconds=ttl_seconds,
            cleanup_enabled=cleanup_enabled,
        )
        self.path = Path(path)
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.load_dict(data)
        except Exception:
            # Avoid breaking the service because of a corrupted demo memory file.
            self.sessions = {}
            self.session_updated_at = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_turn(self, session_id: Optional[str], question: str, answer: str) -> None:
        super().add_turn(session_id, question, answer)
        self.save()

    def get_recent_turns(
        self,
        session_id: Optional[str],
        max_turns: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        turns = super().get_recent_turns(session_id, max_turns=max_turns)
        self.save()
        return turns

    def clear_session(self, session_id: str) -> None:
        super().clear_session(session_id)
        self.save()

    def cleanup_expired_sessions(self) -> int:
        removed_count = super().cleanup_expired_sessions()
        return removed_count

    def enforce_max_sessions(self) -> int:
        removed_count = super().enforce_max_sessions()
        return removed_count



class PersistentSessionMemory(JsonSessionMemory):
    """
    Backward-compatible alias for earlier advanced-memory evaluation scripts.

    Older code imported PersistentSessionMemory directly. The new implementation
    uses JsonSessionMemory for local persistent memory, so this class preserves
    the previous public name while reusing the TTL/cleanup-capable JSON backend.
    """

    def __init__(
        self,
        path: str | Path | None = None,
        memory_path: str | Path | None = None,
        file_path: str | Path | None = None,
        storage_path: str | Path | None = None,
        max_turns: int = 3,
        max_sessions: int = 1000,
        ttl_seconds: Optional[int] = None,
        cleanup_enabled: bool = True,
    ):
        resolved_path = (
            path
            or memory_path
            or file_path
            or storage_path
            or "data/session_memory/session_memory.json"
        )

        super().__init__(
            path=resolved_path,
            max_turns=max_turns,
            max_sessions=max_sessions,
            ttl_seconds=ttl_seconds,
            cleanup_enabled=cleanup_enabled,
        )


def create_session_memory(config: Dict[str, Any]):
    memory_config = config.get("memory", {})

    enabled = memory_config.get("enabled", True)
    if not enabled:
        return InMemorySessionMemory(max_turns=0, max_sessions=0)

    memory_type = memory_config.get("type", "in_memory")
    max_turns = int(memory_config.get("max_turns", 3))
    max_sessions = int(memory_config.get("max_sessions", 1000))
    ttl_seconds = memory_config.get("ttl_seconds")
    cleanup_enabled = bool(memory_config.get("cleanup_enabled", True))

    if ttl_seconds in ("", None):
        ttl_seconds = None
    elif ttl_seconds is not None:
        ttl_seconds = int(ttl_seconds)

    if memory_type in {"json", "file", "json_file"}:
        path = memory_config.get(
            "path",
            "data/session_memory/session_memory.json",
        )
        return JsonSessionMemory(
            path=path,
            max_turns=max_turns,
            max_sessions=max_sessions,
            ttl_seconds=ttl_seconds,
            cleanup_enabled=cleanup_enabled,
        )

    return InMemorySessionMemory(
        max_turns=max_turns,
        max_sessions=max_sessions,
        ttl_seconds=ttl_seconds,
        cleanup_enabled=cleanup_enabled,
    )
