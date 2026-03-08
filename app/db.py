from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL
        );

        INSERT INTO schema_version (id, version)
        VALUES (1, 1)
        ON CONFLICT(id) DO NOTHING;

        CREATE TABLE IF NOT EXISTS bundles (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            source_root TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL UNIQUE,
            imported_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY,
            slug TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            template_code TEXT NOT NULL DEFAULT '',
            doctest TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT '',
            bundle_id INTEGER,
            source_relpath TEXT NOT NULL DEFAULT '',
            assets_manifest_json TEXT NOT NULL DEFAULT '[]',
            content_hash TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(bundle_id) REFERENCES bundles(id)
        );

        CREATE TABLE IF NOT EXISTS bundle_assets (
            id INTEGER PRIMARY KEY,
            bundle_id INTEGER NOT NULL,
            relpath TEXT NOT NULL,
            content BLOB NOT NULL,
            UNIQUE(bundle_id, relpath),
            FOREIGN KEY(bundle_id) REFERENCES bundles(id)
        );

        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY,
            problem_id INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            duration_ms INTEGER,
            status TEXT NOT NULL,
            passed_count INTEGER NOT NULL DEFAULT 0,
            failed_count INTEGER NOT NULL DEFAULT 0,
            stdout TEXT NOT NULL DEFAULT '',
            stderr TEXT NOT NULL DEFAULT '',
            exit_code INTEGER,
            solution_hash TEXT NOT NULL,
            FOREIGN KEY(problem_id) REFERENCES problems(id)
        );

        CREATE TABLE IF NOT EXISTS auth_otps (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL,
            purpose TEXT NOT NULL DEFAULT 'login',
            code_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            attempts_remaining INTEGER NOT NULL,
            last_sent_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_auth_otps_email ON auth_otps(email);

        CREATE TABLE IF NOT EXISTS auth_sessions (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_auth_sessions_email ON auth_sessions(email);
        CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_hash ON auth_sessions(token_hash);

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            email_verified INTEGER NOT NULL DEFAULT 1,
            failed_login_count INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT
        );

        CREATE TABLE IF NOT EXISTS user_solutions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            problem_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, problem_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(problem_id) REFERENCES problems(id)
        );

        CREATE TABLE IF NOT EXISTS user_problem_stats (
            user_id INTEGER NOT NULL,
            problem_id INTEGER NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            last_status TEXT NOT NULL DEFAULT 'never',
            last_run TEXT,
            UNIQUE(user_id, problem_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(problem_id) REFERENCES problems(id)
        );
        """
    )

    otp_columns = {
        str(row["name"])
        for row in conn.execute("PRAGMA table_info(auth_otps)").fetchall()
    }
    if "purpose" not in otp_columns:
        conn.execute(
            "ALTER TABLE auth_otps ADD COLUMN purpose TEXT NOT NULL DEFAULT 'login'"
        )
    if "last_sent_at" not in otp_columns:
        conn.execute("ALTER TABLE auth_otps ADD COLUMN last_sent_at TEXT")
        conn.execute(
            "UPDATE auth_otps SET last_sent_at = created_at WHERE last_sent_at IS NULL"
        )
        conn.execute(
            "UPDATE auth_otps SET last_sent_at = ? WHERE last_sent_at IS NULL",
            (utc_now_iso(),),
        )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_auth_otps_email_purpose ON auth_otps(email, purpose)"
    )

    attempt_columns = {
        str(row["name"])
        for row in conn.execute("PRAGMA table_info(attempts)").fetchall()
    }
    if "user_id" not in attempt_columns:
        conn.execute("ALTER TABLE attempts ADD COLUMN user_id INTEGER")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_attempts_problem_id ON attempts(problem_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_attempts_user_problem ON attempts(user_id, problem_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_user_solutions_user_problem ON user_solutions(user_id, problem_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_user_problem_stats_user_problem ON user_problem_stats(user_id, problem_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_bundle_assets_bundle_id ON bundle_assets(bundle_id)"
    )

    problem_columns = {
        str(row["name"])
        for row in conn.execute("PRAGMA table_info(problems)").fetchall()
    }
    if "title" not in problem_columns:
        conn.execute("ALTER TABLE problems ADD COLUMN title TEXT NOT NULL DEFAULT ''")
    if "description" not in problem_columns:
        conn.execute("ALTER TABLE problems ADD COLUMN description TEXT NOT NULL DEFAULT ''")
    if "template_code" not in problem_columns:
        conn.execute("ALTER TABLE problems ADD COLUMN template_code TEXT NOT NULL DEFAULT ''")
    if "doctest" not in problem_columns:
        conn.execute("ALTER TABLE problems ADD COLUMN doctest TEXT NOT NULL DEFAULT ''")
    if "created_at" not in problem_columns:
        conn.execute("ALTER TABLE problems ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
        conn.execute(
            "UPDATE problems SET created_at = ? WHERE created_at = ''",
            (utc_now_iso(),),
        )

    _repair_empty_problem_templates(conn)
    conn.commit()


def get_bundle_by_hash(conn: sqlite3.Connection, snapshot_hash: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM bundles WHERE snapshot_hash = ?", (snapshot_hash,)
    ).fetchone()


def get_bundle_by_id(conn: sqlite3.Connection, bundle_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM bundles WHERE id = ?", (bundle_id,)).fetchone()


def insert_bundle(
    conn: sqlite3.Connection, name: str, source_root: str, snapshot_hash: str
) -> int:
    cur = conn.execute(
        """
        INSERT INTO bundles(name, source_root, snapshot_hash, imported_at)
        VALUES(?, ?, ?, ?)
        """,
        (name, source_root, snapshot_hash, utc_now_iso()),
    )
    conn.commit()
    return int(cur.lastrowid)


def upsert_problem(
    conn: sqlite3.Connection,
    *,
    bundle_id: int | None,
    slug: str,
    title: str,
    description: str,
    template_code: str,
    doctest: str,
    source_relpath: str,
    assets_manifest: list[str],
    content_hash: str,
) -> None:
    safe_template_code = template_code
    if not safe_template_code.strip():
        safe_template_code = _fallback_template_from_doctest(doctest)

    problem_columns = {
        str(row["name"])
        for row in conn.execute("PRAGMA table_info(problems)").fetchall()
    }
    has_legacy_prompt = "prompt_path" in problem_columns
    has_legacy_solution = "solution_path" in problem_columns

    insert_cols = [
        "bundle_id",
        "slug",
        "title",
        "description",
        "template_code",
        "doctest",
        "created_at",
        "source_relpath",
        "assets_manifest_json",
        "content_hash",
    ]
    values: list[Any] = [
        bundle_id,
        slug,
        title,
        description,
        safe_template_code,
        doctest,
        utc_now_iso(),
        source_relpath,
        json.dumps(assets_manifest),
        content_hash,
    ]
    update_assignments = [
        "bundle_id = excluded.bundle_id",
        "title = excluded.title",
        "description = excluded.description",
        "template_code = excluded.template_code",
        "doctest = excluded.doctest",
        "source_relpath = excluded.source_relpath",
        "assets_manifest_json = excluded.assets_manifest_json",
        "content_hash = excluded.content_hash",
    ]

    if has_legacy_prompt:
        compat_prompt_path = f"compat://prompt/{source_relpath or slug}"
        insert_cols.append("prompt_path")
        values.append(compat_prompt_path)
        update_assignments.append("prompt_path = excluded.prompt_path")
    if has_legacy_solution:
        compat_solution_path = f"compat://solution/{slug}.py"
        insert_cols.append("solution_path")
        values.append(compat_solution_path)
        update_assignments.append("solution_path = excluded.solution_path")

    columns_sql = ", ".join(insert_cols)
    placeholders_sql = ", ".join("?" for _ in insert_cols)
    updates_sql = ",\n            ".join(update_assignments)
    conn.execute(
        f"""
        INSERT INTO problems(
            {columns_sql}
        )
        VALUES({placeholders_sql})
        ON CONFLICT(slug) DO UPDATE SET
            {updates_sql}
        """,
        tuple(values),
    )
    conn.commit()


def get_problem(conn: sqlite3.Connection, problem_ref: str) -> sqlite3.Row | None:
    if problem_ref.isdigit():
        return conn.execute("SELECT * FROM problems WHERE id = ?", (int(problem_ref),)).fetchone()
    return conn.execute("SELECT * FROM problems WHERE slug = ?", (problem_ref,)).fetchone()


def list_problems(conn: sqlite3.Connection, *, user_id: int | None = None) -> list[sqlite3.Row]:
    if user_id is not None:
        rows = conn.execute(
            """
            SELECT
                p.id,
                p.slug,
                p.title,
                p.source_relpath,
                COALESCE(b.name, 'db') AS bundle_name,
                COALESCE(ups.attempts, 0) AS attempts,
                COALESCE(ups.last_status, 'never') AS last_status,
                ups.last_run AS last_run
            FROM problems p
            LEFT JOIN bundles b ON b.id = p.bundle_id
            LEFT JOIN user_problem_stats ups
                ON ups.problem_id = p.id AND ups.user_id = ?
            ORDER BY b.name ASC, p.slug ASC
            """,
            (user_id,),
        ).fetchall()
        return list(rows)

    rows = conn.execute(
        """
        SELECT
            p.id,
            p.slug,
            p.title,
            p.source_relpath,
            COALESCE(b.name, 'db') AS bundle_name,
            COUNT(a.id) AS attempts,
            COALESCE((
                SELECT a2.status
                FROM attempts a2
                WHERE a2.problem_id = p.id
                ORDER BY a2.id DESC
                LIMIT 1
            ), 'never') AS last_status,
            (
                SELECT a3.finished_at
                FROM attempts a3
                WHERE a3.problem_id = p.id
                ORDER BY a3.id DESC
                LIMIT 1
            ) AS last_run
        FROM problems p
        LEFT JOIN bundles b ON b.id = p.bundle_id
        LEFT JOIN attempts a ON a.problem_id = p.id
        GROUP BY p.id
        ORDER BY b.name ASC, p.slug ASC
        """
    ).fetchall()
    return list(rows)


def create_attempt(
    conn: sqlite3.Connection, problem_id: int, solution_hash: str, *, user_id: int | None = None
) -> int:
    cur = conn.execute(
        """
        INSERT INTO attempts(problem_id, started_at, status, solution_hash, user_id)
        VALUES(?, ?, 'error', ?, ?)
        """,
        (problem_id, utc_now_iso(), solution_hash, user_id),
    )
    conn.commit()
    return int(cur.lastrowid)


def finalize_attempt(
    conn: sqlite3.Connection,
    *,
    attempt_id: int,
    status: str,
    passed_count: int,
    failed_count: int,
    stdout: str,
    stderr: str,
    exit_code: int,
    duration_ms: int,
) -> None:
    conn.execute(
        """
        UPDATE attempts
        SET finished_at = ?, duration_ms = ?, status = ?,
            passed_count = ?, failed_count = ?, stdout = ?, stderr = ?, exit_code = ?
        WHERE id = ?
        """,
        (
            utc_now_iso(),
            duration_ms,
            status,
            passed_count,
            failed_count,
            stdout,
            stderr,
            exit_code,
            attempt_id,
        ),
    )
    conn.commit()


def problem_assets(problem_row: sqlite3.Row) -> list[str]:
    data = problem_row["assets_manifest_json"]
    if not data:
        return []
    parsed = json.loads(data)
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return []


def upsert_bundle_asset(
    conn: sqlite3.Connection, *, bundle_id: int, relpath: str, content: bytes
) -> None:
    conn.execute(
        """
        INSERT INTO bundle_assets(bundle_id, relpath, content)
        VALUES(?, ?, ?)
        ON CONFLICT(bundle_id, relpath) DO UPDATE SET
            content = excluded.content
        """,
        (bundle_id, relpath, content),
    )
    conn.commit()


def list_bundle_assets(conn: sqlite3.Connection, *, bundle_id: int) -> list[sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT relpath, content
        FROM bundle_assets
        WHERE bundle_id = ?
        ORDER BY relpath ASC
        """,
        (bundle_id,),
    ).fetchall()
    return list(rows)


