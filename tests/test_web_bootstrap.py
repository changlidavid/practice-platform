from __future__ import annotations

from app import db
from app.config import ensure_workspace, get_paths
from app.web import create_app


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

    _ = create_app()

    conn = db.connect(paths.db_path)
    try:
        count_after = conn.execute("SELECT COUNT(*) AS c FROM problems").fetchone()
        assert count_after is not None
        assert int(count_after["c"]) > 0
    finally:
        conn.close()
