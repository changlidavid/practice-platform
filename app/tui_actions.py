from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Callable

from . import db, opener, runner
from .config import Paths
from .models import RunResult


LogCallback = Callable[[str, str], None]


def problem_by_id(conn: sqlite3.Connection, problem_id: int) -> sqlite3.Row:
    row = db.get_problem(conn, str(problem_id))
    if row is None:
        raise ValueError(f"Unknown problem id: {problem_id}")
    return row


def prepare_problem_view(problem_row: sqlite3.Row) -> tuple[str, Path, Path]:
    from .config import get_paths

    paths = get_paths()
    slug = str(problem_row["slug"]).replace("/", "__").replace(":", "__")
    solution_path = paths.solutions_dir / f"{slug}.py"
    prompt_path = paths.workspace_root / "_virtual_prompt.py"

    conn = db.connect(paths.db_path)
    try:
        user_id = db.ensure_cli_user(conn)
        solution = db.ensure_user_solution(conn, user_id=user_id, problem_row=problem_row)
        solution_path.write_text(str(solution["content"]), encoding="utf-8")
    finally:
        conn.close()

    preview = opener.prompt_preview_text(str(problem_row["template_code"]))
    return preview, solution_path, prompt_path


def launch_editor_for_solution(solution_path: Path) -> bool:
    return opener.launch_editor(solution_path, check=True)


def run_problem_by_id(
    *,
    paths: Paths,
    problem_id: int,
    log_callback: LogCallback | None = None,
) -> tuple[int, RunResult]:
    conn = db.connect(paths.db_path)
    try:
        row = problem_by_id(conn, problem_id)
        return runner.run_problem(conn, paths, row, log_callback=log_callback)
    finally:
        conn.close()
