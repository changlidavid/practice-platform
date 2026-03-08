from __future__ import annotations

from pathlib import Path

import pytest

from app import db
from app import runner
from app.config import get_paths


def test_run_uses_temp_workspace_under_runs_dir(isolated_env, monkeypatch):
    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = db.get_problem(conn, "sample_1")
        assert row is not None
        seen_cwd: list[Path] = []

        def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
            _ = (cmd, log_callback, timeout_seconds)
            seen_cwd.append(Path(cwd))
            return 0, "", ""

        monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)
        attempt_id, _ = runner.run_problem(conn, paths, row)
        assert attempt_id > 0
        assert len(seen_cwd) == 1
        run_dir = seen_cwd[0]
        assert run_dir.parent == paths.runs_dir
        assert run_dir.name.startswith(f"attempt_{attempt_id}_")
    finally:
        conn.close()


def test_run_cleans_temp_workspace_on_success(isolated_env, monkeypatch):
    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = db.get_problem(conn, "sample_1")
        assert row is not None
        seen_cwd: list[Path] = []

        def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
            _ = (cmd, log_callback, timeout_seconds)
            seen_cwd.append(Path(cwd))
            return 0, "", ""

        monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)
        runner.run_problem(conn, paths, row)
        assert len(seen_cwd) == 1
        assert not seen_cwd[0].exists()
    finally:
        conn.close()


def test_run_cleans_temp_workspace_on_execution_error(isolated_env, monkeypatch):
    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = db.get_problem(conn, "sample_1")
        assert row is not None
        seen_cwd: list[Path] = []

        def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
            _ = (cmd, log_callback, timeout_seconds)
            seen_cwd.append(Path(cwd))
            raise RuntimeError("boom")

        monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)
        with pytest.raises(RuntimeError, match="boom"):
            runner.run_problem(conn, paths, row)
        assert len(seen_cwd) == 1
        assert not seen_cwd[0].exists()
    finally:
        conn.close()


def test_assets_are_staged_in_temp_workspace(isolated_env, monkeypatch):
    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = db.get_problem(conn, "sample_7")
        assert row is not None

        def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
            _ = (cmd, log_callback, timeout_seconds)
            run_dir = Path(cwd)
            assert (run_dir / "word_search_1.txt").exists()
            assert (run_dir / "word_search_2.txt").exists()
            return 0, "", ""

        monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)
        runner.run_problem(conn, paths, row)
    finally:
        conn.close()