def to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def get_user_by_email(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    return conn.execute("SELECT id, email FROM users WHERE email = ? LIMIT 1", (email,)).fetchone()


def get_user_solution(conn: sqlite3.Connection, *, user_id: int, problem_id: int) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT id, user_id, problem_id, content, updated_at
        FROM user_solutions
        WHERE user_id = ? AND problem_id = ?
        LIMIT 1
        """,
        (user_id, problem_id),
    ).fetchone()


def upsert_user_solution(
    conn: sqlite3.Connection, *, user_id: int, problem_id: int, content: str
) -> None:
    conn.execute(
        """
        INSERT INTO user_solutions(user_id, problem_id, content, updated_at)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(user_id, problem_id) DO UPDATE SET
            content = excluded.content,
            updated_at = excluded.updated_at
        """,
        (user_id, problem_id, content, utc_now_iso()),
    )
    conn.commit()


def ensure_user_solution(
    conn: sqlite3.Connection, *, user_id: int, problem_row: sqlite3.Row
) -> sqlite3.Row:
    problem_id = int(problem_row["id"])
    existing = get_user_solution(conn, user_id=user_id, problem_id=problem_id)
    if existing is not None:
        # Repair legacy broken rows that were initialized with blank content.
        if str(existing["content"] or "").strip():
            return existing
        repaired_content = _resolve_template_content(conn, problem_row)
        upsert_user_solution(
            conn,
            user_id=user_id,
            problem_id=problem_id,
            content=repaired_content,
        )
        repaired = get_user_solution(conn, user_id=user_id, problem_id=problem_id)
        if repaired is None:
            raise RuntimeError("Failed to repair blank user solution row")
        return repaired

    default_content = _resolve_template_content(conn, problem_row)
    upsert_user_solution(conn, user_id=user_id, problem_id=problem_id, content=default_content)
    ensured = get_user_solution(conn, user_id=user_id, problem_id=problem_id)
    if ensured is None:
        raise RuntimeError("Failed to initialize user solution row")
    return ensured


def _repair_empty_problem_templates(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT p.id, p.template_code, p.doctest, p.source_relpath, b.source_root
        FROM problems p
        LEFT JOIN bundles b ON b.id = p.bundle_id
        WHERE TRIM(COALESCE(p.template_code, '')) = ''
        """
    ).fetchall()
    if not rows:
        return

    for row in rows:
        source_root = str(row["source_root"] or "").strip()
        source_relpath = str(row["source_relpath"] or "").strip()
        source_template: str | None = None
        if source_root and source_relpath:
            source_path = Path(source_root) / source_relpath
            if source_path.exists() and source_path.is_file():
                try:
                    loaded = source_path.read_text(encoding="utf-8")
                except OSError:
                    loaded = ""
                if loaded.strip():
                    source_template = loaded

        replacement = source_template or _fallback_template_from_doctest(str(row["doctest"] or ""))
        conn.execute(
            "UPDATE problems SET template_code = ? WHERE id = ?",
            (replacement, int(row["id"])),
        )


