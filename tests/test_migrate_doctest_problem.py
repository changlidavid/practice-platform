from __future__ import annotations

import json
import subprocess
import sys


def test_migrate_doctest_problem_generates_function_json_bundle(repo_root, tmp_path):
    source = repo_root / "9021" / "sample_1.py"
    output_root = tmp_path / "problems_out"
    script = repo_root / "scripts" / "migrate_doctest_problem.py"

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            str(source),
            "--output-root",
            str(output_root),
            "--public-count",
            "3",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    problem_dir = output_root / "remove_consecutive_duplicates"
    assert problem_dir.exists()

    meta = json.loads((problem_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["slug"] == "remove_consecutive_duplicates"
    assert meta["entry_function"] == "remove_consecutive_duplicates"
    assert meta["evaluation_mode"] == "function_json"

    public_examples = json.loads((problem_dir / "public_examples.json").read_text(encoding="utf-8"))
    assert len(public_examples) == 3
    assert public_examples[0]["input"] == "word = ''"
    assert public_examples[0]["output"] == "''"

    hidden_tests = json.loads((problem_dir / "hidden_tests.json").read_text(encoding="utf-8"))
    assert len(hidden_tests["cases"]) == 7
    assert hidden_tests["cases"][0]["args"] == [""]
    assert hidden_tests["cases"][-1]["expected"] == "abacacd"


def test_migrate_doctest_problem_rejects_print_style_examples(repo_root, tmp_path):
    source = repo_root / "9021" / "sample_2.py"
    output_root = tmp_path / "problems_out"
    script = repo_root / "scripts" / "migrate_doctest_problem.py"

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            str(source),
            "--output-root",
            str(output_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "Print-based" in completed.stderr or "not a Python literal" in completed.stderr
