from __future__ import annotations

import subprocess
import sys

from app import db
from app import runner
from app.config import get_paths


def test_execute_doctest_timeout_returns_124_and_timeout_message(monkeypatch):
    monkeypatch.setenv("PRACTICE_DOCTEST_OUTPUT_MAX_BYTES", "262144")
    cmd = [sys.executable, "-c", "import time; time.sleep(1.0)"]
    returncode, stdout, stderr = runner._execute_doctest(
        cmd,
        cwd=get_paths().repo_root,
        timeout_seconds=0.1,
    )
    assert returncode == 124
    assert stdout == ""
    assert "[runner] Doctest timed out after 0.1s.\n" in stderr


def test_execute_doctest_timeout_terminates_then_kills_process_group(monkeypatch):
    class FakeProc:
        pid = 123

        def __init__(self) -> None:
            self.wait_calls = 0

        def wait(self, timeout: float | None = None):
            self.wait_calls += 1
            if self.wait_calls == 1:
                raise subprocess.TimeoutExpired(cmd=["x"], timeout=timeout or 0.0)
            return 0

    kill_calls: list[tuple[int, int]] = []

    monkeypatch.setattr(runner.os, "name", "posix", raising=False)
    monkeypatch.setattr(runner.os, "killpg", lambda pid, sig: kill_calls.append((pid, sig)))
    proc = FakeProc()
    runner._terminate_process_tree(proc, grace_seconds=0.01)
    assert kill_calls == [
        (123, runner.signal.SIGTERM),
        (123, runner.signal.SIGKILL),
    ]


def test_execute_doctest_caps_stdout_and_appends_marker(monkeypatch):
    monkeypatch.setenv("PRACTICE_DOCTEST_OUTPUT_MAX_BYTES", "64")
    cmd = [sys.executable, "-c", "print('A' * 200)"]
    returncode, stdout, stderr = runner._execute_doctest(
        cmd,
        cwd=get_paths().repo_root,
        timeout_seconds=2.0,
    )
    assert returncode == 0
    assert stderr == ""
    assert "[runner] stdout truncated at 64 bytes.\n" in stdout


def test_execute_doctest_caps_stderr_and_appends_marker(monkeypatch):
    monkeypatch.setenv("PRACTICE_DOCTEST_OUTPUT_MAX_BYTES", "64")
    cmd = [sys.executable, "-c", "import sys; sys.stderr.write('E' * 200)"]
    returncode, stdout, stderr = runner._execute_doctest(
        cmd,
        cwd=get_paths().repo_root,
        timeout_seconds=2.0,
    )
    assert returncode == 0
    assert stdout == ""
    assert "[runner] stderr truncated at 64 bytes.\n" in stderr


def test_truncated_output_does_not_change_status_mapping(isolated_env, monkeypatch):
    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = db.get_problem(conn, "sample_1")
        assert row is not None

        def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
            _ = (cmd, cwd, log_callback, timeout_seconds)
            stdout = "[runner] stdout truncated at 262144 bytes.\n"
            return 1, stdout, ""

        monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)
        _, result = runner.run_problem(conn, paths, row)
        assert result.status == "fail"
    finally:
        conn.close()


def test_build_container_cmd_normalizes_python_interpreter_and_rewrites_workspace_paths():
    cmd = ["/usr/local/bin/python3", "-I", "-m", "doctest", "/tmp/run/solution.py"]
    built = runner._build_container_cmd(cmd, cwd=runner.Path("/tmp/run"))
    assert built[0:2] == ["docker", "run"]
    assert "python:3.12-slim" in built
    image_index = built.index("python:3.12-slim")
    container_exec = built[image_index + 1 :]
    assert container_exec[0] == "python3"
    assert "/workspace/solution.py" in container_exec