def _fallback_template_from_doctest(doctest_text: str) -> str:
    if doctest_text.strip():
        return f"__doc__ = {doctest_text!r}\n"
    return "# Starter code unavailable for this problem.\n"


def _load_problem_source_template(conn: sqlite3.Connection, problem_row: sqlite3.Row) -> str | None:
    bundle_id = problem_row["bundle_id"]
    source_relpath = str(problem_row["source_relpath"] or "").strip()
    if bundle_id is None or not source_relpath:
        return None

    bundle = get_bundle_by_id(conn, int(bundle_id))
    if bundle is None:
        return None

    source_root = Path(str(bundle["source_root"]))
    source_path = source_root / source_relpath
    if not source_path.exists() or not source_path.is_file():
        return None

    try:
        content = source_path.read_text(encoding="utf-8")
    except OSError:
        return None
    return content if content.strip() else None


def _resolve_template_content(conn: sqlite3.Connection, problem_row: sqlite3.Row) -> str:
    template_code = str(problem_row["template_code"] or "")
    if template_code.strip():
        return template_code

    source_template = _load_problem_source_template(conn, problem_row)
    if source_template is not None:
        conn.execute(
            "UPDATE problems SET template_code = ? WHERE id = ?",
            (source_template, int(problem_row["id"])),
        )
        conn.commit()
        return source_template

    return _fallback_template_from_doctest(str(problem_row["doctest"] or ""))


def update_user_problem_stats_after_run(
    conn: sqlite3.Connection, *, user_id: int, problem_id: int, status: str
) -> None:
    now_iso = utc_now_iso()
    conn.execute(
        """
        INSERT INTO user_problem_stats(user_id, problem_id, attempts, last_status, last_run)
        VALUES(?, ?, 1, ?, ?)
        ON CONFLICT(user_id, problem_id) DO UPDATE SET
            attempts = user_problem_stats.attempts + 1,
            last_status = excluded.last_status,
            last_run = excluded.last_run
        """,
        (user_id, problem_id, status, now_iso),
    )
    conn.commit()


def ensure_cli_user(conn: sqlite3.Connection) -> int:
    email = "local-cli@practice.local"
    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO users(email, password_hash, created_at, email_verified)
        VALUES(?, ?, ?, 1)
        ON CONFLICT(email) DO NOTHING
        """,
        (email, "local-cli", now),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if row is None:
        raise RuntimeError("Failed to initialize local CLI user")
    return int(row["id"])
