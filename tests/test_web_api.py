from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app import runner
from app import db
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
            status="pass",
            passed=5,
            failed=0,
            exit_code=0,
            stdout="ok",
            stderr="",
            duration_ms=12,
        )

    monkeypatch.setattr(runner, "run_problem", fake_run_problem)

    run_resp = client.post(f"/api/run/{problem_id}")
    assert run_resp.status_code == 200
    payload = run_resp.json()
    assert payload["attempt_id"] == 99
    assert payload["status"] == "pass"
    assert payload["time_ms"] == 12
    assert "output" in payload


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


def test_index_redirects_to_login_when_not_authenticated(isolated_env):
    app = create_app()
    client = TestClient(app)
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == "/login"
