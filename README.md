# Practice CLI + Web UI

Offline Python practice platform with:
- CLI workflows (`list`, `open`, `run`, `import`)
- FastAPI web UI
- doctest-based grading runner
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
| `PRACTICE_BUNDLE_PATHS` | No | unset | Comma-separated bundle paths, e.g. `9021,final` (takes precedence over single path). |
| `OTP_DEV_MODE` | No | `false` | If true, allows dev OTP fallback when SMTP is missing. |
| `COOKIE_SECURE` | No | `false` dev / `true` prod-like | Secure session cookies (enable under HTTPS). |
| `SMTP_HOST` | Yes for real email OTP | unset | SMTP host (example: Gmail SMTP). |
| `SMTP_PORT` | No | `587` | SMTP port. |
| `SMTP_USERNAME` | Usually yes | unset | SMTP login username. |
| `SMTP_PASSWORD` | Usually yes | unset | SMTP login password/app password. |
| `SMTP_FROM` | Yes for real email OTP | unset | From address used for OTP email. |
| `SMTP_USE_TLS` | No | `true` | Use STARTTLS for SMTP connection. |
| `PRACTICE_DOCTEST_TIMEOUT_SECONDS` | No | `5` | Max doctest runtime per attempt. |
| `PRACTICE_DOCTEST_OUTPUT_MAX_BYTES` | No | `262144` | Max captured bytes per stream (`stdout`/`stderr`). |

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
