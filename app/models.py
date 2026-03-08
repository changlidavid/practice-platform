from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunResult:
    status: str
    passed: int
    failed: int
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
