from __future__ import annotations

from pathlib import Path

from app import db
from app.cli import main
from app.config import get_paths


def test_run_sample4_stages_dictionary_asset(isolated_env, monkeypatch):
    import app.runner as runner

    def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
        _ = (cmd, log_callback, timeout_seconds)
        run_dir = Path(cwd)
        assert (run_dir / "dictionary.txt").exists()
        stdout = "7 tests in 2 items.\n7 passed and 0 failed.\nTest passed.\n"
        return 0, stdout, ""

    monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)

    rc = main(["run", "sample_4"])
    assert rc == 0


def test_run_sample7_stages_word_search_assets(isolated_env, monkeypatch):
    import app.runner as runner

    def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
        _ = (cmd, log_callback, timeout_seconds)
        run_dir = Path(cwd)
        assert (run_dir / "word_search_1.txt").exists()
        assert (run_dir / "word_search_2.txt").exists()
        stdout = "10 tests in 2 items.\n10 passed and 0 failed.\nTest passed.\n"
        return 0, stdout, ""

    monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)

    rc = main(["run", "sample_7"])
    assert rc == 0


def test_run_persists_attempt(isolated_env, monkeypatch):
    import app.runner as runner

    def fake_execute_doctest(cmd, *, cwd, log_callback, timeout_seconds):
        _ = (cmd, cwd, log_callback, timeout_seconds)
        stdout = "7 tests in 2 items.\n7 passed and 0 failed.\nTest passed.\n"
        return 0, stdout, ""

    monkeypatch.setattr(runner, "_execute_doctest", fake_execute_doctest)

    rc = main(["run", "sample_1"])
    assert rc == 0

    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        attempts = conn.execute("SELECT COUNT(*) AS c FROM attempts").fetchone()["c"]
        assert attempts >= 1
    finally:
        conn.close()
