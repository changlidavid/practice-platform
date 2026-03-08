from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

from . import db, importer, opener, problem_index, runner
from .config import ensure_workspace, get_paths
from .statements import ensure_statement


def bootstrap(conn: sqlite3.Connection) -> None:
    db.init_db(conn)


def cmd_list(conn: sqlite3.Connection) -> int:
    rows = problem_index.list_rows(conn)
    if not rows:
        print("No problems imported.")
        return 0

    print(
        f"{'id':>3}  {'bundle':<12}  {'slug':<24}  {'source':<20}  "
        f"{'attempts':>8}  {'status':<8}  {'last_run'}"
    )
    for row in rows:
        last_run = row["last_run"] or "-"
        print(
            f"{row['id']:>3}  {row['bundle_name']:<12}  {row['slug']:<24}  {row['source_relpath']:<20}  "
            f"{row['attempts']:>8}  {row['last_status']:<8}  {last_run}"
        )
    return 0


def _resolve_problem(conn: sqlite3.Connection, problem_ref: str) -> sqlite3.Row:
    row = db.get_problem(conn, problem_ref)
    if row is None:
        raise ValueError(f"Unknown problem: {problem_ref}")
    return row


def cmd_open(conn: sqlite3.Connection, problem_ref: str) -> int:
    row = _resolve_problem(conn, problem_ref)
    paths = get_paths()
    slug = str(row["slug"]).replace("/", "__").replace(":", "__")
    solution_path = paths.solutions_dir / f"{slug}.py"
    cli_user_id = db.ensure_cli_user(conn)
    user_solution = db.ensure_user_solution(conn, user_id=cli_user_id, problem_row=row)
    solution_path.write_text(str(user_solution["content"]), encoding="utf-8")
    statement_path = ensure_statement(get_paths(), row)
    preview = opener.prompt_preview_text(str(row["template_code"]))
    opened = opener.open_in_editor(solution_path)
    if opened and solution_path.exists():
        db.upsert_user_solution(
            conn,
            user_id=cli_user_id,
            problem_id=int(row["id"]),
            content=solution_path.read_text(encoding="utf-8"),
        )

    print(f"Solution: {solution_path}")
    print(f"Prompt:   db://problems/{row['id']}/template_code")
    print(f"Statement:{statement_path}")
    if not opened:
        print("\n$EDITOR is not set; open the solution file manually.")
    print("\nPreview:\n")
    print(preview)
    return 0


def cmd_run(conn: sqlite3.Connection, problem_ref: str) -> int:
    row = _resolve_problem(conn, problem_ref)
    attempt_id, result = runner.run_problem(conn, get_paths(), row)

    print(f"Attempt: {attempt_id}")
    print(f"Status:  {result.status}")
    print(f"Passed:  {result.passed}")
    print(f"Failed:  {result.failed}")
    print(f"Exit:    {result.exit_code}")
    print(f"TimeMs:  {result.duration_ms}")

    if result.status != "pass":
        print("\nTest output:\n")
        combined = (result.stdout + "\n" + result.stderr).strip()
        print(combined[:4000])
    return 0 if result.status == "pass" else 1


def cmd_import(conn: sqlite3.Connection, bundle_path: str) -> int:
    source_root = Path(bundle_path).expanduser().resolve()
    info = importer.import_bundle(conn, get_paths(), source_root)
    print(f"Imported bundle: {info['bundle_name']}_{str(info['snapshot_hash'])[:12]}")
    print(f"Problems: {info['problem_count']}")
    print(f"Assets:   {info['asset_count']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline local coding practice CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List imported problems")

    p_open = sub.add_parser("open", help="Open a problem solution")
    p_open.add_argument("problem", help="Problem id or slug")

    p_run = sub.add_parser("run", help="Run tests for a problem")
    p_run.add_argument("problem", help="Problem id or slug")

    p_import = sub.add_parser("import", help="Import a problem bundle directory")
    p_import.add_argument("path", help="Path to bundle directory")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    paths = get_paths()
    ensure_workspace(paths)

    conn = db.connect(paths.db_path)
    try:
        bootstrap(conn)
        if args.command == "list":
            return cmd_list(conn)
        if args.command == "open":
            return cmd_open(conn, args.problem)
        if args.command == "run":
            return cmd_run(conn, args.problem)
        if args.command == "import":
            return cmd_import(conn, args.path)
        parser.print_help()
        return 2
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
