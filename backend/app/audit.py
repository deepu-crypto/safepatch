import json
from datetime import datetime
from pathlib import Path
from typing import Any


AUDIT_LOG_PATH = Path("audit_logs/agent_audit.jsonl")


def log_event(event_type: str, payload: dict[str, Any]) -> None:
    """
    Writes an audit event to a JSONL file.

    Each line is one JSON object.

    Example event:
    {
      "timestamp": "...",
      "event_type": "human_approval",
      "payload": {...}
    }
    """

    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "payload": payload
    }

    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")
