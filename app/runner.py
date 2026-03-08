from __future__ import annotations

import ast
import hashlib
import doctest
import os
import queue
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, TextIO

from . import db
from .config import Paths
from .models import RunResult


_PASS_FAIL_RE = re.compile(r"(\d+)\s+passed\s+and\s+(\d+)\s+failed")
_TOTAL_RE = re.compile(r"(\d+)\s+tests?\s+in")
_DEFAULT_DOCTEST_TIMEOUT_SECONDS = 5.0
_DEFAULT_OUTPUT_MAX_BYTES = 262_144
_TIMEOUT_EXIT_CODE = 124
LogCallback = Callable[[str, str], None]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _compose_doctest_module(*, doctest_text: str, solution_code: str) -> str:
    # Keep doctests immutable by forcing module-level __doc__ from DB.
    return f"__doc__ = {doctest_text!r}\n\n{solution_code.rstrip()}\n"


def _count_expected_tests(source_code: str) -> int:
    try:
        module = ast.parse(source_code)
    except SyntaxError:
        return 0

    parser = doctest.DocTestParser()
    total = 0
    for node in ast.walk(module):
        if not isinstance(
            node,
            (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            continue
        doc = ast.get_docstring(node, clean=False) or ""
        if not doc:
            continue
        parts = parser.parse(doc)
        total += sum(1 for part in parts if isinstance(part, doctest.Example))
    return total


def _parse_counts(stdout: str, stderr: str) -> tuple[int, int, int]:
    text = f"{stdout}\n{stderr}"
    passed = 0
    failed = 0
    total = 0

    pass_fail_matches = _PASS_FAIL_RE.findall(text)
    if pass_fail_matches:
        last_passed, last_failed = pass_fail_matches[-1]
        passed = int(last_passed)
        failed = int(last_failed)

    total_matches = _TOTAL_RE.findall(text)
    if total_matches:
        # Use the largest summary seen in output to avoid small per-item lines.
        total = max(int(match) for match in total_matches)
    if total > 0 and passed == 0 and failed == 0:
        # Fallback when detailed pass/fail line is not present.
        if "failed" not in text.lower():
            passed = total
        else:
            failed = total
    return passed, failed, total


def _output_max_bytes() -> int:
    raw = os.getenv("PRACTICE_DOCTEST_OUTPUT_MAX_BYTES", str(_DEFAULT_OUTPUT_MAX_BYTES)).strip()
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return _DEFAULT_OUTPUT_MAX_BYTES
    if value <= 0:
        return _DEFAULT_OUTPUT_MAX_BYTES
    return value


def _truncation_marker(stream_name: str, max_bytes: int) -> str:
    return f"[runner] {stream_name} truncated at {max_bytes} bytes.\n"


def _append_capped(
    chunks: list[str],
    *,
    stream_name: str,
    chunk: str,
    used_bytes: int,
    max_bytes: int,
    truncated: bool,
) -> tuple[int, bool, str]:
    if truncated:
        return used_bytes, True, ""

    chunk_bytes = chunk.encode("utf-8")
    if used_bytes + len(chunk_bytes) <= max_bytes:
        chunks.append(chunk)
        return used_bytes + len(chunk_bytes), False, chunk

    room = max_bytes - used_bytes
    appended = ""
    if room > 0:
        appended_bytes = chunk_bytes[:room]
        appended = appended_bytes.decode("utf-8", errors="ignore")
        if appended:
            chunks.append(appended)
            used_bytes += len(appended.encode("utf-8"))

    marker = _truncation_marker(stream_name, max_bytes)
    chunks.append(marker)
    return used_bytes, True, f"{appended}{marker}"


def _terminate_process_tree(proc: subprocess.Popen[str], *, grace_seconds: float = 0.3) -> None:
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=grace_seconds)
            return
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        proc.wait()
        return

    proc.terminate()
    try:
        proc.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def _create_attempt_workspace(paths: Paths, attempt_id: int) -> Path:
    return Path(tempfile.mkdtemp(prefix=f"attempt_{attempt_id}_", dir=paths.runs_dir))


def _should_preserve_attempt_workspace() -> bool:
    # Reserved hook for future debug mode to preserve failed run artifacts.
    return False


def _execute_doctest(
    cmd: list[str],
    *,
    cwd: Path,
    log_callback: LogCallback | None = None,
    timeout_seconds: float,
) -> tuple[int, str, str]:
    popen_kwargs: dict[str, object] = {}
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        **popen_kwargs,
    )
    if proc.stdout is None or proc.stderr is None:
        raise RuntimeError("Failed to capture doctest process output.")

    q: queue.Queue[tuple[str, str | None]] = queue.Queue()
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    output_max_bytes = _output_max_bytes()
    stdout_used_bytes = 0
    stderr_used_bytes = 0
    stdout_truncated = False
    stderr_truncated = False

    def _record_chunk(stream_name: str, chunk: str) -> None:
        nonlocal stdout_used_bytes, stderr_used_bytes, stdout_truncated, stderr_truncated
        if stream_name == "stdout":
            stdout_used_bytes, stdout_truncated, emitted = _append_capped(
                stdout_chunks,
                stream_name=stream_name,
                chunk=chunk,
                used_bytes=stdout_used_bytes,
                max_bytes=output_max_bytes,
                truncated=stdout_truncated,
            )
        else:
            stderr_used_bytes, stderr_truncated, emitted = _append_capped(
                stderr_chunks,
                stream_name=stream_name,
                chunk=chunk,
                used_bytes=stderr_used_bytes,
                max_bytes=output_max_bytes,
                truncated=stderr_truncated,
            )
        if log_callback is not None and emitted:
            log_callback(stream_name, emitted)

    def _reader(stream_name: str, pipe: TextIO) -> None:
        for line in iter(pipe.readline, ""):
            q.put((stream_name, line))
        pipe.close()
        q.put((stream_name, None))

    t_out = threading.Thread(target=_reader, args=("stdout", proc.stdout), daemon=True)
    t_err = threading.Thread(target=_reader, args=("stderr", proc.stderr), daemon=True)
    t_out.start()
    t_err.start()

    deadline = time.monotonic() + timeout_seconds
    timed_out = False
    closed = 0
    while closed < 2:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            _terminate_process_tree(proc)
            break
        try:
            stream_name, chunk = q.get(timeout=remaining)
        except queue.Empty:
            timed_out = True
            _terminate_process_tree(proc)
            break
        if chunk is None:
            closed += 1
            continue
        _record_chunk(stream_name, chunk)

    returncode = proc.wait()
    t_out.join(timeout=0.5)
    t_err.join(timeout=0.5)

    # Drain any buffered output queued while shutting down.
    while True:
        try:
            stream_name, chunk = q.get_nowait()
        except queue.Empty:
            break
        if chunk is None:
            continue
        _record_chunk(stream_name, chunk)

    if timed_out:
        timeout_msg = f"[runner] Doctest timed out after {timeout_seconds:.1f}s.\n"
        _record_chunk("stderr", timeout_msg)
        returncode = _TIMEOUT_EXIT_CODE
    return returncode, "".join(stdout_chunks), "".join(stderr_chunks)


