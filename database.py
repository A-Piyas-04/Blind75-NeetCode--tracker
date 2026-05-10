"""database.py — SQLite persistence layer for NeonCode Recall."""
from __future__ import annotations

import os
import sys
import sqlite3
from datetime import datetime

# When running as a PyInstaller .exe, __file__ points to a temporary extraction
# folder that changes every launch. sys.executable always points to the .exe
# itself, so placing the DB next to it gives stable, persistent storage.
if getattr(sys, "frozen", False):
    _base = os.path.dirname(sys.executable)
else:
    _base = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(_base, "neetcode_flashcards.db")


# ── Connection ────────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ── Schema ────────────────────────────────────────────────────────────────────

def create_tables() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS problems (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT    NOT NULL,
                difficulty     TEXT    NOT NULL,
                topic          TEXT,
                link           TEXT,
                notes          TEXT,
                practice_count INTEGER DEFAULT 0,
                last_practiced TEXT,
                created_at     TEXT,
                updated_at     TEXT
            )
        """)
        conn.commit()


# ── Write operations ──────────────────────────────────────────────────────────

def add_problem(
    name: str,
    difficulty: str,
    topic: str,
    link: str = "",
    notes: str = "",
) -> None:
    ts = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO problems
                (name, difficulty, topic, link, notes, practice_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (name, difficulty, topic, link, notes, ts, ts),
        )
        conn.commit()


def update_problem(
    problem_id: int,
    name: str,
    difficulty: str,
    topic: str,
    link: str,
    notes: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE problems
            SET name=?, difficulty=?, topic=?, link=?, notes=?, updated_at=?
            WHERE id=?
            """,
            (name, difficulty, topic, link, notes, _now(), problem_id),
        )
        conn.commit()


def update_notes(problem_id: int, notes: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE problems SET notes=?, updated_at=? WHERE id=?",
            (notes, _now(), problem_id),
        )
        conn.commit()


def delete_problem(problem_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM problems WHERE id=?", (problem_id,))
        conn.commit()


def mark_as_practiced(problem_id: int) -> None:
    ts = _now()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE problems
            SET practice_count = practice_count + 1,
                last_practiced = ?,
                updated_at     = ?
            WHERE id = ?
            """,
            (ts, ts, problem_id),
        )
        conn.commit()


# ── Read operations ───────────────────────────────────────────────────────────

def get_all_problems(
    search: str = "",
    difficulty: str = "All",
    topic: str = "All",
) -> list:
    query = "SELECT * FROM problems WHERE 1=1"
    params: list = []
    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")
    if difficulty and difficulty != "All":
        query += " AND difficulty = ?"
        params.append(difficulty)
    if topic and topic != "All":
        query += " AND topic = ?"
        params.append(topic)
    query += " ORDER BY created_at DESC"
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_problem_by_id(problem_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM problems WHERE id = ?", (problem_id,)
        ).fetchone()
    return dict(row) if row else None


def get_random_problem(difficulty: str = "All", topic: str = "All") -> dict | None:
    query = "SELECT * FROM problems WHERE 1=1"
    params: list = []
    if difficulty and difficulty != "All":
        query += " AND difficulty = ?"
        params.append(difficulty)
    if topic and topic != "All":
        query += " AND topic = ?"
        params.append(topic)
    query += " ORDER BY RANDOM() LIMIT 1"
    with _connect() as conn:
        row = conn.execute(query, params).fetchone()
    return dict(row) if row else None


def get_stats() -> dict:
    with _connect() as conn:
        total  = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
        easy   = conn.execute("SELECT COUNT(*) FROM problems WHERE difficulty='Easy'").fetchone()[0]
        medium = conn.execute("SELECT COUNT(*) FROM problems WHERE difficulty='Medium'").fetchone()[0]
        hard   = conn.execute("SELECT COUNT(*) FROM problems WHERE difficulty='Hard'").fetchone()[0]
        recent = conn.execute(
            """
            SELECT * FROM problems
            WHERE last_practiced IS NOT NULL
            ORDER BY last_practiced DESC
            LIMIT 5
            """
        ).fetchall()
    return {
        "total":  total,
        "easy":   easy,
        "medium": medium,
        "hard":   hard,
        "recent": [dict(r) for r in recent],
    }
