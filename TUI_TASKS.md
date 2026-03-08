# Tasks: Textual TUI (LeetCode-like)

## T0 Foundation and Dependency
- [ ] Add `textual` dependency to `pyproject.toml`.
- [ ] Create new modules:
  - [ ] `app/tui.py`
  - [ ] `app/tui_data.py`
  - [ ] `app/tui_actions.py`
  - [ ] `app/tui_format.py`
  - [ ] `app/tui.css`
- [ ] Keep existing CLI commands unchanged.

Acceptance:
- `python -m app.tui` launches a minimal Textual app.

## T1 TUI Skeleton
- [ ] Build app shell layout:
  - [ ] header/title
  - [ ] filter/search bar
  - [ ] main DataTable area
  - [ ] status/footer hints
- [ ] Wire startup bootstrap:
  - [ ] `ensure_workspace()`
  - [ ] `db.connect()` + `db.init_db()`
  - [ ] `importer.ensure_imported()`
- [ ] Add keybindings:
  - [ ] `Enter` detail
  - [ ] `E` editor
  - [ ] `R` run
  - [ ] `H` history
  - [ ] `Q` quit

Acceptance:
- App starts with visible layout and keybinding hints.

## T2 List Table + Filters
- [ ] Implement `tui_data.fetch_problem_rows()` query returning:
  - [ ] bundle
  - [ ] slug
  - [ ] attempts
  - [ ] last verdict
  - [ ] last time ms
  - [ ] updated_at
- [ ] Populate DataTable with required columns.
- [ ] Implement slug search (type-to-search).
- [ ] Implement solved filter:
  - [ ] `all`
  - [ ] `solved` (latest pass)
  - [ ] `unsolved` (latest not pass or never)
- [ ] Implement bundle filter (`all + bundle names`).
- [ ] Refresh table on filter/search changes without restart.

Acceptance:
- Table rows/columns reflect DB correctly and filters/search work together.

## T3 Run Integration + Live Logs
- [ ] Add action handler for `R` on selected row.
- [ ] Use background worker (non-blocking UI) to call `runner.run_problem(...)`.
- [ ] While running:
  - [ ] show progress state/spinner
  - [ ] stream or append stdout/stderr into a live log panel/modal
- [ ] On completion:
  - [ ] show verdict summary (`PASS/FAIL/ERROR`)
  - [ ] show counts + duration
  - [ ] refresh selected row and table values from DB
- [ ] Handle runner exceptions gracefully in UI.

Acceptance:
- Running a problem shows live feedback and updates row status without app restart.

## T4 Open/Editor Integration
- [ ] Implement `E` action:
  - [ ] resolve selected problem
  - [ ] open solution via existing opener/editor behavior
  - [ ] fallback notice when `$EDITOR` missing
- [ ] Implement `Enter` detail action:
  - [ ] prompt path
  - [ ] solution path
  - [ ] prompt preview snippet

Acceptance:
- `E` opens editor or shows fallback path; `Enter` displays detail pane.

## T5 History Panel
- [ ] Implement `tui_data.fetch_attempt_history(problem_id)`.
- [ ] Implement `H` action with history panel/modal.
- [ ] Show rows:
  - [ ] attempt id
  - [ ] status
  - [ ] started_at / finished_at
  - [ ] duration_ms
  - [ ] passed_count / failed_count
- [ ] Optional: expandable output excerpt for selected attempt.

Acceptance:
- `H` shows persisted attempt history for selected problem.

## T6 UX and Formatting Polish
- [ ] Add `app/tui.css` styling for readability.
- [ ] Color/status formatting:
  - [ ] PASS (green-ish)
  - [ ] FAIL (red-ish)
  - [ ] ERROR (yellow/orange)
  - [ ] NEVER (dim/neutral)
- [ ] Ensure keyboard navigation is smooth.
- [ ] Add empty-state and error-state views/messages.

Acceptance:
- TUI remains usable and clear across normal, empty, and error scenarios.

## T7 Tests
- [ ] Add tests for data queries and filter logic (unit tests).
- [ ] Add app-level smoke test for launch/imported rows.
- [ ] Add run-action test:
  - [ ] run completes
  - [ ] DB updated
  - [ ] row refresh path triggered
- [ ] Add history panel data retrieval test.

Acceptance:
- New tests pass locally with `pytest`.

## Recommended Execution Order
1. T0 -> T1
2. T2
3. T4
4. T3
5. T5
6. T6 -> T7

## Definition of Done
- [ ] Launch via `python -m app.tui`.
- [ ] Home table columns match spec.
- [ ] Search + solved/unsolved + bundle filters work.
- [ ] `R` run action shows live logs and refreshes status.
- [ ] `E` and `Enter` support editor/detail flows.
- [ ] `H` displays attempt history.
- [ ] Existing CLI remains functional.
