from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app import runner
from app import db
from app import importer
from app.config import get_paths
from app.models import RunResult
from app.web import create_app


def _login(client: TestClient, email: str = "tester@example.com") -> None:
    token = f"test-session-token-{email}"
    now = datetime.now(tz=timezone.utc)
    conn = db.connect(get_paths().db_path)
    try:
        conn.execute(
            """
            INSERT INTO users(email, password_hash, created_at, email_verified)
            VALUES(?, ?, ?, 1)
            ON CONFLICT(email) DO NOTHING
            """,
            (email, "test-hash", now.isoformat()),
        )
        conn.execute(
            """
            INSERT INTO auth_sessions(email, token_hash, created_at, expires_at)
            VALUES(?, ?, ?, ?)
            """,
            (
                email,
                hashlib.sha256(token.encode("utf-8")).hexdigest(),
                now.isoformat(),
                (now + timedelta(days=7)).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    client.cookies.set("session", token)


def test_solution_put_and_run_contract(isolated_env, monkeypatch):
    app = create_app()
    client = TestClient(app)
    _login(client)

    problems = client.get("/api/problems").json()["problems"]
    assert problems
    problem_id = int(problems[0]["id"])

    get_resp = client.get(f"/api/solution/{problem_id}")
    assert get_resp.status_code == 200
    original = get_resp.json()["content"]

    updated = original + "\n# web-api-test\n"
    put_resp = client.put(
        f"/api/solution/{problem_id}",
        json={"content": updated},
        headers={"Content-Type": "application/json"},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["ok"] is True

    verify_resp = client.get(f"/api/solution/{problem_id}")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["content"] == updated

    def fake_run_problem(conn, paths, row, **kwargs):
        _ = (conn, paths, row)
        _ = kwargs
        return 99, RunResult(
            status="fail",
            passed=2,
            failed=1,
            exit_code=0,
            stdout="ok",
            stderr="",
            duration_ms=12,
            feedback={
                "mode": "run",
                "summary": {"total": 3, "passed": 2, "failed": 1},
                "public_examples": [
                    {
                        "id": "pub-1",
                        "input": "n = 1",
                        "expected": 2,
                        "actual": 1,
                        "passed": False,
                        "message": "Wrong answer",
                    }
                ],
            },
        )

    monkeypatch.setattr(runner, "run_problem", fake_run_problem)

    run_resp = client.post(f"/api/run/{problem_id}")
    assert run_resp.status_code == 200
    payload = run_resp.json()
    assert payload["attempt_id"] == 99
    assert payload["mode"] == "run"
    assert payload["status"] == "fail"
    assert payload["time_ms"] == 12
    assert payload["summary"]["total"] == 3
    assert payload["public_examples"][0]["id"] == "pub-1"


def test_practice_state_is_isolated_per_user(isolated_env, monkeypatch):
    app = create_app()
    client_a = TestClient(app)
    client_b = TestClient(app)
    _login(client_a, "a@example.com")
    _login(client_b, "b@example.com")

    problem_id = int(client_a.get("/api/problems").json()["problems"][0]["id"])

    default_a = client_a.get(f"/api/solution/{problem_id}").json()["content"]
    default_b = client_b.get(f"/api/solution/{problem_id}").json()["content"]
    assert default_a == default_b

    edited_a = default_a + "\n# only-user-a\n"
    put_a = client_a.put(f"/api/solution/{problem_id}", json={"content": edited_a})
    assert put_a.status_code == 200

    def fake_run_problem(conn, paths, row, **kwargs):
        _ = (conn, paths, row, kwargs)
        return 101, RunResult(
            status="pass",
            passed=1,
            failed=0,
            exit_code=0,
            stdout="ok",
            stderr="",
            duration_ms=8,
            feedback={"mode": "run", "summary": {"total": 1, "passed": 1, "failed": 0}, "public_examples": []},
        )

    monkeypatch.setattr(runner, "run_problem", fake_run_problem)
    run_a = client_a.post(f"/api/run/{problem_id}")
    assert run_a.status_code == 200
    assert run_a.json()["status"] == "pass"

    now_b = client_b.get(f"/api/solution/{problem_id}").json()["content"]
    assert now_b == default_b
    assert now_b != edited_a

    problems_b = client_b.get("/api/problems")
    assert problems_b.status_code == 200
    row_b = next(row for row in problems_b.json()["problems"] if int(row["id"]) == problem_id)
    assert int(row_b["attempts"]) == 0
    assert row_b["last_status"] == "never"


def test_submit_api_returns_hidden_summary_and_first_failure_only(isolated_env, monkeypatch):
    app = create_app()
    client = TestClient(app)
    _login(client)

    problems = client.get("/api/problems").json()["problems"]
    assert problems
    problem_id = int(problems[0]["id"])

    def fake_run_problem(conn, paths, row, **kwargs):
        _ = (conn, paths, row, kwargs)
        return 202, RunResult(
            status="fail",
            passed=4,
            failed=1,
            exit_code=0,
            stdout="ok",
            stderr="",
            duration_ms=15,
            feedback={
                "mode": "submit",
                "summary": {
                    "total_hidden": 5,
                    "passed_hidden": 4,
                    "failed_hidden": 1,
                },
                "first_failure": {
                    "case_id": "hid-1",
                    "case_label": "Hidden case #1",
                    "message": "Wrong answer",
                    "failure_type": "Wrong Answer",
                    "actual": [0, 0],
                    "expected": [1, 2],
                    "input_summary": "arg1=list(len=4), arg2=int",
                },
            },
        )

    monkeypatch.setattr(runner, "run_problem", fake_run_problem)

    submit_resp = client.post(f"/api/submit/{problem_id}")
    assert submit_resp.status_code == 200
    payload = submit_resp.json()
    assert payload["attempt_id"] == 202
    assert payload["mode"] == "submit"
    assert payload["summary"]["total_hidden"] == 5
    assert payload["summary"]["passed_hidden"] == 4
    assert payload["summary"]["failed_hidden"] == 1
    assert payload["first_failure"]["case_id"] == "hid-1"
    assert payload["first_failure"]["case_label"] == "Hidden case #1"
    assert payload["first_failure"]["failure_type"] == "Wrong Answer"
    dumped = json.dumps(payload)
    assert "hidden_tests" not in dumped


def test_solution_put_accepts_legacy_payload_key(isolated_env):
    app = create_app()
    client = TestClient(app)
    _login(client)

    problems = client.get("/api/problems").json()["problems"]
    assert problems
    problem_id = int(problems[0]["id"])

    put_resp = client.put(
        f"/api/solution/{problem_id}",
        json={"code": "# legacy payload key\n"},
        headers={"Content-Type": "application/json"},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["ok"] is True


def test_api_requires_auth_session(isolated_env):
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/problems")
    assert resp.status_code == 401


def test_api_me_returns_email_and_requires_auth(isolated_env):
    app = create_app()
    client = TestClient(app)

    unauth = client.get("/api/me")
    assert unauth.status_code == 401

    _login(client, "me@example.com")
    auth = client.get("/api/me")
    assert auth.status_code == 200
    assert auth.json()["email"] == "me@example.com"


def test_index_redirects_to_login_when_not_authenticated(isolated_env):
    app = create_app()
    client = TestClient(app)
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"


def test_problem_api_returns_public_examples_not_hidden_tests(isolated_env, tmp_path):
    paths = get_paths()
    bundle_root = tmp_path / "function_api_bundle"
    problem_dir = bundle_root / "two_sum"
    problem_dir.mkdir(parents=True, exist_ok=True)
    (problem_dir / "meta.json").write_text(
        json.dumps({"slug": "two_sum", "title": "Two Sum", "entry_function": "two_sum"}),
        encoding="utf-8",
    )
    (problem_dir / "statement.md").write_text("# Two Sum\nReturn indices.\n", encoding="utf-8")
    (problem_dir / "starter.py").write_text(
        "def two_sum(nums, target):\n    return []\n",
        encoding="utf-8",
    )
    (problem_dir / "public_examples.json").write_text(
        json.dumps([{"id": "pub-1", "input": "nums=[2,7,11,15], target=9", "output": "[0,1]"}]),
        encoding="utf-8",
    )

    conn = db.connect(paths.db_path)
    try:
        db.init_db(conn)
        importer.import_bundle(conn, paths, bundle_root)
    finally:
        conn.close()

    app = create_app()
    client = TestClient(app)
    _login(client)

    all_rows = client.get("/api/problems").json()["problems"]
    target = next(row for row in all_rows if row["slug"] == "function_api_bundle:two_sum")
    payload = client.get(f"/api/problems/{target['id']}").json()

    assert payload["public_examples"]
    assert payload["public_examples"][0]["id"] == "pub-1"
    dumped = json.dumps(payload)
    assert "hidden_tests" not in dumped
    assert "hid-1" not in dumped


def test_problem_api_prefers_title_over_slug_for_display_name(isolated_env, tmp_path):
    paths = get_paths()
    bundle_root = tmp_path / "display_bundle"
    problem_dir = bundle_root / "ugly_problem_name_sample_3"
    problem_dir.mkdir(parents=True, exist_ok=True)
    (problem_dir / "meta.json").write_text(
        json.dumps(
            {
                "slug": "ugly_problem_name_sample_3",
                "title": "Good Subsequences",
                "entry_function": "good_subsequences",
            }
        ),
        encoding="utf-8",
    )
    (problem_dir / "statement.md").write_text("# Good Subsequences\nReturn subsequences.\n", encoding="utf-8")
    (problem_dir / "starter.py").write_text(
        "def good_subsequences(values):\n    return []\n",
        encoding="utf-8",
    )
    (problem_dir / "public_examples.json").write_text(
        json.dumps([{"id": "pub-1", "input": "values=[1,2]", "output": "[[1,2]]"}]),
        encoding="utf-8",
    )

    conn = db.connect(paths.db_path)
    try:
        db.init_db(conn)
        importer.import_bundle(conn, paths, bundle_root)
    finally:
        conn.close()

    app = create_app()
    client = TestClient(app)
    _login(client)

    rows = client.get("/api/problems").json()["problems"]
    target = next(row for row in rows if row["slug"] == "display_bundle:ugly_problem_name_sample_3")
    assert target["display_name"] == "Good Subsequences"

    payload = client.get(f"/api/problems/{target['id']}").json()
    assert payload["problem"]["display_name"] == "Good Subsequences"
