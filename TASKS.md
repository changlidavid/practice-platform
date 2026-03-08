# Tasks: CLI-First Offline Practice Tool

## T0 Project Bootstrap
- [ ] Create `pyproject.toml` for Python project metadata.
- [ ] Add runtime entrypoint (`python -m app.cli`).
- [ ] Add dev dependency: `pytest`.
- [ ] Create package skeleton:
  - [ ] `app/__init__.py`
  - [ ] `app/cli.py`
  - [ ] `app/config.py`
  - [ ] `app/db.py`
  - [ ] `app/importer.py`
  - [ ] `app/problem_index.py`
  - [ ] `app/opener.py`
  - [ ] `app/runner.py`
  - [ ] `app/pytest_harness.py`
  - [ ] `app/models.py`

Acceptance:
- `python -m app.cli --help` runs successfully.

## T1 Workspace and Config
- [ ] Implement workspace root `.practice/`.
- [ ] Implement path helpers for:
  - [ ] DB path `.practice/practice.db`
  - [ ] bundles dir `.practice/bundles/`
  - [ ] solutions dir `.practice/solutions/`
  - [ ] shared assets dir `.practice/assets/`
  - [ ] run temp dir `.practice/runs/`
- [ ] Ensure directories are auto-created.

Acceptance:
- First CLI invocation creates all required workspace directories.

## T2 SQLite Schema and DB Layer
- [ ] Implement SQLite connection factory.
- [ ] Add migration bootstrap (`schema_version` table + idempotent DDL).
- [ ] Create tables:
  - [ ] `bundles`
  - [ ] `problems`
  - [ ] `attempts`
- [ ] Implement repository functions:
  - [ ] insert/get bundle by hash
  - [ ] upsert problem
  - [ ] get problem by id/slug
  - [ ] list problems with latest status and attempt count
  - [ ] create/update attempt

Acceptance:
- Running DB init twice is safe and leaves schema consistent.

## T3 Importer for `9021/`
- [ ] Scan `9021/` for `sample_*.py`.
- [ ] Scan `9021/` for non-`.py` assets.
- [ ] Compute bundle snapshot hash from file paths + file hashes.
- [ ] Copy problem `.py` files to `.practice/bundles/9021_<hash>/`.
- [ ] Copy assets to `.practice/assets/9021_<hash>/` preserving relative paths.
- [ ] Create solution files in `.practice/solutions/` if missing.
- [ ] Persist bundle/problem rows with asset manifest JSON.
- [ ] Add re-import behavior:
  - [ ] no-op if same hash already imported
  - [ ] insert new bundle version if hash changes

Acceptance:
- Import discovers all `9021/sample_*.py`.
- Assets include `dictionary.txt`, `word_search_1.txt`, `word_search_2.txt`.

## T4 CLI Command: `list`
- [ ] Add `list` subcommand in `argparse`.
- [ ] Auto-bootstrap DB + import `9021/` if needed.
- [ ] Print table with:
  - [ ] `id`
  - [ ] `slug`
  - [ ] `source_relpath`
  - [ ] `attempts`
  - [ ] `last_status`
  - [ ] `last_run`
- [ ] Handle empty/problem-free state cleanly.

Acceptance:
- `python -m app.cli list` prints all imported samples and status columns.

## T5 CLI Command: `open`
- [ ] Add `open <problem>` subcommand (id or slug).
- [ ] Resolve target problem from DB.
- [ ] Ensure solution file exists.
- [ ] If `$EDITOR` is set, launch editor with solution file.
- [ ] Otherwise print absolute solution path + brief prompt header preview.

Acceptance:
- `python -m app.cli open sample_4` resolves and opens/prints solution path.

## T6 Pytest Harness and Runner
- [ ] Create generated harness file for a single problem run.
- [ ] Harness imports solution module and executes doctest suite under pytest.
- [ ] Build isolated run dir `.practice/runs/<attempt_id>/`.
- [ ] Stage solution and expose shared assets with relative names.
- [ ] Run `pytest -q <harness> --maxfail=20` in subprocess.
- [ ] Capture stdout, stderr, exit code, duration.
- [ ] Map result:
  - [ ] `pass` for exit code `0`
  - [ ] `fail` for exit code `1`
  - [ ] `error` otherwise

Acceptance:
- Running on a known incomplete sample returns fail with captured details.

## T7 CLI Command: `run`
- [ ] Add `run <problem>` subcommand.
- [ ] Resolve problem and create attempt row (`started_at`).
- [ ] Execute runner and update attempt row (`finished_at`, status, counts).
- [ ] Print concise result summary and failure excerpts.

Acceptance:
- `python -m app.cli run sample_4` creates attempt record and prints result.

## T8 Attempt History and Aggregation
- [ ] Implement query to compute attempts + last status per problem (for `list`).
- [ ] Ensure repeated runs increment counts.
- [ ] Persist solution hash per attempt.

Acceptance:
- Re-running a problem changes attempt count and last run timestamp in `list`.

## T9 Asset Resolution Regression Checks
- [ ] Add runner test for `sample_4.py` requiring `dictionary.txt`.
- [ ] Add runner test for `sample_7.py` requiring `word_search_1.txt` and `word_search_2.txt`.
- [ ] Verify relative-path `open(...)` succeeds without source edits.

Acceptance:
- Both problems execute without `FileNotFoundError` caused by missing assets.

## T10 Test Suite
- [ ] `tests/test_importer.py` for discovery, hashing, copy, DB persistence.
- [ ] `tests/test_cli_list.py` for bootstrap + listing output.
- [ ] `tests/test_cli_open.py` for id/slug resolution and path behavior.
- [ ] `tests/test_cli_run.py` for attempt lifecycle and result status mapping.
- [ ] `tests/test_assets_resolution.py` for data-file-backed problems.

Acceptance:
- `pytest` passes locally for all new tests.

## T11 Error Handling and UX Polish (CLI)
- [ ] Friendly errors for unknown problem id/slug.
- [ ] Friendly errors for missing `9021/` source folder.
- [ ] Clear messaging when pytest is unavailable.
- [ ] Return non-zero exit codes on command failures.

Acceptance:
- Expected failure scenarios produce actionable messages and proper exit codes.

## T12 Documentation
- [ ] Add `README.md` usage quickstart:
  - [ ] install
  - [ ] `list`
  - [ ] `open`
  - [ ] `run`
  - [ ] workspace location explanation
- [ ] Document safety note for running local code.
- [ ] Document asset-copy and relative-path behavior.

Acceptance:
- New user can run end-to-end flow from README only.

## Execution Order (Recommended)
1. T0 -> T1 -> T2 -> T3 -> T4
2. T5
3. T6 -> T7 -> T8
4. T9 -> T10
5. T11 -> T12

## Definition of Done (MVP)
- [ ] `list/open/run` all functional from CLI.
- [ ] SQLite persistence works across restarts.
- [ ] `pytest`-based evaluation works for doctest-backed problems.
- [ ] Shared assets are copied and resolved via relative paths.
- [ ] Tests pass locally.
