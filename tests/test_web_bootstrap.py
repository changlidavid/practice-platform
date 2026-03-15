from __future__ import annotations

import os

from app import db
from app.config import ensure_workspace, get_paths, load_env_file


def test_create_app_bootstraps_problems_when_database_is_empty(tmp_path, monkeypatch, repo_root):
    practice_home = tmp_path / ".practice"
    monkeypatch.setenv("PRACTICE_HOME", str(practice_home))
    monkeypatch.setenv("PRACTICE_BUNDLE_PATH", str(repo_root / "9021"))

    paths = get_paths()
    ensure_workspace(paths)

    conn = db.connect(paths.db_path)
    try:
        db.init_db(conn)
        count_before = conn.execute("SELECT COUNT(*) AS c FROM problems").fetchone()
        assert count_before is not None
        assert int(count_before["c"]) == 0
    finally:
        conn.close()


def test_load_env_file_overrides_existing_bundle_paths(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("PRACTICE_BUNDLE_PATHS=problems,structured\n", encoding="utf-8")
    monkeypatch.setenv("PRACTICE_BUNDLE_PATHS", "problems")

    load_env_file(tmp_path)

    assert os.environ["PRACTICE_BUNDLE_PATHS"] == "problems,structured"

    from app.web import create_app

    _ = create_app()

    conn = db.connect(paths.db_path)
    try:
        count_after = conn.execute("SELECT COUNT(*) AS c FROM problems").fetchone()
        assert count_after is not None
        assert int(count_after["c"]) > 0
    finally:
        conn.close()
