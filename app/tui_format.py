from __future__ import annotations

from datetime import datetime


def verdict_label(status: str | None) -> str:
    normalized = (status or "never").lower()
    if normalized == "pass":
        return "PASS"
    if normalized == "fail":
        return "FAIL"
    if normalized == "error":
        return "ERROR"
    return "NEVER"


def verdict_filter_value(status: str | None) -> str:
    return (status or "never").lower()


def format_duration(duration_ms: int | None) -> str:
    if duration_ms is None:
        return "-"
    return str(duration_ms)


def format_timestamp(ts: str | None) -> str:
    if not ts:
        return "-"
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return ts
    return dt.strftime("%Y-%m-%d %H:%M:%S")
