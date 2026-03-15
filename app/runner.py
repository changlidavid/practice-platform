from __future__ import annotations

import ast
import hashlib
import doctest
import json
import os
import queue
import re
import shlex
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, TextIO

from . import db
from .config import Paths
from .models import RunResult


_PASS_FAIL_RE = re.compile(r"(\d+)\s+passed\s+and\s+(\d+)\s+failed")
_TOTAL_RE = re.compile(r"(\d+)\s+tests?\s+in")
_DEFAULT_DOCTEST_TIMEOUT_SECONDS = 5.0
_DEFAULT_OUTPUT_MAX_BYTES = 262_144
_TIMEOUT_EXIT_CODE = 124
_MAX_FAILURE_DETAILS = 5
_DOCKER_CHECK_TIMEOUT_SECONDS = 5.0
_MAX_INPUT_SUMMARY_ITEMS = 3
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


def _count_expected_tests_in_doctest_text(doctest_text: str) -> int:
    if not doctest_text.strip():
        return 0
    parser = doctest.DocTestParser()
    parts = parser.parse(doctest_text)
    return sum(1 for part in parts if isinstance(part, doctest.Example))


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


def _runner_mount_mode() -> str:
    return os.getenv("PRACTICE_RUNNER_MOUNT_MODE", "").strip().lower()


def _runner_image() -> str:
    return os.getenv("PRACTICE_RUNNER_IMAGE", "python:3.12-slim").strip() or "python:3.12-slim"


def _runner_debug_enabled() -> bool:
    return os.getenv("PRACTICE_RUNNER_DEBUG", "").strip().lower() in {"1", "true", "yes"}


