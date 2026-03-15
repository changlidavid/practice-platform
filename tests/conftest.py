from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, repo_root: Path) -> Path:
    practice_home = tmp_path / ".practice"
    hidden_tests_root = tmp_path / "hidden-tests"
    monkeypatch.setenv("PRACTICE_HOME", str(practice_home))
    monkeypatch.setenv("PRACTICE_BUNDLE_PATH", str(repo_root / "9021"))
    monkeypatch.setenv("PRACTICE_HIDDEN_TESTS_ROOT", str(hidden_tests_root))
    from app import db, importer
    from app.config import ensure_workspace, get_paths

    paths = get_paths()
    ensure_workspace(paths)
    hidden_tests_root.mkdir(parents=True, exist_ok=True)
    conn = db.connect(paths.db_path)
    try:
        db.init_db(conn)
        importer.ensure_imported(conn, paths)
    finally:
        conn.close()
    return practice_home
