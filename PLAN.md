# Implementation Plan: CLI-First Offline Practice Tool

## 1. Scope Lock
This plan implements the existing specification with the following fixed constraints:
- Python only.
- Local CLI-first workflow.
- `pytest` used for evaluation.
- SQLite for persistence.
- Source problems imported from `9021/` in this repository.
- Non-Python assets copied to a shared assets directory.
- Minimal initial CLI commands: `list`, `open`, `run`.

## 2. Deliverable Shape (MVP)
MVP is a local command-line app that:
1. Imports problems from `9021/` into a workspace snapshot.
2. Lists imported problems and latest status.
3. Opens a problem’s editable solution file.
4. Runs tests via `pytest` and stores attempt results in SQLite.
5. Resolves asset files using copied shared assets and relative path mapping.

## 3. Proposed Project Layout
```text
.
├── 9021/                           # input bundle (already exists)
├── app/
│   ├── __init__.py
│   ├── cli.py                      # argparse entrypoint
│   ├── config.py                   # workspace paths
│   ├── db.py                       # sqlite connection + migrations
│   ├── importer.py                 # bundle discovery + copy
│   ├── problem_index.py            # list/query helpers
│   ├── opener.py                   # open/edit workflow
│   ├── runner.py                   # pytest execution orchestration
│   ├── pytest_harness.py           # generated test harness helpers
│   └── models.py                   # typed records/dataclasses
├── tests/
│   ├── test_importer.py
│   ├── test_cli_list.py
│   ├── test_cli_open.py
│   ├── test_cli_run.py
│   ├── test_assets_resolution.py
│   └── fixtures/
├── .practice/
│   ├── practice.db                 # sqlite database
│   ├── bundles/
│   │   └── 9021_<hash>/            # snapshot of imported python files
│   ├── solutions/
│   │   └── <problem_slug>.py       # user-editable files
│   ├── assets/
│   │   └── 9021_<hash>/            # shared copied assets
│   └── runs/
│       └── <attempt_id>/           # ephemeral pytest run files
└── pyproject.toml
```

## 4. Data Model (SQLite)
Use a simple migration-on-start strategy (single `schema_version` table plus idempotent DDL).

### Tables
- `bundles`
  - `id INTEGER PK`
  - `name TEXT NOT NULL` (e.g. `9021`)
  - `source_root TEXT NOT NULL`
  - `snapshot_hash TEXT NOT NULL UNIQUE`
  - `imported_at TEXT NOT NULL`

- `problems`
  - `id INTEGER PK`
  - `bundle_id INTEGER NOT NULL`
  - `slug TEXT NOT NULL UNIQUE` (e.g. `sample_4`)
  - `source_relpath TEXT NOT NULL`
  - `prompt_path TEXT NOT NULL` (snapshot copy path)
  - `solution_path TEXT NOT NULL` (editable copy path)
  - `assets_manifest_json TEXT NOT NULL` (JSON list of relative asset paths)
  - `content_hash TEXT NOT NULL`
  - `FOREIGN KEY(bundle_id) REFERENCES bundles(id)`

- `attempts`
  - `id INTEGER PK`
  - `problem_id INTEGER NOT NULL`
  - `started_at TEXT NOT NULL`
  - `finished_at TEXT`
  - `duration_ms INTEGER`
  - `status TEXT NOT NULL` (`pass` | `fail` | `error`)
  - `passed_count INTEGER NOT NULL DEFAULT 0`
  - `failed_count INTEGER NOT NULL DEFAULT 0`
  - `stdout TEXT NOT NULL DEFAULT ''`
  - `stderr TEXT NOT NULL DEFAULT ''`
  - `exit_code INTEGER`
  - `solution_hash TEXT NOT NULL`
  - `FOREIGN KEY(problem_id) REFERENCES problems(id)`

## 5. CLI Contract (Minimal)

### `list`
- Purpose: show imported problems and latest result.
- Output columns:
  - `id`, `slug`, `source`, `attempts`, `last_status`, `last_run`.
- Behavior:
  - If DB not initialized, auto-bootstrap and import `9021/`.

### `open <problem>`
- Purpose: prepare and open solution file for editing.
- `problem` accepts numeric id or slug.
- Behavior:
  - Ensure solution file exists in `.practice/solutions/`.
  - Default action: print absolute path and first lines of prompt reference.
  - If `$EDITOR` exists, launch `$EDITOR <solution_path>` in foreground.