def _docker_available() -> bool:
    try:
        proc = subprocess.run(
            ["docker", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=_DOCKER_CHECK_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def _rewrite_cmd_for_container(cmd: list[str], *, cwd: Path, mount_root: Path) -> list[str]:
    rewritten: list[str] = []
    for index, token in enumerate(cmd):
        if index == 0 and (token == sys.executable or Path(token).is_absolute()):
            # Never pass host interpreter paths into the container.
            # Use a container-local interpreter instead.
            rewritten.append("python3")
            continue
        path_like = Path(token)
        if path_like.is_absolute():
            try:
                rel = path_like.relative_to(cwd)
                rewritten.append(str((mount_root / rel).as_posix()))
                continue
            except ValueError:
                pass
        rewritten.append(token)
    return rewritten


def _build_container_cmd(cmd: list[str], *, cwd: Path) -> list[str]:
    mount_root = Path("/workspace")
    rewritten_cmd = _rewrite_cmd_for_container(cmd, cwd=cwd, mount_root=mount_root)
    if rewritten_cmd:
        first_name = Path(rewritten_cmd[0]).name.lower()
        if first_name.startswith("python") or Path(rewritten_cmd[0]).is_absolute():
            rewritten_cmd[0] = "python3"

    docker_cmd = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--workdir",
        str(mount_root),
        "-v",
        f"{cwd}:{mount_root}:rw",
    ]

    memory_limit = os.getenv("PRACTICE_RUNNER_MEMORY", "").strip()
    if memory_limit:
        docker_cmd.extend(["--memory", memory_limit])
    pids_limit = os.getenv("PRACTICE_RUNNER_PIDS_LIMIT", "").strip()
    if pids_limit:
        docker_cmd.extend(["--pids-limit", pids_limit])
    cpu_limit = os.getenv("PRACTICE_RUNNER_CPUS", "").strip()
    if cpu_limit:
        docker_cmd.extend(["--cpus", cpu_limit])

    docker_cmd.append(_runner_image())
    docker_cmd.extend(rewritten_cmd)
    return docker_cmd


def _execute_doctest(
    cmd: list[str],
    *,
    cwd: Path,
    log_callback: LogCallback | None = None,
    timeout_seconds: float,
) -> tuple[int, str, str]:
    launch_cmd = cmd
    if _runner_mount_mode() in {"bind", "volume"} and _docker_available():
        launch_cmd = _build_container_cmd(cmd, cwd=cwd)
    debug_prefix = ""
    if _runner_debug_enabled():
        debug_prefix = (
            f"[runner-debug] cwd={cwd}\n"
            f"[runner-debug] requested_cmd={shlex.join(cmd)}\n"
            f"[runner-debug] launch_cmd={shlex.join(launch_cmd)}\n"
        )

    popen_kwargs: dict[str, object] = {}
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        launch_cmd,
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
    stderr_chunks: list[str] = [debug_prefix] if debug_prefix else []
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


_FUNCTION_EVAL_SCRIPT = """\
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path


def _emit(payload: dict[str, object], code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(code)


def main() -> None:
    if len(sys.argv) < 5:
        _emit({"status": "error", "error": "Invalid evaluator arguments."}, 2)

    cases_path = Path(sys.argv[1])
    solution_path = Path(sys.argv[2])
    entry_function = sys.argv[3]
    feedback_mode = sys.argv[4]

    try:
        cases_payload = json.loads(cases_path.read_text(encoding="utf-8"))
    except Exception as exc:
        _emit({"status": "error", "error": f"Failed to load evaluator cases: {exc}"}, 2)

    cases = cases_payload.get("cases") if isinstance(cases_payload, dict) else None
    if not isinstance(cases, list):
        _emit({"status": "error", "error": "Evaluator cases must be an object with list field 'cases'."}, 2)
    if not cases:
        _emit({"status": "error", "error": "Evaluator cases contain no cases."}, 2)

    try:
        spec = importlib.util.spec_from_file_location("user_solution", solution_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("Failed to create module spec.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exc:
        _emit({"status": "error", "error": f"Failed to import submitted solution: {type(exc).__name__}: {exc}"}, 2)

    candidate = getattr(module, entry_function, None)
    if candidate is None or not callable(candidate):
        _emit({"status": "error", "error": f"Target function '{entry_function}' not found or not callable."}, 2)

    passed = 0
    failed = 0
    public_results: list[dict[str, object]] = []
    first_failure: dict[str, object] | None = None
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            failed += 1
            if feedback_mode == "submit" and first_failure is None:
                first_failure = {
                    "case_id": f"case-{index}",
                    "message": "Case entry must be an object.",
                }
            continue

        case_id = str(case.get("id") or f"case-{index}")
        case_label = case.get("case_label") or case_id
        args = case.get("args", [])
        kwargs = case.get("kwargs", {})
        expected = case.get("expected")
        input_text = case.get("input_text")
        input_summary = case.get("input_summary")

        if not isinstance(args, list) or not isinstance(kwargs, dict):
            failed += 1
            if feedback_mode == "run":
                public_results.append(
                    {
                        "id": case_id,
                        "input": input_text,
                        "expected": expected,
                        "actual": None,
                        "passed": False,
                        "message": "Case args must be list and kwargs must be object.",
                    }
                )
            elif first_failure is None:
                first_failure = {
                    "case_id": case_id,
                    "case_label": case_label,
                    "message": "Case args must be list and kwargs must be object.",
                    "failure_type": "Runtime Error",
                }
            continue

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                actual = candidate(*args, **kwargs)
            except Exception as exc:
                failed += 1
                if feedback_mode == "run":
                    public_results.append(
                        {
                            "id": case_id,
                            "input": input_text,
                            "expected": expected,
                            "actual": None,
                            "passed": False,
                            "message": f"{type(exc).__name__}: {exc}",
                        }
                    )
                elif first_failure is None:
                    first_failure = {
                        "case_id": case_id,
                        "case_label": case_label,
                        "message": f"{type(exc).__name__}: {exc}",
                        "failure_type": "Runtime Error",
                        "input_summary": input_summary,
                    }
                continue

        if actual == expected:
            passed += 1
            if feedback_mode == "run":
                public_results.append(
                    {
                        "id": case_id,
                        "input": input_text,
                        "expected": expected,
                        "actual": actual,
                        "passed": True,
                    }
                )
            continue

        failed += 1
        if feedback_mode == "run":
            public_results.append(
                {
                    "id": case_id,
                    "input": input_text,
                    "expected": expected,
                    "actual": actual,
                    "passed": False,
                    "message": "Wrong answer",
                }
            )
        elif first_failure is None:
            first_failure = {
                "case_id": case_id,
                "case_label": case_label,
                "message": "Wrong answer",
                "failure_type": "Wrong Answer",
                "actual": actual,
                "expected": expected,
                "input_summary": input_summary,
            }

    status = "pass" if failed == 0 else "fail"
    payload = {"status": status, "passed": passed, "failed": failed, "total": len(cases)}
    if feedback_mode == "run":
        payload["results"] = public_results
    else:
        payload["first_failure"] = first_failure
    _emit(payload)


if __name__ == "__main__":
    main()
"""


def _runner_timeout_seconds() -> float:
    timeout_seconds = float(os.getenv("PRACTICE_DOCTEST_TIMEOUT_SECONDS", _DEFAULT_DOCTEST_TIMEOUT_SECONDS))
    if timeout_seconds <= 0:
        timeout_seconds = _DEFAULT_DOCTEST_TIMEOUT_SECONDS
    return timeout_seconds


def _extract_json_payload(text: str) -> dict[str, object] | None:
    for line in reversed(text.splitlines()):
        raw = line.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def _summarize_value(value: Any) -> str:
    if isinstance(value, str):
        return f"str(len={len(value)})"
    if isinstance(value, (bytes, bytearray)):
        return f"bytes(len={len(value)})"
    if isinstance(value, bool):
        return f"bool({value})"
    if value is None:
        return "None"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, list):
        return f"list(len={len(value)})"
    if isinstance(value, tuple):
        return f"tuple(len={len(value)})"
    if isinstance(value, set):
        return f"set(len={len(value)})"
    if isinstance(value, dict):
        return f"dict(len={len(value)})"
    return type(value).__name__


