from __future__ import annotations

import hmac
import hashlib
import json
import os
import re
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from html import escape
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db, importer, runner
from .config import ensure_workspace, get_paths, load_env_file
from .statements import ensure_statement

try:
    import markdown  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    markdown = None


OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
OTP_ATTEMPTS = 5
OTP_SEND_COOLDOWN_SECONDS = 60
SESSION_DAYS = 7
PASSWORD_MIN_LENGTH = 8
PASSWORD_HASH_ITERATIONS = 310_000
PASSWORD_MAX_ATTEMPTS = 5
PASSWORD_LOCK_MINUTES = 10
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _to_iso(dt: datetime) -> str:
    return dt.isoformat()


def _from_iso(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iterations_raw, salt_hex, hash_hex = encoded.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
        expected = bytes.fromhex(hash_hex)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, TypeError):
        return False
    got = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(got, expected)


def _validate_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email))


def _cookie_secure() -> bool:
    return os.environ.get("COOKIE_SECURE", "").strip().lower() in {"1", "true", "yes"}


def _smtp_use_tls() -> bool:
    return os.environ.get("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes"}


def _smtp_port() -> int:
    raw = os.environ.get("SMTP_PORT", "").strip()
    return int(raw) if raw else 587


def _otp_dev_mode_enabled() -> bool:
    return os.environ.get("OTP_DEV_MODE", "").strip().lower() in {"1", "true", "yes"}


def _send_login_code_email(email: str, code: str) -> None:
    host = os.environ.get("SMTP_HOST", "").strip()
    username = os.environ.get("SMTP_USERNAME", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    from_addr = os.environ.get("SMTP_FROM", "").strip()
    if "gmail.com" in host.lower():
        # Gmail app passwords are often copied with spaces between 4-char groups.
        password = password.replace(" ", "")
    if not host or not from_addr:
        if _otp_dev_mode_enabled():
            print(f"[otp-dev] email={email} code={code} expires_in={OTP_EXPIRY_MINUTES}m")
            return
        raise HTTPException(
            status_code=500,
            detail=(
                "SMTP is not configured. Set SMTP_HOST and SMTP_FROM, "
                "or enable OTP_DEV_MODE=true for local terminal OTP output."
            ),
        )

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = email
    msg["Subject"] = "Your Local Practice verification code"
    msg.set_content(
        f"Your Local Practice verification code is: {code}\n\n"
        f"It expires in {OTP_EXPIRY_MINUTES} minutes.\n"
    )

    port = _smtp_port()
    try:
        if _smtp_use_tls():
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.starttls()
                if username:
                    server.login(username, password)
                server.send_message(msg)
            return

        with smtplib.SMTP(host, port, timeout=10) as server:
            if username:
                server.login(username, password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "SMTP authentication failed. For Gmail, use your full Gmail address as SMTP_USERNAME "
                "and a Google App Password as SMTP_PASSWORD (no spaces)."
            ),
        ) from exc
    except smtplib.SMTPException as exc:
        raise HTTPException(status_code=502, detail=f"SMTP error: {exc}") from exc


def _cleanup_auth_rows(conn) -> None:
    now_iso = _to_iso(_utc_now())
    conn.execute("DELETE FROM auth_otps WHERE expires_at < ?", (now_iso,))
    conn.execute("DELETE FROM auth_sessions WHERE expires_at < ?", (now_iso,))
    conn.commit()


