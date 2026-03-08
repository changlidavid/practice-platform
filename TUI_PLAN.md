# Plan: Textual TUI on Existing CLI/SQLite Core

## 1. Scope Lock
- UI framework: `Textual`.
- Keep existing SQLite schema unchanged (`bundles`, `problems`, `attempts`).
- Reuse existing modules for core behavior:
  - `app.importer` for bootstrap/imported data presence.
  - `app.runner` for doctest execution and attempt persistence.
  - `app.opener` for editor behavior/preview support.
- Preserve existing CLI commands (`list/open/run/import`) unchanged.

## 2. Launch Command
- Primary command:
  - `python -m app.tui`

## 3. File / Module Layout
```text
app/
├── tui.py             # Textual App entrypoint, layout, key bindings
├── tui_data.py        # DB query functions for grid rows + history + filters
├── tui_actions.py     # open/editor, run worker, detail/history orchestration
├── tui_format.py      # verdict/time formatting helpers
└── tui.css            # Textual styles for panels/table/status bar
```

Optional (if needed during implementation):
```text
app/
└── tui_widgets.py     # custom modal/panel widgets (history/detail)
```

## 4. Execution Flow

### 4.1 Startup
1. `app.tui` initializes workspace via `config.ensure_workspace()`.
2. Open DB with `db.connect()` and run `db.init_db()`.
3. Call `importer.ensure_imported()` so default `9021/` behavior remains.
4. Load table rows using `tui_data.fetch_problem_rows()`.

### 4.2 Home Screen
- DataTable columns:
  - `bundle | slug | attempts | last_verdict | last_time_ms | updated_at`
- Controls:
  - search input (slug substring)
  - solved filter (`all/solved/unsolved`)
  - bundle filter (`all + discovered bundles`)

### 4.3 Keybindings
- `Enter`: problem details modal (prompt preview + solution path)
- `E`: open selected solution in `$EDITOR`, fallback notification with path
- `R`: run selected problem via background worker, show progress, refresh row
- `H`: history modal for selected problem attempts
- `Q`: quit

## 5. Data Access Plan (No Schema Changes)

## 5.1 `tui_data.fetch_problem_rows()`
- Single query returning:
  - problem id
  - bundle name
  - slug
  - attempt count
  - latest status
  - latest duration_ms
  - latest finished_at
- Apply search/filter in SQL where practical, fallback in Python for simple V1.

## 5.2 `tui_data.fetch_attempt_history(problem_id)`
- Ordered newest-first from `attempts` with:
  - `id, started_at, finished_at, status, duration_ms, passed_count, failed_count`.

## 6. Action Plan

## 6.1 Open (`E` / `Enter`)
- Resolve selected problem using `db.get_problem()`.
- Reuse `opener.open_problem(solution_path, prompt_path)`.
- For `Enter`, show preview text in modal instead of launching editor.

## 6.2 Run (`R`)
- Use Textual worker/thread to call:
  - `runner.run_problem(conn, paths, problem_row)`.
- On completion:
  - show status notification (`PASS/FAIL/ERROR`, counts, time),
  - requery row data and update DataTable in place.

## 6.3 History (`H`)
- Modal/table with attempt rows and compact status badges.

## 7. Implementation Phases

### Phase A: Skeleton + Launch
- Add `app/tui.py` with minimal `App`, key map, static table shell.
- Add dependency `textual` to `pyproject.toml`.
- Validate `python -m app.tui` launches.

### Phase B: Data Wiring
- Implement `tui_data.py`.
- Populate table from DB and add search/filter controls.

### Phase C: Actions
- Implement `Enter`, `E`, `R`, `H`.
- Add background run workflow and row refresh.

### Phase D: Polish
- Add `tui.css`, improve readability/status colors.
- Handle empty/error states and missing `$EDITOR` messaging.

## 8. Acceptance Checklist
- [ ] `python -m app.tui` launches TUI successfully.
- [ ] Home table shows required columns with correct DB values.
- [ ] Search and filters update visible rows correctly.
- [ ] `Enter`, `E`, `R`, `H` work on selected problem.
- [ ] After `R`, row status/attempt/time update without restarting.
- [ ] Existing CLI behavior remains unchanged.