def _build_input_summary(args: list[Any], kwargs: dict[str, Any]) -> str:
    items: list[str] = []
    for index, value in enumerate(args[:_MAX_INPUT_SUMMARY_ITEMS], start=1):
        items.append(f"arg{index}={_summarize_value(value)}")
    remaining = len(args) - min(len(args), _MAX_INPUT_SUMMARY_ITEMS)
    if remaining > 0:
        items.append(f"+{remaining} more args")

    kw_names = sorted(kwargs.keys())
    for key in kw_names[:_MAX_INPUT_SUMMARY_ITEMS]:
        items.append(f"{key}={_summarize_value(kwargs[key])}")
    remaining_kwargs = len(kw_names) - min(len(kw_names), _MAX_INPUT_SUMMARY_ITEMS)
    if remaining_kwargs > 0:
        items.append(f"+{remaining_kwargs} more kwargs")
    return ", ".join(items)


def _hidden_case_label(index: int) -> str:
    return f"Hidden case #{index}"


def _hidden_case_id(index: int, raw_id: Any) -> str:
    raw = str(raw_id or "").strip()
    if not raw or raw.startswith("case-"):
        return f"hidden-{index:02d}"
    return raw


def _failure_type_from_error_message(message: str) -> str:
    text = message.lower()
    if "timed out" in text or "timeout" in text:
        return "Timeout"
    if "failed to import" in text or "import" in text:
        return "Import Error"
    if "syntaxerror" in text or "syntax error" in text:
        return "Syntax Error"
    return "Runtime Error"


def _load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_literal_eval(raw: str) -> Any:
    return ast.literal_eval(raw)


