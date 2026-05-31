import sqlite3
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

DB_PATH = "bot.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                channel_name TEXT,
                active INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                post_id INTEGER NOT NULL,
                responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)


# ---------- channels ----------

def add_channel(channel_id: str, channel_name: str = ""):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO channels (channel_id, channel_name, active) VALUES (?, ?, 1)",
            (str(channel_id), channel_name),
        )


def remove_channel(channel_id: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE channels SET active = 0 WHERE channel_id = ?",
            (str(channel_id),),
        )


def get_active_channels() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT channel_id FROM channels WHERE active = 1"
        ).fetchall()
    return [r["channel_id"] for r in rows]


def get_all_channels() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT channel_id, channel_name, active FROM channels ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


# ---------- cooldown ----------

def is_on_cooldown(channel_id: str, cooldown_minutes: int) -> bool:
    since = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM responses WHERE channel_id = ? AND responded_at > ? LIMIT 1",
            (str(channel_id), since.strftime("%Y-%m-%d %H:%M:%S")),
        ).fetchone()
    return row is not None


def record_response(channel_id: str, post_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO responses (channel_id, post_id) VALUES (?, ?)",
            (str(channel_id), post_id),
        )


# ---------- settings ----------

def get_setting(key: str, default: str = "") -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
