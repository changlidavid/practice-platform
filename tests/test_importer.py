from __future__ import annotations

from app import db, importer
from app.config import ensure_workspace, get_paths


def test_importer_creates_problem_and_asset_snapshots(isolated_env):
    paths = get_paths()
    ensure_workspace(paths)

    conn = db.connect(paths.db_path)
    try:
        db.init_db(conn)
        importer.ensure_imported(conn, paths)

        rows = db.list_problems(conn)
        assert len(rows) == 7
        slugs = {row["slug"] for row in rows}
        assert "sample_4" in slugs
        assert "sample_7" in slugs

        bundle = conn.execute("SELECT * FROM bundles ORDER BY id DESC LIMIT 1").fetchone()
        assert bundle is not None
        assets = conn.execute(
            "SELECT relpath FROM bundle_assets WHERE bundle_id = ? ORDER BY relpath ASC",
            (int(bundle["id"]),),
        ).fetchall()
        relpaths = {str(row["relpath"]) for row in assets}
        assert "dictionary.txt" in relpaths
        assert "word_search_1.txt" in relpaths
        assert "word_search_2.txt" in relpaths
    finally:
        conn.close()


def test_ensure_user_solution_falls_back_when_template_code_empty(isolated_env):
    paths = get_paths()
    ensure_workspace(paths)

    conn = db.connect(paths.db_path)
    try:
        db.init_db(conn)
        importer.ensure_imported(conn, paths)

        row = db.get_problem(conn, "sample_3")
        assert row is not None
        problem_id = int(row["id"])

        # Simulate a legacy bad row where template_code is empty.
        conn.execute("UPDATE problems SET template_code = '' WHERE id = ?", (problem_id,))
        conn.commit()

        row_with_empty_template = db.get_problem(conn, str(problem_id))
        assert row_with_empty_template is not None

        user_id = db.ensure_cli_user(conn)
        solution = db.ensure_user_solution(
            conn,
            user_id=user_id,
            problem_row=row_with_empty_template,
        )
        assert str(solution["content"]).strip() != ""

        refreshed = db.get_problem(conn, str(problem_id))
        assert refreshed is not None
        assert str(refreshed["template_code"]).strip() != ""
    finally:
        conn.close()


def test_ensure_user_solution_repairs_existing_blank_user_solution(isolated_env):
    paths = get_paths()
    ensure_workspace(paths)

    conn = db.connect(paths.db_path)
    try:
        db.init_db(conn)
        importer.ensure_imported(conn, paths)

        row = db.get_problem(conn, "sample_4")
        assert row is not None
        user_id = db.ensure_cli_user(conn)
        problem_id = int(row["id"])

        db.upsert_user_solution(conn, user_id=user_id, problem_id=problem_id, content="   ")
        repaired = db.ensure_user_solution(conn, user_id=user_id, problem_row=row)
        assert str(repaired["content"]).strip() != ""
    finally:
        conn.close()
