from __future__ import annotations

import json
import subprocess
import sys


def _seed_structured_problem(problem_dir, *, slug: str, entry_function: str) -> None:
    problem_dir.mkdir(parents=True, exist_ok=True)
    (problem_dir / "meta.json").write_text(
        json.dumps(
            {
                "slug": slug,
                "title": "Title",
                "entry_function": entry_function,
                "evaluation_mode": "function_json",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (problem_dir / "starter.py").write_text(
        f"def {entry_function}(x):\n    return x\n",
        encoding="utf-8",
    )
    (problem_dir / "statement.md").write_text("# Title\n", encoding="utf-8")
    (problem_dir / "public_examples.json").write_text("[]\n", encoding="utf-8")
    (problem_dir / "hidden_tests.json").write_text('{"version": 1, "cases": []}\n', encoding="utf-8")


def test_rename_structured_problems_renames_directory_and_updates_meta(repo_root, tmp_path):
    script = repo_root / "scripts" / "rename_structured_problems.py"
    structured_root = tmp_path / "structured"
    old_dir = structured_root / "final__ugly__name"
    _seed_structured_problem(old_dir, slug="final__ugly__name", entry_function="sum_discarding_carry_overs")

    completed = subprocess.run(
        [sys.executable, str(script), "--root", str(structured_root)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    new_dir = structured_root / "sum_discarding_carry_overs"
    assert new_dir.exists()
    meta = json.loads((new_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["slug"] == "sum_discarding_carry_overs"


def test_rename_structured_problems_uses_fallback_for_generic_function_names(repo_root, tmp_path):
    script = repo_root / "scripts" / "rename_structured_problems.py"
    structured_root = tmp_path / "structured"
    ugly_dir = structured_root / "final__1754923206907syv__item__dfs__a"
    _seed_structured_problem(
        ugly_dir,
        slug="final__1754923206907syv__item__dfs__a",
        entry_function="f",
    )

    completed = subprocess.run(
        [sys.executable, str(script), "--root", str(structured_root)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert (structured_root / "f_dfs_a").exists()


def test_rename_structured_problems_resolves_collisions(repo_root, tmp_path):
    script = repo_root / "scripts" / "rename_structured_problems.py"
    structured_root = tmp_path / "structured"
    _seed_structured_problem(
        structured_root / "final__2__sample_1",
        slug="final__2__sample_1",
        entry_function="shared_name",
    )
    _seed_structured_problem(
        structured_root / "final__2__sample_3",
        slug="final__2__sample_3",
        entry_function="shared_name",
    )

    completed = subprocess.run(
        [sys.executable, str(script), "--root", str(structured_root)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert (structured_root / "shared_name").exists()
    assert (structured_root / "shared_name_sample_3").exists()
