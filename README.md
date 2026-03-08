# Practice CLI + Web UI

Local offline practice runner for doctest-based Python problems.

## CLI quickstart

```bash
python -m app.cli list
python -m app.cli open sample_1
python -m app.cli run sample_1
```

## Run the web UI

Install deps (if needed):

```bash
pip install -e .
```

Start the server:

```bash
python -m app.web
```

Open:

- http://127.0.0.1:8000

## Notes

- Problems are imported from `9021/` by default.
- Solutions are edited in `.practice/solutions/`.
- Statement markdown files are generated on demand under `statements/`.
- The web `Run` button uses the same doctest runner as `python -m app.cli run`.
