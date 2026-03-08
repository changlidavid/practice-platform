# Architecture

## Overview

The system is an offline-first Python practice platform composed of:
- a FastAPI web server
- a SQLite database
- a bundle importer
- a doctest execution runner
- Docker packaging for reproducible deployment

All runtime state is stored under `PRACTICE_HOME` (for example `/data` in Docker, `.practice/` locally).

## Components

### 1. FastAPI Web Server (`app/web.py`)

Responsibilities:
- startup bootstrap (workspace creation, DB initialization, bundle import)
- session-based auth (email/password and OTP login)
- HTML rendering (`/login`, `/`)
- JSON API endpoints for problems, solutions, and runs
- static asset serving (`/static`)

At startup, the app:
1. Loads `.env`
2. Ensures workspace directories
3. Initializes SQLite schema
4. Imports problems from configured bundle path(s)

### 2. SQLite Database (`app/db.py`)

SQLite is the single persistent store for:
- problem metadata and doctests
- imported bundle snapshots and bundle assets
- run attempts and run outputs
- users, OTP records, sessions
- per-user solutions and per-problem stats

Schema migrations are handled in code by:
- `CREATE TABLE IF NOT EXISTS ...`
- compatibility checks via `PRAGMA table_info(...)`
- additive `ALTER TABLE` for legacy DB compatibility

### 3. Problem Importer (`app/importer.py`)

Importer behavior:
- recursively discovers `.py` problem files plus non-Python assets from bundle directories
- computes snapshot hash of all files for deduplication
- extracts module doctests and descriptions
- upserts problems and bundle assets into DB

Bundle selection:
- `PRACTICE_BUNDLE_PATHS` (comma-separated) if provided
- otherwise legacy single path `PRACTICE_BUNDLE_PATH`

Default local bundle is `9021/`.

### 4. Doctest Runner (`app/runner.py`)

Runner behavior:
- builds a temporary attempt workspace under `runs/`
- composes executable module with immutable doctest text from DB
- executes Python doctest in a subprocess
- enforces timeout and output-size caps
- parses pass/fail counts
- stores attempt result and updates user/problem stats

The same runner is reused by both:
- CLI (`python -m app.cli run ...`)
- Web API (`POST /api/run/{problem_id}`)

### 5. Docker Deployment

Container build (`Dockerfile`):
- base image: `python:3.12-slim`
- copies app source plus default bundles
- installs package via `pip install .`
- runs as non-root user
- default command: `python -m app.web`

Compose modes:
- `docker-compose.yml`: development-oriented, bind-mounts `./.practice` to `/data`
- `docker-compose.prod.yml`: production-like override with named volume and healthcheck

## Data Flow

### Import flow
1. App bootstraps.
2. Importer scans configured bundle path(s).
3. Problems and assets are upserted into SQLite.
4. Problem list becomes available to CLI and web UI.

### Run flow
1. User submits code from CLI or web UI.
2. Runner materializes attempt workspace and assets.
3. Runner executes doctest subprocess with caps.
4. Result is stored in DB and returned to caller.

### Auth flow (web)
1. User requests register/login OTP or password login.
2. OTP/session rows are created and validated in SQLite.
3. Session cookie is issued (`COOKIE_SECURE` controls secure flag).
4. Authenticated API calls use session token lookup.

## Deployment Notes

- For HTTPS deployments, set `COOKIE_SECURE=true`.
- For real OTP email delivery, configure SMTP environment variables.
- Keep `.env` private; commit only `.env.example`.
