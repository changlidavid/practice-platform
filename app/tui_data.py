from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class ProblemRow:
    problem_id: int
    bundle_name: str
    slug: str
    attempts: int
    last_status: str
    last_time_ms: int | None
    updated_at: str | None


@dataclass(frozen=True)
class AttemptRow:
    attempt_id: int
    started_at: str
    finished_at: str | None
    status: str
    duration_ms: int | None
    passed_count: int
    failed_count: int


def fetch_bundle_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT DISTINCT name FROM bundles ORDER BY name ASC").fetchall()
    return [str(row["name"]) for row in rows]


def fetch_problem_rows(
    conn: sqlite3.Connection,
    *,
    search: str = "",
    solved_filter: str = "all",
    bundle_filter: str = "all",
) -> list[ProblemRow]:
    sql = """
    SELECT *
    FROM (
        SELECT
            p.id AS problem_id,
            b.name AS bundle_name,
            p.slug AS slug,
            (SELECT COUNT(*) FROM attempts a WHERE a.problem_id = p.id) AS attempts,
            COALESCE((
                SELECT a2.status
                FROM attempts a2
                WHERE a2.problem_id = p.id
                ORDER BY a2.id DESC
                LIMIT 1
            ), 'never') AS last_status,
            (
                SELECT a3.duration_ms
                FROM attempts a3
                WHERE a3.problem_id = p.id
                ORDER BY a3.id DESC
                LIMIT 1
            ) AS last_time_ms,
            (
                SELECT a4.finished_at
                FROM attempts a4
                WHERE a4.problem_id = p.id
                ORDER BY a4.id DESC
                LIMIT 1
            ) AS updated_at
        FROM problems p
        JOIN bundles b ON b.id = p.bundle_id
    ) t
    WHERE 1=1
    """
    params: list[object] = []

    if search.strip():
        sql += " AND lower(t.slug) LIKE ?"
        params.append(f"%{search.strip().lower()}%")

    if bundle_filter != "all":
        sql += " AND t.bundle_name = ?"
        params.append(bundle_filter)

    if solved_filter == "solved":
        sql += " AND t.last_status = 'pass'"
    elif solved_filter == "unsolved":
        sql += " AND t.last_status != 'pass'"

    sql += " ORDER BY t.bundle_name ASC, t.slug ASC"

    rows = conn.execute(sql, params).fetchall()
    return [
        ProblemRow(
            problem_id=int(row["problem_id"]),
            bundle_name=str(row["bundle_name"]),
            slug=str(row["slug"]),
            attempts=int(row["attempts"]),
            last_status=str(row["last_status"]),
            last_time_ms=row["last_time_ms"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


def fetch_attempt_history(conn: sqlite3.Connection, problem_id: int, limit: int = 30) -> list[AttemptRow]:
    rows = conn.execute(
        """
        SELECT
            id,
            started_at,
            finished_at,
            status,
            duration_ms,
            passed_count,
            failed_count
        FROM attempts
        WHERE problem_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (problem_id, limit),
    ).fetchall()
    return [
        AttemptRow(
            attempt_id=int(row["id"]),
            started_at=str(row["started_at"]),
            finished_at=row["finished_at"],
            status=str(row["status"]),
            duration_ms=row["duration_ms"],
            passed_count=int(row["passed_count"]),
            failed_count=int(row["failed_count"]),
        )
        for row in rows
    ]
