from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RunResult:
    status: str
    passed: int
    failed: int
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    feedback: dict[str, Any] | None = None
