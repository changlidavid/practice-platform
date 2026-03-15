from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app import db, runner
from app.config import get_paths


def _docker_available() -> bool:
    try:
        proc = subprocess.run(
            ["docker", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


pytestmark = pytest.mark.skipif(
    not _docker_available(),
    reason="Docker runtime is required for container-isolation runner tests.",
)


def _upsert_ephemeral_problem(conn, *, slug: str, doctest_text: str):
    db.upsert_problem(
        conn,
        bundle_id=None,
        slug=slug,
        title=slug,
        description="security test",
        template_code="# security test\n",
        doctest=doctest_text,
        source_relpath=f"{slug}.py",
        assets_manifest=[],
        content_hash=slug,
    )
    row = db.get_problem(conn, slug)
    assert row is not None
    return row


def _configure_container_runner(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    shared = tmp_path / "runner_jobs"
    shared.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PRACTICE_RUNNER_MOUNT_MODE", "bind")
    monkeypatch.setenv("PRACTICE_RUNNER_SHARED_DIR", str(shared))
    monkeypatch.setenv("PRACTICE_RUNNER_IMAGE", "python:3.12-slim")
    monkeypatch.setenv("PRACTICE_RUNNER_MEMORY", "128m")
    monkeypatch.setenv("PRACTICE_RUNNER_PIDS_LIMIT", "64")
    monkeypatch.setenv("PRACTICE_RUNNER_CPUS", "0.50")
    return shared


def test_submitted_code_cannot_read_app_env_secrets(isolated_env, monkeypatch, tmp_path):
    _configure_container_runner(monkeypatch, tmp_path)
    monkeypatch.setenv("SMTP_PASSWORD", "TOP_SECRET_FOR_WEB_ONLY")

    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = _upsert_ephemeral_problem(
            conn,
            slug="security_env_hidden",
            doctest_text='>>> import os\n>>> print(os.environ.get("SMTP_PASSWORD"))\nNone\n',
        )
        _, result = runner.run_problem(conn, paths, row, solution_content="# noop\n")
    finally:
        conn.close()

    print("STATUS:", result.status)
    print("EXIT:", result.exit_code)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.status == "pass"


def test_submitted_code_cannot_access_main_db_path(isolated_env, monkeypatch, tmp_path):
    _configure_container_runner(monkeypatch, tmp_path)

    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = _upsert_ephemeral_problem(
            conn,
            slug="security_db_hidden",
            doctest_text='>>> import os\n>>> print(os.path.exists("/data/practice.db"))\nFalse\n',
        )
        _, result = runner.run_problem(conn, paths, row, solution_content="# noop\n")
    finally:
        conn.close()

    assert result.status == "pass"


def test_submitted_code_has_no_outbound_network(isolated_env, monkeypatch, tmp_path):
    _configure_container_runner(monkeypatch, tmp_path)

    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = _upsert_ephemeral_problem(
            conn,
            slug="security_no_network",
            doctest_text=(
                ">>> import socket\n"
                ">>> ok = True\n"
                ">>> try:\n"
                "...     socket.create_connection(('example.com', 80), timeout=1)\n"
                "... except OSError:\n"
                "...     ok = False\n"
                ">>> print(ok)\n"
                "False\n"
            ),
        )
        _, result = runner.run_problem(conn, paths, row, solution_content="# noop\n")
    finally:
        conn.close()

    assert result.status == "pass"


def test_container_timeout_and_workspace_cleanup(isolated_env, monkeypatch, tmp_path):
    shared = _configure_container_runner(monkeypatch, tmp_path)
    monkeypatch.setenv("PRACTICE_DOCTEST_TIMEOUT_SECONDS", "0.3")

    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = _upsert_ephemeral_problem(
            conn,
            slug="security_timeout_cleanup",
            doctest_text=">>> while True:\n...     pass\n",
        )
        _, result = runner.run_problem(conn, paths, row, solution_content="# noop\n")
    finally:
        conn.close()

    assert result.exit_code == 124
    assert result.status == "error"
    assert list(shared.glob("attempt_*")) == []
