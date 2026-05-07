#每次传入一个 dict，把它转成 JSON
#追加写入 logs/rag_service.jsonl
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def write_json_log(log_path: str, log_record: Dict[str, Any]) -> None:
    """
    Write one structured log record as one JSON line.
    """
    full_log_path = PROJECT_ROOT / log_path
    full_log_path.parent.mkdir(parents=True, exist_ok=True)

    log_record["timestamp"] = datetime.now(timezone.utc).isoformat()

    with open(full_log_path, "a", encoding="utf-8") as file:
        file.write(json.dumps(log_record, ensure_ascii=False) + "\n")