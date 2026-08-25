import sqlite3
from contextlib import closing

from config import DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resumes (
                chat_id INTEGER PRIMARY KEY,
                resume_text TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def save_resume(chat_id: int, resume_text: str) -> None:
    with closing(get_conn()) as conn, conn:
        conn.execute(
            """
            INSERT INTO resumes (chat_id, resume_text, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(chat_id) DO UPDATE SET
                resume_text = excluded.resume_text,
                updated_at = excluded.updated_at
            """,
            (chat_id, resume_text),
        )


def get_resume(chat_id: int) -> str | None:
    with closing(get_conn()) as conn:
        row = conn.execute(
            "SELECT resume_text FROM resumes WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return row["resume_text"] if row else None
