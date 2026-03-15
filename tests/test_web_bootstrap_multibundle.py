from __future__ import annotations

from app import db, importer
from app.config import ensure_workspace, get_paths


def test_create_app_bootstraps_multiple_bundles_and_skips_missing_path(
    tmp_path, monkeypatch, repo_root
):
    practice_home = tmp_path / ".practice"
    monkeypatch.setenv("PRACTICE_HOME", str(practice_home))
    monkeypatch.setenv(
        "PRACTICE_BUNDLE_PATHS",
        "9021,final,does-not-exist-bundle",
    )

    paths = get_paths()
    ensure_workspace(paths)

    # Seed a partially populated database with only the 9021 bundle.
    conn = db.connect(paths.db_path)
    try:
        db.init_db(conn)
        importer.import_bundle(conn, paths, repo_root / "9021")
        count_before = conn.execute("SELECT COUNT(*) AS c FROM problems").fetchone()
        assert count_before is not None
        assert int(count_before["c"]) == 7
    finally:
        conn.close()


def test_create_app_prunes_bundles_removed_from_bundle_paths(
    tmp_path, monkeypatch, repo_root
):
    practice_home = tmp_path / ".practice"
    monkeypatch.setenv("PRACTICE_HOME", str(practice_home))
    monkeypatch.setenv(
        "PRACTICE_BUNDLE_PATHS",
        "9021,final,problems",
    )

    from app.web import create_app

    _ = create_app()

    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        slugs_before = {str(row["slug"]) for row in db.list_problems(conn)}
        assert "sample_1" in slugs_before
        assert any(slug.startswith("final:") for slug in slugs_before)
        assert any(slug.startswith("average_of_digits_common_to") for slug in slugs_before)
    finally:
        conn.close()

    monkeypatch.setenv("PRACTICE_BUNDLE_PATHS", "problems")
    _ = create_app()

    conn = db.connect(paths.db_path)
    try:
        rows_after = db.list_problems(conn)
        slugs_after = {str(row["slug"]) for row in rows_after}
        bundle_names_after = {str(row["bundle_name"]) for row in rows_after}
        assert "sample_1" not in slugs_after
        assert not any(slug.startswith("final:") for slug in slugs_after)
        assert bundle_names_after == {"problems"}
    finally:
        conn.close()

    from app.web import create_app

    _ = create_app()

    conn = db.connect(paths.db_path)
    try:
        count_after = conn.execute("SELECT COUNT(*) AS c FROM problems").fetchone()
        assert count_after is not None
        assert int(count_after["c"]) > int(count_before["c"])
        assert int(count_after["c"]) >= 100
    finally:
        conn.close()
