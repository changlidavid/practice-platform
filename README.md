# Practice CLI + Web UI

Offline Python practice platform with:
- CLI workflows (`list`, `open`, `run`, `import`)
- FastAPI web UI
- dual-mode grading runner (legacy doctest + hidden JSON function evaluator)
- SQLite persistence
- startup bundle importer (single or multi-bundle)
- optional OTP email authentication

It is designed for local-first practice and reproducible deployment (native Python or Docker).

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/changlidavid/practice-platform.git
cd practice-platform

python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

### 2. Configure environment

```bash
cp -n .env.example .env
```

For local development without real SMTP, you can set:

```bash
OTP_DEV_MODE=true
COOKIE_SECURE=false
```

### 3. Run web app

```bash
python -m app.web
```

Open `http://127.0.0.1:8000`.

### 4. Run CLI

```bash
python -m app.cli list
python -m app.cli open sample_1
python -m app.cli run sample_1
```

## Docker Deployment

### Docker Quick Start (Recommended)

```bash
cp -n .env.example .env
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Open `http://127.0.0.1:8000`.

Useful commands:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

Overrides in [`docker-compose.prod.yml`](/home/changli/Desktop/9021tasks/docker-compose.prod.yml):
- named volume `practice_data` for `/data`
- `COOKIE_SECURE=true` by default
- healthcheck for `/login`

### Optional: Development Compose (Bind Mount)

Use this only if you specifically want host-visible runtime data and your local filesystem permissions are configured for bind mounts:

```bash
docker compose up -d --build
```

Defaults in [`docker-compose.yml`](/home/changli/Desktop/9021tasks/docker-compose.yml):
- bind mount `./.practice:/data`
- `COOKIE_SECURE=false`
- suitable for local HTTP testing when permissions are compatible

### Known Issue (Dev Bind Mount)

On some machines/filesystems, bind-mounted `./.practice:/data` can fail on fresh clones due to local ownership/permission behavior.  
If that happens, use the recommended prod-like compose flow above (named volume `practice_data`) instead of bind mount mode.

### Migrating local data to `practice_data` volume

```bash
docker run --rm \
  -v "$(pwd)/.practice:/from:ro" \
  -v practice_data:/to \
  alpine sh -c "cp -a /from/. /to/"
```

## Environment Variables

Configured in `.env` (see `.env.example`).

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `PRACTICE_HOME` | No | `/data` in Docker, `.practice` locally | Workspace root (DB, runs, solutions, assets). |
| `PRACTICE_BUNDLE_PATH` | No | `9021` | Legacy single startup bundle path. |
| `PRACTICE_BUNDLE_PATHS` | No | unset | Comma-separated bundle paths, e.g. `9021,problems` (takes precedence over single path). |
| `OTP_DEV_MODE` | No | `false` | If true, allows dev OTP fallback when SMTP is missing. |
| `COOKIE_SECURE` | No | `false` dev / `true` prod-like | Secure session cookies (enable under HTTPS). |
| `SMTP_HOST` | Yes for real email OTP | unset | SMTP host (example: Gmail SMTP). |
| `SMTP_PORT` | No | `587` | SMTP port. |
| `SMTP_USERNAME` | Usually yes | unset | SMTP login username. |
| `SMTP_PASSWORD` | Usually yes | unset | SMTP login password/app password. |
| `SMTP_FROM` | Yes for real email OTP | unset | From address used for OTP email. |
| `SMTP_USE_TLS` | No | `true` | Use STARTTLS for SMTP connection. |
| `PRACTICE_DOCTEST_TIMEOUT_SECONDS` | No | `5` | Max runtime per attempt (used for doctest and hidden-test evaluator subprocesses). |
| `PRACTICE_DOCTEST_OUTPUT_MAX_BYTES` | No | `262144` | Max captured bytes per stream (`stdout`/`stderr`). |

## New Function-JSON Problem Format

In addition to legacy doctest `.py` problems, you can add function-only problems in directory form:

```text
problems/<problem_name>/
  meta.json
  statement.md
  starter.py
  public_examples.json
  hidden_tests.json
```

- `statement.md` and `public_examples.json` are visible in UI.
- `hidden_tests.json` is loaded server-side by the runner and never returned by API.
- `meta.json` requires at least: `entry_function` (and usually `slug`, `title`).

## Migration Template

Keep dual-mode support during migration:
- Legacy doctest `.py` problems stay in place and continue to run.
- Migrated problems are added as new directory-based `function_json` problems.

Recommended mapping from old doctest problem to new files:
- `meta.json`: set `slug` to the target problem slug, `title` to a readable title, and `entry_function` to the original function name.
- `statement.md`: reuse any non-doctest prose from the original function docstring; if the source has no prose, add a short plain-language prompt plus the function signature.
- `starter.py`: keep the original function signature, but replace the implementation with a minimal stub.
- `public_examples.json`: keep a small display-only subset of examples, usually the first 2-3 representative doctests.
- `hidden_tests.json`: include the full official evaluation set. During early migration, it is reasonable to copy all original doctest examples here, including the public ones, and then add extra hidden edge cases manually.

Automatic conversion is safest for return-value problems whose doctests look like direct literal calls such as `f([1, 2])` with literal outputs such as `[2, 1]`.
Problems that grade printed output should stay on legacy doctest for now or be migrated manually after redesigning them as return-value functions.

Helper script:

```bash
python3 scripts/migrate_doctest_problem.py 9021/sample_1.py --output-root problems --public-count 3
```

The script:
- extracts the first top-level function and its doctest examples
- writes `meta.json`, `statement.md`, `starter.py`, `public_examples.json`, and `hidden_tests.json`
- uses all original doctest examples as the initial hidden test set
- leaves final review to you, especially for better statement wording and extra hidden edge cases

Security note:
- Never commit real credentials in `.env`.
- Use `.env.example` as the shared template.

## Screenshots

Add screenshots under `docs/screenshots/` and reference them here.

Example placeholders:
- `docs/screenshots/login.png`
- `docs/screenshots/web-home.png`
- `docs/screenshots/run-result.png`

## Architecture

See [`docs/architecture.md`](/home/changli/Desktop/9021tasks/docs/architecture.md) for component and data flow details.

## Suggested Repository Structure

See [`docs/repository-structure.md`](/home/changli/Desktop/9021tasks/docs/repository-structure.md) for a clean open-source layout proposal.

## Development and Testing

```bash
pytest -q
```

## License

This repository uses the MIT License (see [`LICENSE`](/home/changli/Desktop/9021tasks/LICENSE)).
