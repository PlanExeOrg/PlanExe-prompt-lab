"""Shared event logging for optimization iterations.

Writes JSONL events to an events.jsonl file in the analysis directory,
matching the format used by self_improve/runner.py.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path


def timestamp() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def emit_event(events_path: Path, event: str, **kwargs) -> None:
    """Append one JSON line to the events file."""
    entry = {"timestamp": timestamp(), "event": event, **kwargs}
    with open(events_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


class EventTimer:
    """Context manager that emits start/complete/error events with duration."""

    def __init__(self, events_path: Path, name: str, **extra):
        self.events_path = events_path
        self.name = name
        self.extra = extra

    def __enter__(self):
        emit_event(self.events_path, f"{self.name}_start", **self.extra)
        self._t0 = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = round(time.monotonic() - self._t0, 2)
        if exc_type is None:
            emit_event(self.events_path, f"{self.name}_complete",
                       status="ok", duration_seconds=duration)
        else:
            emit_event(self.events_path, f"{self.name}_error",
                       error=str(exc_val), duration_seconds=duration)
        return False
