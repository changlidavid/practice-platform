# Spec: Local-First LeetCode-Like TUI (Textual)

## 1. Objective
Build an offline-first terminal UI (TUI) using Textual on top of the existing CLI and SQLite-backed core in `app/`.

The TUI must provide a LeetCode-like interactive flow:
- Browse all problems
- Search/filter quickly
- Open/edit/run from keyboard
- Review per-problem run history
- Reflect DB updates immediately after runs

## 2. Scope

### In Scope (V1)
- New entrypoint: `python -m app.tui`
- Home table with problem metadata and verdicts
- Search by slug and filters (solved/unsolved, bundle)
- Key actions: `Enter`, `E`, `R`, `H`
- Live run feedback and post-run row refresh
- Reuse existing SQLite and runner logic (no network dependency)

### Out of Scope (V1)
- Rich in-terminal code editor (editing stays in `$EDITOR`)
- Multi-user profiles
- Remote sync/cloud features

## 3. Existing System Contract
- Existing CLI interface in [app/cli.py](/home/changli/Desktop/9021tasks/app/cli.py) remains unchanged.
- Existing DB schema in [app/db.py](/home/changli/Desktop/9021tasks/app/db.py) remains the source of truth.
- Existing run behavior in [app/runner.py](/home/changli/Desktop/9021tasks/app/runner.py) remains primary execution path.
- Solution files remain in `.practice/solutions/`.

## 4. User Experience Requirements

## 4.1 Start Command
- User can launch TUI with:
  - `python -m app.tui`

## 4.2 Home Screen
Home screen displays a selectable table with columns:
- `bundle`
- `slug`
- `attempts`
- `last_verdict` (normalized display: `PASS` / `FAIL` / `ERROR` / `NEVER`)
- `last_time_ms`
- `updated_at`

Interpretation rules:
- `last_verdict` derives from latest `attempts.status`.
- `last_time_ms` derives from latest `attempts.duration_ms` (blank or `-` if never run).
- `updated_at` derives from latest `attempts.finished_at` (blank or `-` if never run).

## 4.3 Search and Filters
- Type-to-search: matches `slug` with case-insensitive substring.
- Solved filter:
  - `all` (default)
  - `solved` (latest verdict `PASS`)
  - `unsolved` (latest verdict not `PASS`, including never attempted)
- Bundle filter:
  - `all` + dynamically discovered bundle names from DB

Filtering and search must combine (AND semantics).

## 4.4 Key Actions
- `Enter` on selected row:
  - Show problem detail pane/modal with:
    - problem slug and bundle
    - prompt path
    - solution path
    - prompt preview (first N lines)
- `E`:
  - Open selected solution in `$EDITOR`
  - If `$EDITOR` missing: show non-blocking message with solution path
- `R`:
  - Run selected problem doctests using internal runner call
  - Show run-in-progress indicator
  - Show final verdict and summary counts
  - Refresh selected row and table state without restarting app
- `H`:
  - Open history panel/modal showing attempts for selected problem:
    - attempt id, started_at, finished_at, status, duration_ms, passed_count, failed_count
    - optional short output excerpt

## 5. Architecture

## 5.1 New Modules
- `app/tui.py`
  - Textual `App` entrypoint and key bindings
- `app/tui_data.py`
  - DB query adapter for problem list, filters, and history
- `app/tui_actions.py`
  - Action handlers for open/run/detail/history
- `app/tui_widgets.py` (optional)
  - Shared widget composition if `tui.py` grows large

## 5.2 Reuse Strategy
- Reuse existing:
  - `db.connect()`, `db.init_db()`, `db.get_problem()`
  - `importer.ensure_imported()` bootstrap behavior
  - `runner.run_problem()` for execution/persistence
  - `opener.open_problem()` for editor fallback and preview behavior
- TUI should call Python modules directly (no shelling out to CLI commands).

## 5.3 Threading/Responsiveness
- Long-running `R` action must not freeze UI.
- Use Textual worker/thread pattern for run execution, then marshal results back to UI thread for refresh.

## 6. Data Query Requirements

## 6.1 Problem List Query
Implement a TUI-focused query (new helper or extension) returning:
- problem id, bundle, slug
- attempts count
- latest status
- latest duration_ms
- latest finished_at

Prefer a single SQL query with correlated subqueries or window functions for latest-attempt fields.

## 6.2 History Query
Per selected problem, return attempts ordered by newest first with:
- `id, started_at, finished_at, status, duration_ms, passed_count, failed_count, stdout, stderr`

## 7. Offline-First and Dependency Constraints
- Runtime must work fully offline once dependencies are installed.
- UI framework: `textual` only (plus existing stdlib and current project deps).
- Keep dependencies minimal:
  - add `textual` in project dependency config
  - avoid additional UI toolkits

## 8. Error Handling
- Missing DB/workspace: auto-bootstrap via existing initialization path.
- Missing bundle data: show clear message and allow retry.
- Missing `$EDITOR`: informational fallback only, no crash.
- Runner errors: surface concise error banner + optional detailed output panel.

## 9. Performance Targets
- Home screen initial load for <=1,000 problems: <=1s.
- Search/filter interaction update latency: <=150ms typical.
- Post-run table refresh latency: <=300ms after runner returns.

## 10. Security and Reliability
- Do not execute arbitrary shell commands for normal actions.
- Preserve existing local execution semantics and warnings.
- Ensure DB writes from run action remain consistent with current runner logic.

## 11. Acceptance Criteria
1. `python -m app.tui` launches a usable TUI home screen.
2. Home table correctly shows:
   - `bundle | slug | attempts | last verdict | last time ms | updated_at`.
3. Search by slug and solved/unsolved + bundle filters work as defined.
4. `Enter`, `E`, `R`, `H` actions function on selected problem.
5. After `R`, row verdict/attempts/time update in UI without restart.
6. Existing CLI commands (`list/open/run/import`) continue to work unchanged.

## 12. Delivery Milestones

### M1 TUI Skeleton
- Entry app, layout, keybindings, bootstrap wiring.

### M2 Data Integration
- Problem list query with required columns, search/filter controls.

### M3 Actions
- Detail/open/run/history behaviors with progress and notifications.

### M4 Polish
- Better formatting, empty/error states, keyboard hints, refresh ergonomics.
