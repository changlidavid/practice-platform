# Contributing

## Development Setup

```bash
git clone <your-repo-url>
cd 9021tasks
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
cp -n .env.example .env
```

## Running Locally

- Web app:

```bash
python -m app.web
```

- CLI:

```bash
python -m app.cli list
python -m app.cli run sample_1
```

## Testing

```bash
pytest -q
```

Please add or update tests for behavior changes.

## Pull Request Guidelines

- Keep PRs focused and small when possible.
- Do not include unrelated refactors.
- Update docs when behavior or configuration changes.
- Do not commit secrets (`.env`, API keys, SMTP passwords).

## Issues

When filing bugs, include:
- steps to reproduce
- expected vs actual behavior
- environment details (OS, Python version, Docker/non-Docker)
- relevant logs or traceback snippets
