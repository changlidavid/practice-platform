from __future__ import annotations

import json

from app import db, runner
from app.config import get_paths


def _seed_function_problem(conn, tmp_path):
    bundle_root = tmp_path / "bundle_json"
    problem_dir = bundle_root / "two_sum"
    problem_dir.mkdir(parents=True, exist_ok=True)
    (problem_dir / "hidden_tests.json").write_text(
        json.dumps(
            {
                "version": 1,
                "cases": [
                    {"id": "c1", "args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
                    {"id": "c2", "args": [[3, 2, 4], 6], "expected": [1, 2]},
                ],
            }
        ),
        encoding="utf-8",
    )
    (problem_dir / "public_examples.json").write_text(
        json.dumps(
            [
                {
                    "id": "pub-1",
                    "input": "nums = [2, 7, 11, 15]\ntarget = 9",
                    "output": "[0, 1]",
                },
                {
                    "id": "pub-2",
                    "input": "nums = [3, 2, 4]\ntarget = 6",
                    "output": "[1, 2]",
                },
            ]
        ),
        encoding="utf-8",
    )

    bundle_id = db.insert_bundle(conn, "bundle_json", str(bundle_root), "bundle-json-hash")
    db.upsert_problem(
        conn,
        bundle_id=bundle_id,
        slug="bundle_json:two_sum",
        title="Two Sum",
        description="Find indices.",
        template_code="def two_sum(nums, target):\n    return []\n",
        doctest="",
        source_relpath="two_sum/starter.py",
        assets_manifest=[],
        content_hash="hash-two-sum",
        evaluation_mode="function_json",
        entry_function="two_sum",
        problem_dir_relpath="two_sum",
        public_examples_json="[]",
        statement_md="# Two Sum\n",
    )
    row = db.get_problem(conn, "bundle_json:two_sum")
    assert row is not None
    return row


def test_function_json_runner_passes_hidden_cases(isolated_env, tmp_path):
    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = _seed_function_problem(conn, tmp_path)
        solution = """\
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        need = target - n
        if need in seen:
            return [seen[need], i]
        seen[n] = i
    return []
"""
        _, result = runner.run_problem(
            conn,
            paths,
            row,
            solution_content=solution,
            function_json_feedback_mode="submit",
        )
        assert result.status == "pass"
        assert result.passed == 2
        assert result.failed == 0
        assert result.feedback is not None
        assert result.feedback["summary"]["total_hidden"] == 2
        assert result.feedback["first_failure"] is None
    finally:
        conn.close()


def test_function_json_runner_run_uses_public_examples(isolated_env, tmp_path):
    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = _seed_function_problem(conn, tmp_path)
        solution = """\
def two_sum(nums, target):
    return [0, 0]
"""
        _, result = runner.run_problem(
            conn,
            paths,
            row,
            solution_content=solution,
            function_json_feedback_mode="run",
        )
        assert result.status == "fail"
        assert result.failed == 2
        assert result.feedback is not None
        public_examples = result.feedback["public_examples"]
        assert len(public_examples) == 2
        assert public_examples[0]["id"] == "pub-1"
        assert public_examples[0]["input"] == "nums = [2, 7, 11, 15]\ntarget = 9"
        assert public_examples[0]["expected"] == [0, 1]
        assert public_examples[0]["actual"] == [0, 0]
        assert public_examples[0]["passed"] is False
    finally:
        conn.close()


def test_function_json_runner_submit_returns_only_first_failure(isolated_env, tmp_path):
    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = _seed_function_problem(conn, tmp_path)
        solution = """\
def two_sum(nums, target):
    return [0, 0]
"""
        _, result = runner.run_problem(
            conn,
            paths,
            row,
            solution_content=solution,
            function_json_feedback_mode="submit",
        )
        assert result.status == "fail"
        assert result.failed == 2
        assert result.feedback is not None
        summary = result.feedback["summary"]
        assert summary["total_hidden"] == 2
        assert summary["passed_hidden"] == 0
        assert summary["failed_hidden"] == 2
        first_failure = result.feedback["first_failure"]
        assert first_failure["case_id"] == "c1"
        assert first_failure["case_label"] == "Hidden case #1"
        assert first_failure["message"] == "Wrong answer"
        assert first_failure["failure_type"] == "Wrong Answer"
        assert first_failure["actual"] == [0, 0]
        assert first_failure["expected"] == [0, 1]
        assert "arg1=list(len=4)" in first_failure["input_summary"]
        assert "arg2=int" in first_failure["input_summary"]
        dumped = json.dumps(result.feedback)
        assert "c2" not in dumped
    finally:
        conn.close()


def test_function_json_runner_errors_when_target_missing(isolated_env, tmp_path):
    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        row = _seed_function_problem(conn, tmp_path)
        solution = """\
def not_two_sum(nums, target):
    return [0, 1]
"""
        _, result = runner.run_problem(
            conn,
            paths,
            row,
            solution_content=solution,
            function_json_feedback_mode="submit",
        )
        assert result.status == "error"
        assert result.failed == 0
        assert "not found" in (result.stdout + result.stderr).lower()
        assert result.feedback is not None
        assert result.feedback["first_failure"]["failure_type"] == "Import Error"
    finally:
        conn.close()