def _ensure_registered_user(conn, email: str):
    row = conn.execute(
        """
        SELECT id, email, password_hash, failed_login_count, locked_until
        FROM users
        WHERE email = ?
        """,
        (email,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not registered")
    return row


def _rate_limit_send_code(conn, *, email: str, purpose: str, now: datetime) -> None:
    row = conn.execute(
        """
        SELECT last_sent_at
        FROM auth_otps
        WHERE email = ? AND purpose = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (email, purpose),
    ).fetchone()
    if row is None or row["last_sent_at"] is None:
        return
    seconds_since_last = (now - _from_iso(str(row["last_sent_at"]))).total_seconds()
    if seconds_since_last < OTP_SEND_COOLDOWN_SECONDS:
        raise HTTPException(
            status_code=429,
            detail="Please wait before requesting another code.",
        )


def _store_otp(conn, *, email: str, purpose: str, code: str, now: datetime) -> str:
    created_at = _to_iso(now)
    conn.execute(
        """
        INSERT INTO auth_otps(email, purpose, code_hash, created_at, expires_at, attempts_remaining, last_sent_at)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email,
            purpose,
            _hash_text(code),
            created_at,
            _to_iso(now + timedelta(minutes=OTP_EXPIRY_MINUTES)),
            OTP_ATTEMPTS,
            created_at,
        ),
    )
    conn.commit()
    return created_at


def _verify_otp(conn, *, email: str, purpose: str, code: str, now: datetime) -> None:
    otp_row = conn.execute(
        """
        SELECT id, code_hash, expires_at, attempts_remaining
        FROM auth_otps
        WHERE email = ? AND purpose = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (email, purpose),
    ).fetchone()
    if otp_row is None:
        raise HTTPException(status_code=401, detail="Invalid or expired code")

    if _from_iso(str(otp_row["expires_at"])) <= now:
        raise HTTPException(status_code=401, detail="Invalid or expired code")

    attempts_remaining = int(otp_row["attempts_remaining"])
    if attempts_remaining <= 0:
        raise HTTPException(status_code=401, detail="No attempts remaining")

    if _hash_text(code) != str(otp_row["code_hash"]):
        conn.execute(
            "UPDATE auth_otps SET attempts_remaining = ? WHERE id = ?",
            (attempts_remaining - 1, int(otp_row["id"])),
        )
        conn.commit()
        raise HTTPException(status_code=401, detail="Invalid or expired code")


def _create_session_response(conn, *, email: str, now: datetime) -> JSONResponse:
    token = secrets.token_urlsafe(32)
    conn.execute("DELETE FROM auth_sessions WHERE email = ?", (email,))
    conn.execute(
        """
        INSERT INTO auth_sessions(email, token_hash, created_at, expires_at)
        VALUES(?, ?, ?, ?)
        """,
        (
            email,
            _hash_text(token),
            _to_iso(now),
            _to_iso(now + timedelta(days=SESSION_DAYS)),
        ),
    )
    conn.commit()
    response = JSONResponse({"ok": True})
    response.set_cookie(
        key="session",
        value=token,
        max_age=SESSION_DAYS * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(),
        path="/",
    )
    return response


def _session_email_or_none(request: Request) -> str | None:
    token = request.cookies.get("session")
    if not token:
        return None

    conn = db.connect(get_paths().db_path)
    try:
        _cleanup_auth_rows(conn)
        row = conn.execute(
            """
            SELECT email
            FROM auth_sessions
            WHERE token_hash = ? AND expires_at > ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (_hash_text(token), _to_iso(_utc_now())),
        ).fetchone()
        if row is None:
            return None
        return str(row["email"])
    finally:
        conn.close()


def _require_session_api(request: Request) -> str:
    email = _session_email_or_none(request)
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return email


def _bootstrap(conn, paths) -> None:
    db.init_db(conn)
    raw_paths = os.environ.get("PRACTICE_BUNDLE_PATHS", "").strip()
    if raw_paths:
        candidates: list[Path] = []
        seen: set[str] = set()
        for raw_part in raw_paths.split(","):
            part = raw_part.strip()
            if not part:
                continue
            source_root = Path(part).expanduser()
            if not source_root.is_absolute():
                source_root = paths.repo_root / source_root
            resolved = source_root.resolve()
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(resolved)
    else:
        candidates = [paths.source_bundle]

    imported_roots: list[str] = []
    for source_root in candidates:
        if not source_root.exists() or not source_root.is_dir():
            continue
        try:
            importer.import_bundle(conn, paths, source_root)
            imported_roots.append(str(source_root.resolve()))
        except (FileNotFoundError, RuntimeError):
            # Keep startup resilient when a configured bundle path is invalid.
            continue
    if imported_roots:
        db.prune_bundles_not_in_source_roots(conn, allowed_source_roots=imported_roots)


def _normalize_row(row: Any) -> dict[str, Any]:
    slug = str(row["slug"])
    display_name = slug.split(":", 1)[1] if ":" in slug else slug
    return {
        "id": int(row["id"]),
        "slug": slug,
        "display_name": display_name,
        "title": str(row["title"]),
        "bundle_name": str(row["bundle_name"]),
        "source_relpath": str(row["source_relpath"]),
        "attempts": int(row["attempts"]),
        "last_status": str(row["last_status"]),
        "last_run": row["last_run"],
    }


def _load_rows(*, user_id: int | None = None) -> list[dict[str, Any]]:
    paths = get_paths()
    conn = db.connect(paths.db_path)
    try:
        return [_normalize_row(row) for row in db.list_problems(conn, user_id=user_id)]
    finally:
        conn.close()


def _problem_or_404(conn, problem_id: int):
    row = db.get_problem(conn, str(problem_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return row


def _require_session_user(conn, request: Request):
    email = _require_session_api(request)
    user = db.get_user_by_email(conn, email)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


def _render_markdown(md_text: str) -> str:
    if markdown is None:
        return f"<pre>{escape(md_text)}</pre>"
    return markdown.markdown(md_text, extensions=["fenced_code", "tables", "nl2br"])


def _public_examples(row: Any) -> list[dict[str, Any]]:
    raw = str(row["public_examples_json"] or "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        items = parsed.get("examples")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def create_app() -> FastAPI:
    paths = get_paths()
    load_env_file(paths.repo_root)
    ensure_workspace(paths)

    conn = db.connect(paths.db_path)
    try:
        _bootstrap(conn, paths)
    finally:
        conn.close()

    app = FastAPI(title="Practice Web UI")

    templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
    app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")

    def _auth_page(request: Request) -> Response:
        if _session_email_or_none(request):
            return RedirectResponse(url="/", status_code=303)
        return templates.TemplateResponse("login.html", {"request": request})

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request) -> Response:
        return _auth_page(request)

    @app.get("/auth", response_class=HTMLResponse)
    def auth_page(request: Request) -> Response:
        return _auth_page(request)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> Response:
        email = _session_email_or_none(request)
        if not email:
            return RedirectResponse(url="/login", status_code=303)
        conn = db.connect(get_paths().db_path)
        try:
            user = db.get_user_by_email(conn, email)
            if user is None:
                return RedirectResponse(url="/login", status_code=303)
            rows = [_normalize_row(row) for row in db.list_problems(conn, user_id=int(user["id"]))]
        finally:
            conn.close()
        selected_id = rows[0]["id"] if rows else None
        return templates.TemplateResponse(
            "web.html",
            {
                "request": request,
                "rows": rows,
                "selected_id": selected_id,
                "session_email": email,
            },
        )

    async def _json_payload_or_empty(request: Request) -> dict[str, Any]:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        return payload if isinstance(payload, dict) else {}

    @app.post("/api/auth/register/request_code")
    async def api_register_request_code(request: Request) -> dict[str, bool]:
        payload = await _json_payload_or_empty(request)
        email = str(payload.get("email", "")).strip().lower()
        if not _validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email")

        now = _utc_now()
        conn = db.connect(get_paths().db_path)
        try:
            _cleanup_auth_rows(conn)
            existing = conn.execute(
                "SELECT id FROM users WHERE email = ? LIMIT 1", (email,)
            ).fetchone()
            if existing is not None:
                raise HTTPException(status_code=409, detail="Email already registered")
            _rate_limit_send_code(conn, email=email, purpose="register", now=now)
            code = f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"
            created_at = _store_otp(conn, email=email, purpose="register", code=code, now=now)
        finally:
            conn.close()

        try:
            _send_login_code_email(email, code)
        except Exception:
            conn = db.connect(get_paths().db_path)
            try:
                conn.execute(
                    """
                    DELETE FROM auth_otps
                    WHERE email = ? AND purpose = 'register' AND created_at = ?
                    """,
                    (email, created_at),
                )
                conn.commit()
            finally:
                conn.close()
            raise
        return {"ok": True}

    @app.post("/api/auth/register/verify")
    async def api_register_verify(request: Request) -> JSONResponse:
        payload = await _json_payload_or_empty(request)
        email = str(payload.get("email", "")).strip().lower()
        code = str(payload.get("code", "")).strip()
        password = str(payload.get("password", ""))
        if not _validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email")
        if not (code.isdigit() and len(code) == OTP_LENGTH):
            raise HTTPException(status_code=400, detail="Invalid code format")
        if len(password) < PASSWORD_MIN_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters.",
            )

        now = _utc_now()
        conn = db.connect(get_paths().db_path)
        try:
            _cleanup_auth_rows(conn)
            if conn.execute("SELECT id FROM users WHERE email = ? LIMIT 1", (email,)).fetchone():
                raise HTTPException(status_code=409, detail="Email already registered")
            _verify_otp(conn, email=email, purpose="register", code=code, now=now)
            conn.execute(
                """
                INSERT INTO users(email, password_hash, created_at, email_verified)
                VALUES(?, ?, ?, 1)
                """,
                (email, _hash_password(password), _to_iso(now)),
            )
            conn.execute(
                "DELETE FROM auth_otps WHERE email = ? AND purpose = 'register'", (email,)
            )
            response = _create_session_response(conn, email=email, now=now)
        except HTTPException:
            raise
        except Exception as exc:
            if "UNIQUE constraint failed: users.email" in str(exc):
                raise HTTPException(status_code=409, detail="Email already registered") from exc
            raise
        finally:
            conn.close()
        return response

    @app.post("/api/auth/login/password")
    async def api_login_password(request: Request) -> JSONResponse:
        payload = await _json_payload_or_empty(request)
        email = str(payload.get("email", "")).strip().lower()
        password = str(payload.get("password", ""))
        if not _validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email")
        if not password:
            raise HTTPException(status_code=400, detail="Password is required")

        now = _utc_now()
        conn = db.connect(get_paths().db_path)
        try:
            _cleanup_auth_rows(conn)
            user = _ensure_registered_user(conn, email)
            locked_until_raw = user["locked_until"]
            if locked_until_raw:
                locked_until = _from_iso(str(locked_until_raw))
                if locked_until > now:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many failed attempts. Please try again later.",
                    )
            if not _verify_password(password, str(user["password_hash"])):
                failed_count = int(user["failed_login_count"]) + 1
                lock_until = None
                if failed_count >= PASSWORD_MAX_ATTEMPTS:
                    failed_count = 0
                    lock_until = _to_iso(now + timedelta(minutes=PASSWORD_LOCK_MINUTES))
                conn.execute(
                    "UPDATE users SET failed_login_count = ?, locked_until = ? WHERE id = ?",
                    (failed_count, lock_until, int(user["id"])),
                )
                conn.commit()
                raise HTTPException(status_code=401, detail="Invalid email or password")
            conn.execute(
                "UPDATE users SET failed_login_count = 0, locked_until = NULL WHERE id = ?",
                (int(user["id"]),),
            )
            response = _create_session_response(conn, email=email, now=now)
        finally:
            conn.close()
        return response

    @app.post("/api/auth/login/request_code")
    async def api_login_request_code(request: Request) -> dict[str, bool]:
        payload = await _json_payload_or_empty(request)
        email = str(payload.get("email", "")).strip().lower()
        if not _validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email")

        now = _utc_now()
        conn = db.connect(get_paths().db_path)
        try:
            _cleanup_auth_rows(conn)
            _ensure_registered_user(conn, email)
            _rate_limit_send_code(conn, email=email, purpose="login", now=now)
            code = f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"
            created_at = _store_otp(conn, email=email, purpose="login", code=code, now=now)
        finally:
            conn.close()

        try:
            _send_login_code_email(email, code)
        except Exception:
            conn = db.connect(get_paths().db_path)
            try:
                conn.execute(
                    """
                    DELETE FROM auth_otps
                    WHERE email = ? AND purpose = 'login' AND created_at = ?
                    """,
                    (email, created_at),
                )
                conn.commit()
            finally:
                conn.close()
            raise
        return {"ok": True}

    @app.post("/api/auth/login/verify")
    async def api_login_verify(request: Request) -> JSONResponse:
        payload = await _json_payload_or_empty(request)
        email = str(payload.get("email", "")).strip().lower()
        code = str(payload.get("code", "")).strip()
        if not _validate_email(email):
            raise HTTPException(status_code=400, detail="Invalid email")
        if not (code.isdigit() and len(code) == OTP_LENGTH):
            raise HTTPException(status_code=400, detail="Invalid code format")

        now = _utc_now()
        conn = db.connect(get_paths().db_path)
        try:
            _cleanup_auth_rows(conn)
            _ensure_registered_user(conn, email)
            _verify_otp(conn, email=email, purpose="login", code=code, now=now)
            conn.execute("DELETE FROM auth_otps WHERE email = ? AND purpose = 'login'", (email,))
            response = _create_session_response(conn, email=email, now=now)
        finally:
            conn.close()
        return response

    @app.post("/api/auth/request_code")
    async def api_auth_request_code_legacy(request: Request) -> dict[str, bool]:
        return await api_login_request_code(request)

    @app.post("/api/auth/verify_code")
    async def api_auth_verify_code_legacy(request: Request) -> JSONResponse:
        return await api_login_verify(request)

    @app.post("/api/auth/logout")
    def api_auth_logout(request: Request) -> Response:
        token = request.cookies.get("session")
        if token:
            conn = db.connect(get_paths().db_path)
            try:
                conn.execute("DELETE FROM auth_sessions WHERE token_hash = ?", (_hash_text(token),))
                conn.commit()
            finally:
                conn.close()

        response = JSONResponse({"ok": True})
        response.delete_cookie(key="session", path="/")
        return response

    @app.get("/api/me")
    def api_me(request: Request) -> dict[str, str]:
        email = _require_session_api(request)
        return {"email": email}

    @app.get("/api/problems")
    def api_problems(request: Request) -> dict[str, Any]:
        conn = db.connect(get_paths().db_path)
        try:
            user = _require_session_user(conn, request)
            return {
                "problems": [
                    _normalize_row(row)
                    for row in db.list_problems(conn, user_id=int(user["id"]))
                ]
            }
        finally:
            conn.close()

    @app.get("/api/problems/{problem_id}")
    @app.get("/api/problem/{problem_id}")
    def api_problem(problem_id: int, request: Request) -> dict[str, Any]:
        _require_session_api(request)
        paths = get_paths()
        conn = db.connect(paths.db_path)
        try:
            row = _problem_or_404(conn, problem_id)
            statement_file = ensure_statement(paths, row)
            statement_md = statement_file.read_text(encoding="utf-8")
            statement_html = _render_markdown(statement_md)

            return {
                "problem": {
                    "id": int(row["id"]),
                    "slug": str(row["slug"]),
                    "display_name": str(row["slug"]).split(":", 1)[1]
                    if ":" in str(row["slug"])
                    else str(row["slug"]),
                    "title": str(row["title"]),
                    "description": str(row["description"]),
                    "source_relpath": str(row["source_relpath"]),
                },
                "statement_markdown": statement_md,
                "statement_html": statement_html,
                "statement_path": str(statement_file),
                "public_examples": _public_examples(row),
            }
        finally:
            conn.close()

    @app.get("/api/solution/{problem_id}")
    def api_get_solution(problem_id: int, request: Request) -> dict[str, str]:
        conn = db.connect(get_paths().db_path)
        try:
            user = _require_session_user(conn, request)
            row = _problem_or_404(conn, problem_id)
            user_solution = db.ensure_user_solution(
                conn,
                user_id=int(user["id"]),
                problem_row=row,
            )
            return {
                "path": f"db://users/{user['id']}/problems/{row['id']}/solution",
                "content": str(user_solution["content"]),
            }
        finally:
            conn.close()

    @app.put("/api/solution/{problem_id}")
    async def api_put_solution(problem_id: int, request: Request) -> dict[str, Any]:
        content: str | None = None
        content_type = request.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            try:
                payload = await request.json()
            except Exception:
                payload = None
            if isinstance(payload, dict):
                for key in ("content", "code", "solution", "text"):
                    value = payload.get(key)
                    if isinstance(value, str):
                        content = value
                        break
            elif isinstance(payload, str):
                content = payload

        if content is None:
            raw_body = await request.body()
            if raw_body:
                content = raw_body.decode("utf-8")

        if content is None:
            raise HTTPException(
                status_code=400,
                detail='Missing solution content; send JSON like {"content": "..."}',
            )

        conn = db.connect(get_paths().db_path)
        try:
            user = _require_session_user(conn, request)
            row = _problem_or_404(conn, problem_id)
            db.upsert_user_solution(
                conn,
                user_id=int(user["id"]),
                problem_id=int(row["id"]),
                content=content,
            )
            return {"ok": True, "path": f"db://users/{user['id']}/problems/{row['id']}/solution"}
        finally:
            conn.close()

    @app.post("/api/run/{problem_id}")
    def api_run(problem_id: int, request: Request) -> dict[str, Any]:
        paths = get_paths()
        conn = db.connect(paths.db_path)
        try:
            user = _require_session_user(conn, request)
            row = _problem_or_404(conn, problem_id)
            user_solution = db.ensure_user_solution(
                conn,
                user_id=int(user["id"]),
                problem_row=row,
            )
            attempt_id, result = runner.run_problem(
                conn,
                paths,
                row,
                user_id=int(user["id"]),
                solution_content=str(user_solution["content"]),
                function_json_feedback_mode="run",
            )
            db.update_user_problem_stats_after_run(
                conn,
                user_id=int(user["id"]),
                problem_id=int(row["id"]),
                status=result.status,
            )
            payload: dict[str, Any] = {
                "attempt_id": attempt_id,
                "mode": "run",
                "status": result.status,
                "passed": result.passed,
                "failed": result.failed,
                "exit_code": result.exit_code,
                "time_ms": result.duration_ms,
            }
            if result.feedback is not None:
                payload.update(result.feedback)
            else:
                payload["output"] = (result.stdout + "\n" + result.stderr).strip()
            return payload
        finally:
            conn.close()

    @app.post("/api/submit/{problem_id}")
    def api_submit(problem_id: int, request: Request) -> dict[str, Any]:
        paths = get_paths()
        conn = db.connect(paths.db_path)
        try:
            user = _require_session_user(conn, request)
            row = _problem_or_404(conn, problem_id)
            user_solution = db.ensure_user_solution(
                conn,
                user_id=int(user["id"]),
                problem_row=row,
            )
            attempt_id, result = runner.run_problem(
                conn,
                paths,
                row,
                user_id=int(user["id"]),
                solution_content=str(user_solution["content"]),
                function_json_feedback_mode="submit",
            )
            db.update_user_problem_stats_after_run(
                conn,
                user_id=int(user["id"]),
                problem_id=int(row["id"]),
                status=result.status,
            )
            payload = {
                "attempt_id": attempt_id,
                "mode": "submit",
                "status": result.status,
                "passed": result.passed,
                "failed": result.failed,
                "exit_code": result.exit_code,
                "time_ms": result.duration_ms,
            }
            if result.feedback is not None:
                payload.update(result.feedback)
            else:
                payload["output"] = (result.stdout + "\n" + result.stderr).strip()
            return payload
        finally:
            conn.close()

    return app


app = create_app()


def main() -> None:
    import uvicorn

    print("Server running on http://0.0.0.0:8000")
    print("LAN access: use your computer's local IP, e.g. http://192.168.x.x:8000")
    uvicorn.run("app.web:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
