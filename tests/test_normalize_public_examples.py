from __future__ import annotations

import json
import subprocess
import sys


def _seed_problem_dir(problem_dir, *, starter: str, public_examples: list[dict[str, str]]) -> None:
    problem_dir.mkdir(parents=True, exist_ok=True)
    (problem_dir / "starter.py").write_text(starter, encoding="utf-8")
    (problem_dir / "meta.json").write_text(
        json.dumps({"slug": problem_dir.name, "title": "Title", "entry_function": "filtered_sequence"}),
        encoding="utf-8",
    )
    (problem_dir / "statement.md").write_text("# Title\n", encoding="utf-8")
    (problem_dir / "hidden_tests.json").write_text(
        json.dumps({"version": 1, "cases": [{"id": "c1", "args": [[], 2], "kwargs": {}, "expected": []}]}),
        encoding="utf-8",
    )
    (problem_dir / "public_examples.json").write_text(
        json.dumps(public_examples, indent=2) + "\n",
        encoding="utf-8",
    )


def test_normalize_public_examples_rewrites_function_calls_and_tuple_assignments(repo_root, tmp_path):
    script = repo_root / "scripts" / "normalize_public_examples.py"
    root = tmp_path / "structured"
    problem_dir = root / "sample_problem"
    _seed_problem_dir(
        problem_dir,
        starter="def filtered_sequence(L, n):\n    return []\n",
        public_examples=[
            {"id": "ex-1", "input": "filtered_sequence([], 2)", "output": "[]"},
            {"id": "ex-2", "input": "L = [3, 3333, 33], n = 3", "output": "[3, 3333, 33]"},
        ],
    )

    completed = subprocess.run(
        [sys.executable, str(script), str(root)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads((problem_dir / "public_examples.json").read_text(encoding="utf-8"))
    assert payload[0]["input"] == "L = []\nn = 2"
    assert payload[1]["input"] == "L = [3, 3333, 33]\nn = 3"


def test_normalize_public_examples_dry_run_does_not_write(repo_root, tmp_path):
    script = repo_root / "scripts" / "normalize_public_examples.py"
    root = tmp_path / "problems"
    problem_dir = root / "sample_problem"
    _seed_problem_dir(
        problem_dir,
        starter="def upp(L):\n    return []\n",
        public_examples=[{"id": "ex-1", "input": "upp([])", "output": "[]"}],
    )

    completed = subprocess.run(
        [sys.executable, str(script), str(root), "--dry-run"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads((problem_dir / "public_examples.json").read_text(encoding="utf-8"))
    assert payload[0]["input"] == "upp([])"
