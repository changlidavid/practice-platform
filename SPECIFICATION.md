# Spec: Local-First Offline Coding Practice Tool

## 1. Objective
Build a local-first, offline coding practice application (LeetCode-style) that imports problem bundles from folders (starting with `9021/`), lets users browse/open problems, write solutions, run tests locally, and track attempts/results over time.

## 2. Goals and Non-Goals

### Goals
- Work fully offline after installation.
- Import problems and bundled assets from a local folder.
- Provide a fast local workflow: browse -> open -> code -> run -> view results.
- Persist attempt history and outcome metrics locally.
- Reliably handle problems that depend on data files (`dictionary.txt`, `word_search_1.txt`, etc.).

### Non-Goals (V1)
- No cloud sync/account system.
- No online judge integration.
- No collaborative/multi-user editing.
- No plagiarism detection.

## 3. Primary Users
- Student practicing COMP9021-style programming questions locally.
- Instructor or TA preparing/testing local bundles.

## 4. User Stories
- As a user, I can import a folder (`9021/`) and see all valid problems discovered.
- As a user, I can browse/filter/sort problems by title, source file, status, tags.
- As a user, I can open a problem and edit my solution in an integrated editor.
- As a user, I can run tests locally and get pass/fail with useful diagnostics.
- As a user, I can retry multiple times and see attempt history over time.
- As a user, I can run problems requiring bundled data files without manual path hacks.

## 5. Functional Requirements

### FR-1 Bundle Import
- Input: local folder path.
- System scans recursively (default depth configurable) for supported problem definitions.
- Initial supported format:
  - Python source files (`*.py`) with doctest blocks and `if __name__ == "__main__": doctest.testmod()`.
- System creates immutable snapshot metadata for each imported file:
  - file hash (SHA-256), discovered title, function/class targets, required assets.
- Import operation reports:
  - imported count, skipped files, warnings, and parse errors.

### FR-2 Problem Discovery and Browsing
- Problem list shows:
  - title, source file, bundle name, last run status, attempts count, last attempted time.
- Filters:
  - never attempted, passing, failing, has assets, filename search.
- Sorting:
  - alphabetical, last attempted, pass rate, import order.

### FR-3 Open and Edit Problem
- Opening a problem creates/loads a user solution file in a managed workspace (never edits original imported source by default).
- UI shows read-only prompt/reference and editable solution area.
- User can reset solution to starter template.
- Auto-save locally at short interval and on explicit run.

### FR-4 Local Test Execution
- Run executes inside a controlled local runner with:
  - configured Python interpreter,
  - execution timeout,
  - memory/recursion safeguards (best effort in-process, strict via subprocess).
- For doctest-backed problems:
  - run doctests against the user solution module.
- Output includes:
  - pass/fail summary,
  - failed test details (expected vs actual),
  - runtime and timestamp.

### FR-5 Attempt and Result Tracking
- Every run stores an attempt record:
  - problem id, solution revision hash, timestamp, duration, status, counts, failure excerpts.
- Problem-level aggregates:
  - total attempts, pass count, latest pass date, best streak/current streak.
- History view supports:
  - chronological timeline and per-problem drill-down.

### FR-6 Data Asset Packaging and Resolution
- Importer detects non-Python assets in bundle and indexes them.
- At run time, runner sets working directory and asset map so relative file opens resolve reliably.
- Asset resolution order:
  1. per-problem working copy asset path,
  2. bundle asset path snapshot.
- Missing asset errors are explicit and include searched paths.
- If bundle changes on disk, tool can re-import and version new snapshot without corrupting prior attempts.

### FR-7 Offline-First Guarantees
- All core features operate without network access.
- No runtime dependency on remote APIs.
- Optional update checks (if later added) must be off by default.

## 6. Data Model (Local)

### Entities
- `bundles`
  - `id`, `name`, `root_path`, `imported_at`, `version_hash`
- `problems`
  - `id`, `bundle_id`, `source_relpath`, `title`, `type`, `asset_manifest`, `content_hash`
- `solutions`
  - `id`, `problem_id`, `workspace_path`, `last_saved_at`, `current_hash`
- `attempts`
  - `id`, `problem_id`, `solution_hash`, `started_at`, `finished_at`, `duration_ms`, `status`, `passed`, `failed`, `output_excerpt`
- `problem_stats` (materialized or computed)
  - `problem_id`, `attempts_total`, `passes_total`, `last_status`, `last_attempted_at`

### Storage
- Local SQLite DB for metadata/history.
- Local filesystem workspace for solution files and imported bundle snapshots.

## 7. Architecture (V1 Recommendation)
- Desktop-first local app:
  - Backend service: Python (runner/importer/storage).
  - Frontend: local web UI or desktop shell (e.g., Tauri/Electron) pointing to local backend.
- Runner model:
  - subprocess execution for isolation and stable cwd/environment setup.
- Bundle parser:
  - plugin interface for future non-doctest formats.

## 8. UX Requirements
- Core loop should require <=3 interactions from open problem to first run.
- Problem page includes:
  - statement/context, starter code, run button, result panel, attempt history.
- Consistent states:
  - idle, running, passed, failed, runner error (timeout/import/asset missing).
- Keyboard-first shortcuts:
  - run, save, next/previous problem, search.

## 9. Performance Requirements
- Problem list load (up to 1,000 problems): <=1.0s on reference machine.
- Open problem to editor ready: <=500ms median.
- Start local run after click: <=300ms overhead excluding test execution.
- Attempt history query for one problem (up to 5,000 attempts): <=200ms median.

## 10. Security and Reliability
- Runner executes only local code under user context, no elevated privileges.
- Clear warning that running untrusted bundles executes code locally.
- Crash-safe persistence:
  - attempt record should not be lost if app closes after run completion.
- Import validation prevents path traversal when copying/snapshotting assets.

## 11. Acceptance Criteria (V1)
- Importing `/home/changli/Desktop/9021tasks/9021` discovers all `sample_*.py` files and asset files.
- Opening `sample_4.py` and running tests resolves `dictionary.txt` without manual edits.
- Opening `sample_7.py` and running tests resolves `word_search_1.txt` and `word_search_2.txt`.
- Failed and passed runs are both persisted and visible in history.
- Relaunching app preserves bundles, solutions, and attempt stats.
- App functions with network disabled.

## 12. Milestones

### M1 Import + Read-Only Browser
- Bundle ingestion, problem catalog, metadata DB.

### M2 Editor + Doctest Runner
- Editable solution workspace, run button, result panel.

### M3 History + Stats
- Attempt persistence, dashboards, filters.

### M4 Asset Reliability + Hardening
- Asset manifesting, robust cwd/path mapping, error handling.

### M5 Polish
- Keyboard shortcuts, performance tuning, packaging docs.

## 13. Open Decisions
- Preferred UI packaging: browser UI + local server vs desktop shell.
- Strict sandbox level for runner (OS-dependent controls vs lightweight subprocess only).
- Multi-language support timeline beyond Python/doctest format.
