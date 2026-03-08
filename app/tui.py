from __future__ import annotations

import os
import sqlite3
import subprocess
from pathlib import Path

try:
    from textual import work
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal
    from textual.widgets import DataTable, Footer, Header, Input, Select, Static
except ModuleNotFoundError as exc:  # pragma: no cover - environment guard
    if exc.name == "textual":
        raise SystemExit(
            "Textual is not installed. Install dependencies (e.g., `pip install -e .`) and retry."
        )
    raise

from . import db, importer, tui_actions, tui_data
from .config import Paths, ensure_workspace, get_paths
from .tui_format import format_duration, format_timestamp, verdict_label


class PracticeTUI(App[None]):
    CSS_PATH = "tui.css"
    BINDINGS = [
        ("enter", "show_detail", "Detail"),
        ("e", "open_editor", "Edit"),
        ("r", "run_problem", "Run"),
        ("h", "show_history", "History"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.paths: Paths = get_paths()
        self.conn: sqlite3.Connection | None = None
        self.rows: list[tui_data.ProblemRow] = []
        self.search_term = ""
        self.solved_filter = "all"
        self.bundle_filter = "all"
        self.log_buffer = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="filters"):
            yield Input(placeholder="Search slug...", id="search")
            yield Select(
                options=[("All", "all"), ("Solved", "solved"), ("Unsolved", "unsolved")],
                value="all",
                id="solved_filter",
                prompt="Solved",
            )
            yield Select(options=[("All Bundles", "all")], value="all", id="bundle_filter", prompt="Bundle")
        yield DataTable(id="problems")
        yield Static("Ready", id="status")
        yield Static("", id="detail")
        yield Static("", id="logs")
        yield Footer()

    def on_mount(self) -> None:
        ensure_workspace(self.paths)
        self.conn = db.connect(self.paths.db_path)
        db.init_db(self.conn)
        importer.ensure_imported(self.conn, self.paths)

        table = self.query_one("#problems", DataTable)
        table.cursor_type = "row"
        table.add_columns("bundle", "slug", "attempts", "last verdict", "last time ms", "updated_at")

        self._refresh_bundle_filter()
        self.refresh_table()

    def on_unmount(self) -> None:
        if self.conn is not None:
            self.conn.close()

    def _refresh_bundle_filter(self) -> None:
        if self.conn is None:
            return
        names = tui_data.fetch_bundle_names(self.conn)
        options = [("All Bundles", "all")] + [(name, name) for name in names]
        select = self.query_one("#bundle_filter", Select)
        select.set_options(options)
        select.value = "all"

    def refresh_table(self) -> None:
        if self.conn is None:
            return
        self.rows = tui_data.fetch_problem_rows(
            self.conn,
            search=self.search_term,
            solved_filter=self.solved_filter,
            bundle_filter=self.bundle_filter,
        )
        table = self.query_one("#problems", DataTable)
        table.clear(columns=False)
        for row in self.rows:
            table.add_row(
                row.bundle_name,
                row.slug,
                str(row.attempts),
                verdict_label(row.last_status),
                format_duration(row.last_time_ms),
                format_timestamp(row.updated_at),
            )
        self.query_one("#status", Static).update(f"Loaded {len(self.rows)} problems")

    def _selected_problem(self) -> tui_data.ProblemRow | None:
        table = self.query_one("#problems", DataTable)
        if not self.rows:
            return None
        idx = table.cursor_row
        if idx < 0 or idx >= len(self.rows):
            return None
        return self.rows[idx]

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search":
            return
        self.search_term = event.value
        self.refresh_table()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "solved_filter":
            self.solved_filter = str(event.value)
        elif event.select.id == "bundle_filter":
            self.bundle_filter = str(event.value)
        else:
            return
        self.refresh_table()

    def action_show_detail(self) -> None:
        selected = self._selected_problem()
        if selected is None or self.conn is None:
            self.notify("No problem selected", severity="warning")
            return
        row = tui_actions.problem_by_id(self.conn, selected.problem_id)
        preview, solution_path, prompt_path = tui_actions.prepare_problem_view(row)
        content = (
            f"Bundle:   {selected.bundle_name}\n"
            f"Slug:     {selected.slug}\n"
            f"Prompt:   {prompt_path}\n"
            f"Solution: {solution_path}\n\n"
            "Preview:\n"
            f"{preview}"
        )
        self.query_one("#detail", Static).update(content)

    def action_open_editor(self) -> None:
        selected = self._selected_problem()
        if selected is None or self.conn is None:
            self.notify("No problem selected", severity="warning")
            return
        row = tui_actions.problem_by_id(self.conn, selected.problem_id)
        _preview, solution_path, _prompt_path = tui_actions.prepare_problem_view(row)

        editor = os.environ.get("EDITOR")
        if not editor:
            self.notify(
                f"$EDITOR is not set. Solution: {solution_path}. Set it with `export EDITOR=nvim`.",
                severity="warning",
            )
            return

        try:
            with self.app.suspend():
                opened = tui_actions.launch_editor_for_solution(solution_path)
        except FileNotFoundError as exc:
            editor_bin = Path(exc.filename).name if exc.filename else editor.split()[0]
            self.notify(f"Editor not found: {editor_bin}", severity="error")
            return
        except subprocess.CalledProcessError as exc:
            self.notify(
                f"Editor exited with status {exc.returncode}. Solution: {solution_path}",
                severity="warning",
            )
            return
        except ValueError as exc:
            self.notify(f"Invalid $EDITOR value: {exc}", severity="error")
            return
        if opened:
            self.notify(f"Opened in editor: {solution_path}")
        else:
            self.notify(
                f"Could not launch $EDITOR. Solution: {solution_path}. "
                "Set EDITOR, e.g. `export EDITOR=nvim`.",
                severity="warning",
            )

    @work(thread=True, exclusive=True)
    def _run_selected_worker(self, problem_id: int) -> None:
        def on_log(_stream: str, line: str) -> None:
            self.call_from_thread(self._append_log, line)

        try:
            attempt_id, result = tui_actions.run_problem_by_id(
                paths=self.paths,
                problem_id=problem_id,
                log_callback=on_log,
            )
            self.call_from_thread(self._on_run_completed, problem_id, attempt_id, result)
        except Exception as exc:  # pragma: no cover - UI-level guard
            self.call_from_thread(self._on_run_failed, str(exc))

    def _append_log(self, line: str) -> None:
        self.log_buffer += line
        if len(self.log_buffer) > 20000:
            self.log_buffer = self.log_buffer[-20000:]
        logs = self.query_one("#logs", Static)
        logs.update(self.log_buffer)

    def _on_run_completed(self, problem_id: int, attempt_id: int, result: object) -> None:
        self.refresh_table()
        self.query_one("#status", Static).update(
            f"Run complete for problem {problem_id} (attempt {attempt_id}): "
            f"{getattr(result, 'status', 'error').upper()} "
            f"passed={getattr(result, 'passed', 0)} failed={getattr(result, 'failed', 0)} "
            f"time={getattr(result, 'duration_ms', 0)}ms"
        )

    def _on_run_failed(self, message: str) -> None:
        self.query_one("#status", Static).update(f"Run failed: {message}")
        self.notify(message, severity="error")

    def action_run_problem(self) -> None:
        selected = self._selected_problem()
        if selected is None:
            self.notify("No problem selected", severity="warning")
            return
        self.log_buffer = "[running...]\n"
        self.query_one("#logs", Static).update(self.log_buffer)
        self.query_one("#status", Static).update(f"Running {selected.slug}...")
        self._run_selected_worker(selected.problem_id)

    def action_show_history(self) -> None:
        selected = self._selected_problem()
        if selected is None or self.conn is None:
            self.notify("No problem selected", severity="warning")
            return
        rows = tui_data.fetch_attempt_history(self.conn, selected.problem_id, limit=20)
        if not rows:
            self.query_one("#detail", Static).update("No attempt history for selected problem.")
            return

        lines = ["Recent attempts (newest first):", "id status duration_ms passed failed finished_at"]
        for row in rows:
            finished = row.finished_at or "-"
            duration = "-" if row.duration_ms is None else str(row.duration_ms)
            lines.append(
                f"{row.attempt_id} {row.status.upper():<5} {duration:<11} "
                f"{row.passed_count:<6} {row.failed_count:<6} {finished}"
            )
        self.query_one("#detail", Static).update("\n".join(lines))


def main() -> None:
    app = PracticeTUI()
    app.run()


if __name__ == "__main__":
    main()