def _public_input_to_args_kwargs(raw_input: Any) -> tuple[list[Any], dict[str, Any]]:
    if isinstance(raw_input, dict):
        args = raw_input.get("args", [])
        kwargs = raw_input.get("kwargs", {})
        if not isinstance(args, list) or not isinstance(kwargs, dict):
            raise ValueError("Public example input dict must contain list 'args' and object 'kwargs'.")
        return args, kwargs
    if not isinstance(raw_input, str):
        raise ValueError("Public example input must be a string or an args/kwargs object.")

    module = ast.parse(raw_input, mode="exec")
    args: list[Any] = []
    for statement in module.body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            raise ValueError("Public example input must be simple assignments.")
        target = statement.targets[0]
        if not isinstance(target, ast.Name):
            raise ValueError("Public example input assignments must target simple names.")
        value = _safe_literal_eval(ast.get_source_segment(raw_input, statement.value) or "")
        args.append(value)
    return args, {}


def _normalize_public_examples(public_examples_path: Path) -> list[dict[str, Any]]:
    payload = _load_json_file(public_examples_path)
    if not isinstance(payload, list):
        raise ValueError("Public examples must be a list.")

    cases: list[dict[str, Any]] = []
    for index, example in enumerate(payload, start=1):
        if not isinstance(example, dict):
            raise ValueError("Each public example must be an object.")
        args, kwargs = _public_input_to_args_kwargs(example.get("input"))
        expected_raw = example.get("expected", example.get("output"))
        if isinstance(expected_raw, str):
            try:
                expected = _safe_literal_eval(expected_raw)
            except (ValueError, SyntaxError):
                expected = expected_raw
        else:
            expected = expected_raw
        cases.append(
            {
                "id": str(example.get("id") or f"example-{index}"),
                "args": args,
                "kwargs": kwargs,
                "expected": expected,
                "input_text": example.get("input"),
            }
        )
    return cases


