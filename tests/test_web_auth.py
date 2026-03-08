from __future__ import annotations

import pytest
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app import db
from app.config import get_paths
from app.web import _hash_password, create_app


def _install_code_capture(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    sent: dict[str, str] = {}

    def fake_send(email: str, code: str) -> None:
        sent[email] = code

    monkeypatch.setattr("app.web._send_login_code_email", fake_send)
    return sent


def _insert_user(email: str, password: str) -> None:
    conn = db.connect(get_paths().db_path)
    try:
        conn.execute(
            """
            INSERT INTO users(email, password_hash, created_at, email_verified)
            VALUES(?, ?, ?, 1)
            """,
            (email, _hash_password(password), db.utc_now_iso()),
        )
        conn.commit()
    finally:
        conn.close()


def test_register_flow_creates_user_and_session(isolated_env, monkeypatch):
    sent = _install_code_capture(monkeypatch)
    client = TestClient(create_app())
    email = "new_user@example.com"

    request_resp = client.post("/api/auth/register/request_code", json={"email": email})
    assert request_resp.status_code == 200
    assert request_resp.json()["ok"] is True
    assert email in sent

    verify_resp = client.post(
        "/api/auth/register/verify",
        json={"email": email, "password": "strongpass123", "code": sent[email]},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["ok"] is True

    conn = db.connect(get_paths().db_path)
    try:
        row = conn.execute("SELECT email FROM users WHERE email = ?", (email,)).fetchone()
        assert row is not None
    finally:
        conn.close()

    problems_resp = client.get("/api/problems")
    assert problems_resp.status_code == 200


def test_login_password_rejects_unregistered(isolated_env):
    client = TestClient(create_app())
    resp = client.post(
        "/api/auth/login/password",
        json={"email": "missing@example.com", "password": "whatever"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not registered"


def test_login_password_locks_after_too_many_attempts(isolated_env):
    email = "lock_me@example.com"
    _insert_user(email, "right-password")
    client = TestClient(create_app())

    for _ in range(5):
        resp = client.post(
            "/api/auth/login/password",
            json={"email": email, "password": "wrong-password"},
        )
        assert resp.status_code == 401

    locked_resp = client.post(
        "/api/auth/login/password",
        json={"email": email, "password": "wrong-password"},
    )
    assert locked_resp.status_code == 429


def test_login_otp_flow_for_registered_user(isolated_env, monkeypatch):
    sent = _install_code_capture(monkeypatch)
    email = "otp_user@example.com"
    _insert_user(email, "secret-pass")
    client = TestClient(create_app())

    request_resp = client.post("/api/auth/login/request_code", json={"email": email})
    assert request_resp.status_code == 200
    assert request_resp.json()["ok"] is True
    assert email in sent

    verify_resp = client.post(
        "/api/auth/login/verify",
        json={"email": email, "code": sent[email]},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["ok"] is True

    problems_resp = client.get("/api/problems")
    assert problems_resp.status_code == 200


def test_login_otp_rejects_unregistered(isolated_env, monkeypatch):
    _install_code_capture(monkeypatch)
    client = TestClient(create_app())
    resp = client.post("/api/auth/login/request_code", json={"email": "missing2@example.com"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not registered"