def run_problem(
    conn: sqlite3.Connection,
    paths: Paths,
    problem_row: sqlite3.Row,
    *,
    user_id: int | None = None,
    solution_content: str | None = None,
    log_callback: LogCallback | None = None,
) -> tuple[int, RunResult]:
    if solution_content is None:
        if user_id is not None:
            solution_row = db.ensure_user_solution(conn, user_id=user_id, problem_row=problem_row)
            solution_content = str(solution_row["content"])
        else:
            cli_user_id = db.ensure_cli_user(conn)
            solution_row = db.ensure_user_solution(conn, user_id=cli_user_id, problem_row=problem_row)
            solution_content = str(solution_row["content"])

    run_user = user_id if user_id is not None else "anon"
    composed = _compose_doctest_module(
        doctest_text=str(problem_row["doctest"]),
        solution_code=solution_content,
    )
    expected_tests = _count_expected_tests(composed)
    solution_hash = _sha256_text(solution_content)

    attempt_id = db.create_attempt(
        conn,
        int(problem_row["id"]),
        solution_hash,
        user_id=user_id,
    )

    run_dir = _create_attempt_workspace(paths, attempt_id)
    run_solution = run_dir / f"solution_user_{run_user}.py"
    run_solution.write_text(composed, encoding="utf-8")

    bundle_id_raw = problem_row["bundle_id"]
    if bundle_id_raw is not None:
        for asset in db.list_bundle_assets(conn, bundle_id=int(bundle_id_raw)):
            rel_str = str(asset["relpath"])
            dest = run_dir / rel_str
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(bytes(asset["content"]))

    timeout_seconds = float(os.getenv("PRACTICE_DOCTEST_TIMEOUT_SECONDS", _DEFAULT_DOCTEST_TIMEOUT_SECONDS))
    if timeout_seconds <= 0:
        timeout_seconds = _DEFAULT_DOCTEST_TIMEOUT_SECONDS

    cmd = [sys.executable, "-I", "-m", "doctest", str(run_solution)]

    start = time.monotonic()
    try:
        returncode, stdout, stderr = _execute_doctest(
            cmd,
            cwd=run_dir,
            log_callback=log_callback,
            timeout_seconds=timeout_seconds,
        )
    finally:
        if not _should_preserve_attempt_workspace():
            shutil.rmtree(run_dir, ignore_errors=True)
    duration_ms = int((time.monotonic() - start) * 1000)

    passed_count, failed_count, total_count = _parse_counts(stdout, stderr)
    if returncode == 0 and expected_tests > 0:
        status = "pass"
    elif returncode == 1:
        status = "fail"
    else:
        status = "error"

    if returncode == 0 and total_count == 0 and expected_tests > 0:
        # `python -m doctest` can be silent on success without `-v`.
        passed_count = expected_tests
        failed_count = 0

    result = RunResult(
        status=status,
        passed=passed_count,
        failed=failed_count,
        exit_code=returncode,
        stdout=stdout,
        stderr=stderr,
        duration_ms=duration_ms,
    )

    db.finalize_attempt(
        conn,
        attempt_id=attempt_id,
        status=result.status,
        passed_count=result.passed,
        failed_count=result.failed,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        duration_ms=result.duration_ms,
    )
    return attempt_id, result
