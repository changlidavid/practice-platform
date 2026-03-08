from __future__ import annotations

import sqlite3
from pathlib import Path

from app import db


def test_upsert_problem_supports_legacy_prompt_and_solution_path_columns(tmp_path: Path):
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(
            """
            CREATE TABLE problems (
                id INTEGER PRIMARY KEY,
                bundle_id INTEGER,
                slug TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                template_code TEXT NOT NULL DEFAULT '',
                doctest TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT '',
                source_relpath TEXT NOT NULL DEFAULT '',
                prompt_path TEXT NOT NULL,
                solution_path TEXT NOT NULL,
                assets_manifest_json TEXT NOT NULL DEFAULT '[]',
                content_hash TEXT NOT NULL DEFAULT ''
            )
            """
        )

        db.upsert_problem(
            conn,
            bundle_id=None,
            slug="final:1.question_1",
            title="Question 1",
            description="desc",
            template_code='"""prompt"""',
            doctest="",
            source_relpath="1/question_1.py",
            assets_manifest=[],
            content_hash="abc123",
        )

        row = conn.execute(
            "SELECT prompt_path, solution_path FROM problems WHERE slug = ?",
            ("final:1.question_1",),
        ).fetchone()
        assert row is not None
        assert str(row["prompt_path"]) == "compat://prompt/1/question_1.py"
        assert str(row["solution_path"]) == "compat://solution/final:1.question_1.py"
    finally:
        conn.close()
