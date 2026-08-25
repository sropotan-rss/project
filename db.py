import sqlite3
from contextlib import closing

from config import DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with closing(get_conn()) as conn, conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS price_watches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                selector TEXT NOT NULL,
                last_price TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mention_watches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_mentions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watch_id INTEGER NOT NULL REFERENCES mention_watches(id) ON DELETE CASCADE,
                link TEXT NOT NULL,
                seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(watch_id, link)
            )
            """
        )


# --- price watches ---------------------------------------------------------

def add_price_watch(chat_id: int, name: str, url: str, selector: str) -> int:
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO price_watches (chat_id, name, url, selector) VALUES (?, ?, ?, ?)",
            (chat_id, name, url, selector),
        )
        return cur.lastrowid


def update_price(watch_id: int, price_text: str) -> None:
    with closing(get_conn()) as conn, conn:
        conn.execute(
            "UPDATE price_watches SET last_price = ? WHERE id = ?",
            (price_text, watch_id),
        )


def list_price_watches(chat_id: int) -> list[dict]:
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT * FROM price_watches WHERE chat_id = ? ORDER BY id", (chat_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def all_price_watches() -> list[dict]:
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT * FROM price_watches ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def remove_price_watch(chat_id: int, watch_id: int) -> bool:
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "DELETE FROM price_watches WHERE id = ? AND chat_id = ?",
            (watch_id, chat_id),
        )
        return cur.rowcount > 0


# --- mention watches ---------------------------------------------------------

def add_mention_watch(chat_id: int, keyword: str) -> int:
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO mention_watches (chat_id, keyword) VALUES (?, ?)",
            (chat_id, keyword),
        )
        return cur.lastrowid


def list_mention_watches(chat_id: int) -> list[dict]:
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT * FROM mention_watches WHERE chat_id = ? ORDER BY id", (chat_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def all_mention_watches() -> list[dict]:
    with closing(get_conn()) as conn:
        rows = conn.execute("SELECT * FROM mention_watches ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def remove_mention_watch(chat_id: int, watch_id: int) -> bool:
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "DELETE FROM mention_watches WHERE id = ? AND chat_id = ?",
            (watch_id, chat_id),
        )
        return cur.rowcount > 0


def mark_seen_if_new(watch_id: int, link: str) -> bool:
    """Records a mention link as seen. Returns True if it was not seen before."""
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO seen_mentions (watch_id, link) VALUES (?, ?)",
            (watch_id, link),
        )
        return cur.rowcount > 0
