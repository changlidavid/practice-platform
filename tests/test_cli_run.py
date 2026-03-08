from __future__ import annotations

from app import db
from app.cli import main
from app.config import get_paths


def test_run_marks_failed_attempt_when_doctest_fails(isolated_env, monkeypatch):
    import app.runner as runner

    def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
        _ = (cmd, cwd, log_callback, timeout_seconds)
        stdout = "7 tests in 2 items.\n6 passed and 1 failed.\n***Test Failed*** 1 failures.\n"
        return 1, stdout, ""

    monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)

    rc = main(["run", "sample_1"])
    assert rc == 1

    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = conn.execute(
            "SELECT status, failed_count FROM attempts ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row["status"] == "fail"
        assert row["failed_count"] >= 1
    finally:
        conn.close()


def test_run_zero_tests_is_not_pass(isolated_env, monkeypatch):
    import app.runner as runner

    def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
        _ = (cmd, cwd, log_callback, timeout_seconds)
        stdout = "1 item had no tests:\n    solution_user_1\n0 tests in 1 items.\n0 passed and 0 failed.\nTest passed.\n"
        return 0, stdout, ""

    monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)
    monkeypatch.setattr(runner, "_count_expected_tests", lambda _source: 0)

    rc = main(["run", "sample_1"])
    assert rc == 1

    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = conn.execute(
            "SELECT status, passed_count, failed_count FROM attempts ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row["status"] == "error"
        assert row["passed_count"] == 0
        assert row["failed_count"] == 0
    finally:
        conn.close()


def test_run_quiet_success_output_is_still_pass(isolated_env, monkeypatch):
    import app.runner as runner

    def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
        # Non-verbose doctest can emit no summary on success.
        _ = (cmd, cwd, log_callback, timeout_seconds)
        return 0, "", ""

    monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)

    rc = main(["run", "sample_1"])
    assert rc == 0

    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = conn.execute(
            "SELECT status, passed_count, failed_count FROM attempts ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        assert row["status"] == "pass"
        assert row["passed_count"] > 0
        assert row["failed_count"] == 0
    finally:
        conn.close()
