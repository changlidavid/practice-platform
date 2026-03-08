from __future__ import annotations

import sqlite3

from . import db


def list_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return db.list_problems(conn)