### `run <problem>`
- Purpose: run local evaluation and persist attempt.
- Behavior:
  - Creates attempt row (`started_at`).
  - Runs pytest harness for that specific problem in isolated run dir.
  - Updates attempt row with pass/fail/error, counts, outputs, duration.
  - Prints concise summary and failing snippets.

## 6. Import Strategy (`9021/`)

### Discovery Rules
- Include Python problems: `9021/sample_*.py`.
- Include shared assets: every non-`.py` file under `9021/`.
- Ignore hidden files and cache artifacts.

### Snapshot/Copy Rules
- Compute `snapshot_hash` from file paths + file hashes.
- Copy source problem files to `.practice/bundles/9021_<hash>/`.
- Copy non-Python assets to `.practice/assets/9021_<hash>/`.
- Keep relative structure intact.
- For each problem, precreate editable solution file from source snapshot.

## 7. Asset Resolution Design
- Run each problem from a temporary run directory under `.practice/runs/<attempt_id>/`.
- Symlink or copy:
  - solution file as test target module,
  - required shared assets preserving relative names.
- Set process working directory to run directory so plain `open("dictionary.txt")` works.
- Asset manifest for initial version:
  - default all shared assets in imported bundle are available to all problems.
  - later refinement: per-problem dependency detection.

## 8. `pytest` Evaluation Design

### Rationale
Source files currently embed doctests. We keep compatibility while standardizing on `pytest`.

### Approach
- For each run, generate a tiny harness file in run directory:
  - imports solution module.
  - defines test function using `doctest.DocTestSuite(module)`.
  - executes suite under pytest assertions.
- Invoke:
  - `pytest -q <generated_harness.py> --maxfail=20`.
- Parse pytest result:
  - exit code `0` => pass.
  - exit code `1` => fail.
  - others => error.
- Capture stdout/stderr for persistence.

## 9. Module-by-Module Build Plan

### Phase 1: Skeleton + Config
- Add `pyproject.toml` with runtime deps (none mandatory) and dev deps (`pytest`).
- Implement `app/config.py`:
  - workspace root `.practice/`,
  - standardized directories,
  - path helper utilities.

### Phase 2: SQLite Core
- Implement `app/db.py`:
  - connection factory,
  - migration bootstrap,
  - transactional helpers.
- Add minimal repository operations for bundles, problems, attempts.

### Phase 3: Importer
- Implement `app/importer.py`:
  - scan `9021/`,
  - snapshot hashing,
  - file copy logic,
  - DB upsert/update.

### Phase 4: CLI `list` and `open`
- Implement `app/problem_index.py` query helpers.
- Implement `app/opener.py` with `$EDITOR` fallback to path print.
- Wire `argparse` in `app/cli.py` for `list` and `open`.

### Phase 5: Runner + CLI `run`
- Implement `app/pytest_harness.py` generator.
- Implement `app/runner.py` subprocess execution and result parsing.
- Wire `run` command in CLI and attempt persistence.

### Phase 6: Test Coverage
- Unit tests for importer/hash/schema.
- CLI behavior tests via subprocess/pytest `capsys`.
- Asset resolution regression tests for:
  - `sample_4.py` using `dictionary.txt`.
  - `sample_7.py` using `word_search_1.txt` and `word_search_2.txt`.

## 10. Acceptance Checks for MVP
- `python -m app.cli list` shows all `sample_*.py` from `9021/`.
- `python -m app.cli open sample_4` yields editable solution path.
- `python -m app.cli run sample_4` executes via pytest and stores attempt.
- Attempt rows increase on repeated runs and statuses are queryable.
- Problems requiring assets run without manual path edits.
- Running with network disabled has no impact.

## 11. Risks and Mitigations
- Doctest-to-pytest bridge edge cases:
  - Mitigation: integration tests against all current sample files.
- Asset over-sharing in MVP:
  - Mitigation: allow all bundle assets first; add per-problem manifest later.
- User edits breaking import assumptions:
  - Mitigation: source snapshot immutable, editable copy isolated.

## 12. Immediate Next Execution Step
Implement Phases 1-3 first (skeleton, DB, importer), then land `list` as first working CLI vertical slice before `open` and `run`.