def _normalize_hidden_cases(hidden_tests_path: Path) -> list[dict[str, Any]]:
    payload = _load_json_file(hidden_tests_path)
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list):
        raise ValueError("Hidden tests must be an object with list field 'cases'.")

    normalized: list[dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError("Each hidden test case must be an object.")
        args = case.get("args", [])
        kwargs = case.get("kwargs", {})
        if not isinstance(args, list) or not isinstance(kwargs, dict):
            raise ValueError("Hidden test case args must be list and kwargs must be object.")
        normalized.append(
            {
                "id": _hidden_case_id(index, case.get("id")),
                "case_label": _hidden_case_label(index),
                "args": args,
                "kwargs": kwargs,
                "expected": case.get("expected"),
                "input_summary": _build_input_summary(args, kwargs),
            }
        )
    return normalized


def _format_function_evaluator_output(payload: dict[str, object], *, feedback_mode: str) -> str:
    total = int(payload.get("total", 0))
    passed = int(payload.get("passed", 0))
    failed = int(payload.get("failed", 0))
    lines = [f"[function-json:{feedback_mode}] total={total} passed={passed} failed={failed}"]

    if feedback_mode == "run":
        results = payload.get("results")
        if isinstance(results, list):
            for result in results[:_MAX_FAILURE_DETAILS]:
                if not isinstance(result, dict):
                    continue
                lines.append(
                    f"- {result.get('id', 'case')}: {'pass' if result.get('passed') else 'fail'}"
                )
    else:
        first_failure = payload.get("first_failure")
        if isinstance(first_failure, dict):
            lines.append(
                f"- {first_failure.get('case_label', first_failure.get('case_id', 'case'))}: "
                f"{first_failure.get('failure_type', 'Failure')} - {first_failure.get('message', 'failure')}"
            )
    if "error" in payload:
        lines.append(f"[function-json] error: {payload['error']}")
    return "\n".join(lines).strip() + "\n"


def _function_json_feedback_from_payload(payload: dict[str, object], *, feedback_mode: str) -> dict[str, Any]:
    total = int(payload.get("total", 0))
    passed = int(payload.get("passed", 0))
    failed = int(payload.get("failed", 0))
    status = str(payload.get("status", "error"))
    feedback: dict[str, Any] = {"mode": feedback_mode, "status": status}
    error_message = str(payload.get("error", "")).strip()
    if error_message:
        feedback["error"] = error_message

    if feedback_mode == "run":
        results = payload.get("results")
        feedback["summary"] = {"total": total, "passed": passed, "failed": failed}
        feedback["public_examples"] = results if isinstance(results, list) else []
    else:
        feedback["summary"] = {
            "total_hidden": total,
            "passed_hidden": passed,
            "failed_hidden": failed,
        }
        first_failure = payload.get("first_failure")
        if isinstance(first_failure, dict):
            feedback["first_failure"] = first_failure
        elif error_message:
            feedback["first_failure"] = {
                "case_id": "runner",
                "case_label": "Hidden case",
                "message": error_message,
                "failure_type": _failure_type_from_error_message(error_message),
            }
        else:
            feedback["first_failure"] = None
    return feedback


def _run_doctest_evaluation(
    conn: sqlite3.Connection,
    problem_row: sqlite3.Row,
    *,
    solution_content: str,
    run_dir: Path,
    run_user: int | str,
    log_callback: LogCallback | None = None,
) -> RunResult:
    composed = _compose_doctest_module(
        doctest_text=str(problem_row["doctest"]),
        solution_code=solution_content,
    )
    expected_tests = _count_expected_tests_in_doctest_text(str(problem_row["doctest"]))
    if expected_tests == 0:
        # Backward compatibility for legacy rows where doctest text may be missing.
        expected_tests = _count_expected_tests(composed)
    run_solution = run_dir / f"solution_user_{run_user}.py"
    run_solution.write_text(composed, encoding="utf-8")

    bundle_id_raw = problem_row["bundle_id"]
    if bundle_id_raw is not None:
        for asset in db.list_bundle_assets(conn, bundle_id=int(bundle_id_raw)):
            rel_str = str(asset["relpath"])
            dest = run_dir / rel_str
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(bytes(asset["content"]))

    cmd = [sys.executable, "-I", "-m", "doctest", str(run_solution)]
    returncode, stdout, stderr = _execute_doctest(
        cmd,
        cwd=run_dir,
        log_callback=log_callback,
        timeout_seconds=_runner_timeout_seconds(),
    )

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

    return RunResult(
        status=status,
        passed=passed_count,
        failed=failed_count,
        exit_code=returncode,
        stdout=stdout,
        stderr=stderr,
        duration_ms=0,
    )


def _run_function_json_evaluation(
    conn: sqlite3.Connection,
    problem_row: sqlite3.Row,
    *,
    solution_content: str,
    run_dir: Path,
    run_user: int | str,
    feedback_mode: str,
    log_callback: LogCallback | None = None,
) -> RunResult:
    entry_function = str(problem_row["entry_function"] or "").strip()
    if not entry_function:
        return RunResult(
            status="error",
            passed=0,
            failed=0,
            exit_code=2,
            stdout="",
            stderr="[runner] Missing entry_function for function_json problem.\n",
            duration_ms=0,
        )

    bundle_id_raw = problem_row["bundle_id"]
    if bundle_id_raw is None:
        return RunResult(
            status="error",
            passed=0,
            failed=0,
            exit_code=2,
            stdout="",
            stderr="[runner] Missing bundle_id for function_json problem.\n",
            duration_ms=0,
        )

    bundle = db.get_bundle_by_id(conn, int(bundle_id_raw))
    if bundle is None:
        return RunResult(
            status="error",
            passed=0,
            failed=0,
            exit_code=2,
            stdout="",
            stderr="[runner] Bundle not found for function_json problem.\n",
            duration_ms=0,
        )

    problem_dir_relpath = str(problem_row["problem_dir_relpath"] or "").strip()
    if not problem_dir_relpath:
        return RunResult(
            status="error",
            passed=0,
            failed=0,
            exit_code=2,
            stdout="",
            stderr="[runner] Missing problem_dir_relpath for function_json problem.\n",
            duration_ms=0,
        )

    source_root = Path(str(bundle["source_root"]))
    problem_dir = source_root / problem_dir_relpath
    if feedback_mode == "run":
        cases_path = problem_dir / "public_examples.json"
        missing_label = "Public examples"
    else:
        cases_path = problem_dir / "hidden_tests.json"
        missing_label = "Hidden tests"
    if not cases_path.exists():
        return RunResult(
            status="error",
            passed=0,
            failed=0,
            exit_code=2,
            stdout="",
            stderr=f"[runner] {missing_label} not found: {cases_path}\n",
            duration_ms=0,
        )

    try:
        if feedback_mode == "run":
            cases = _normalize_public_examples(cases_path)
        else:
            cases = _normalize_hidden_cases(cases_path)
    except (ValueError, json.JSONDecodeError, SyntaxError) as exc:
        return RunResult(
            status="error",
            passed=0,
            failed=0,
            exit_code=2,
            stdout="",
            stderr=f"[runner] Failed to prepare {feedback_mode} cases: {exc}\n",
            duration_ms=0,
        )

    run_solution = run_dir / f"solution_user_{run_user}.py"
    run_solution.write_text(solution_content.rstrip() + "\n", encoding="utf-8")
    run_cases = run_dir / "_function_cases.json"
    run_cases.write_text(json.dumps({"cases": cases}, ensure_ascii=False), encoding="utf-8")

    evaluator_script = run_dir / "_function_eval.py"
    evaluator_script.write_text(_FUNCTION_EVAL_SCRIPT, encoding="utf-8")

    cmd = [
        sys.executable,
        "-I",
        str(evaluator_script),
        str(run_cases),
        str(run_solution),
        entry_function,
        feedback_mode,
    ]
    returncode, stdout, stderr = _execute_doctest(
        cmd,
        cwd=run_dir,
        log_callback=log_callback,
        timeout_seconds=_runner_timeout_seconds(),
    )
    payload = _extract_json_payload(stdout)
    if payload is None:
        return RunResult(
            status="error",
            passed=0,
            failed=0,
            exit_code=returncode,
            stdout=stdout,
            stderr=stderr or "[runner] Failed to parse evaluator output.\n",
            duration_ms=0,
        )

    status = str(payload.get("status", "error"))
    if status not in {"pass", "fail", "error"}:
        status = "error"

    feedback = _function_json_feedback_from_payload(payload, feedback_mode=feedback_mode)
    return RunResult(
        status=status,
        passed=int(payload.get("passed", 0)),
        failed=int(payload.get("failed", 0)),
        exit_code=returncode,
        stdout=_format_function_evaluator_output(payload, feedback_mode=feedback_mode),
        stderr=stderr,
        duration_ms=0,
        feedback=feedback,
    )


def run_problem(
    conn: sqlite3.Connection,
    paths: Paths,
    problem_row: sqlite3.Row,
    *,
    user_id: int | None = None,
    solution_content: str | None = None,
    function_json_feedback_mode: str | None = None,
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

    solution_hash = _sha256_text(solution_content)
    attempt_id = db.create_attempt(
        conn,
        int(problem_row["id"]),
        solution_hash,
        user_id=user_id,
    )

    run_user = user_id if user_id is not None else "anon"
    mode = str(problem_row["evaluation_mode"] or "doctest").strip() or "doctest"
    feedback_mode = function_json_feedback_mode or "submit"
    run_dir = _create_attempt_workspace(paths, attempt_id)
    start = time.monotonic()
    try:
        if mode == "function_json":
            result = _run_function_json_evaluation(
                conn,
                problem_row,
                solution_content=solution_content,
                run_dir=run_dir,
                run_user=run_user,
                feedback_mode=feedback_mode,
                log_callback=log_callback,
            )
        else:
            result = _run_doctest_evaluation(
                conn,
                problem_row,
                solution_content=solution_content,
                run_dir=run_dir,
                run_user=run_user,
                log_callback=log_callback,
            )
    finally:
        if not _should_preserve_attempt_workspace():
            shutil.rmtree(run_dir, ignore_errors=True)

    result.duration_ms = int((time.monotonic() - start) * 1000)
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
