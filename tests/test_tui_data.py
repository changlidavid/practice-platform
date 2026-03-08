from __future__ import annotations

from app import db
from app.cli import main
from app.config import get_paths
from app.tui_data import fetch_attempt_history, fetch_bundle_names, fetch_problem_rows


def test_fetch_problem_rows_and_filters(isolated_env):
    assert main(["list"]) == 0

    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        all_rows = fetch_problem_rows(conn)
        assert any(row.slug == "sample_1" for row in all_rows)

        searched = fetch_problem_rows(conn, search="sample_1")
        assert len(searched) >= 1
        assert all("sample_1" in row.slug for row in searched)

        bundles = fetch_bundle_names(conn)
        assert "9021" in bundles

        bundled = fetch_problem_rows(conn, bundle_filter="9021")
        assert len(bundled) >= 1
    finally:
        conn.close()


def test_fetch_attempt_history_after_run(isolated_env, monkeypatch):
    import app.runner as runner

    def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
        _ = (cmd, cwd, log_callback, timeout_seconds)
        stdout = "7 tests in 2 items.\n7 passed and 0 failed.\nTest passed.\n"
        return 0, stdout, ""

    monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)

    assert main(["run", "sample_1"]) == 0

    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = db.get_problem(conn, "sample_1")
        assert row is not None
        history = fetch_attempt_history(conn, int(row["id"]))
        assert len(history) >= 1
        assert history[0].status == "pass"
    finally:
        conn.close()
