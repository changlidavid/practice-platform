# Practice CLI + Web UI

Local offline practice runner for doctest-based Python problems.

## Local CLI Quickstart

```bash
python -m app.cli list
python -m app.cli open sample_1
python -m app.cli run sample_1
```

## Docker Quickstart (Development)

1. Create runtime env file:

```bash
cp -n .env.example .env
```

2. Start:

```bash
docker compose up -d --build
```

3. Open:

- http://127.0.0.1:8000

4. Logs:

```bash
docker compose logs -f web
```

5. Stop:

```bash
docker compose down
```

Development defaults:
- `docker-compose.yml` bind-mounts `./.practice:/data` (host data visible inside container).
- `COOKIE_SECURE=false` is suitable for local HTTP.
- `OTP_DEV_MODE` can be true for log-only OTP fallback when SMTP is missing.

## Docker Prod-Like Compose (Minimal Override)

Use layered compose files:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Stop:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

Prod-like overrides in `docker-compose.prod.yml`:
- switch `/data` to named volume `practice_data`
- `COOKIE_SECURE=true` by default
- `OTP_DEV_MODE=false` by default
- add service healthcheck (uses Python stdlib, no `curl`/`wget` dependency)

Health status:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

## Environment Variables (`.env`)

Required for real email OTP:
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `SMTP_USE_TLS`

Important flags:
- `OTP_DEV_MODE`
  - `true`: dev fallback can print OTP codes in logs when SMTP is not configured.
  - `false`: intended for real SMTP delivery.
- `COOKIE_SECURE`
  - `false`: local HTTP development.
  - `true`: HTTPS deployments.

Runner hardening options:
- `PRACTICE_DOCTEST_TIMEOUT_SECONDS` (default `5`)
- `PRACTICE_DOCTEST_OUTPUT_MAX_BYTES` (default `262144` per stream)

## Migration Note: Bind Mount -> Named Volume

When switching from dev bind mount (`./.practice:/data`) to prod-like named volume (`practice_data`), existing host data is not auto-copied.

One-time copy:

```bash
docker run --rm \
  -v "$(pwd)/.practice:/from:ro" \
  -v practice_data:/to \
  alpine sh -c "cp -a /from/. /to/"
```

Then start prod-like compose.

## Notes

- Problems are imported from `9021/` by default.
- Statement markdown files are generated on demand under `statements/`.
- Web `Run` uses the same doctest runner as CLI `run`.
