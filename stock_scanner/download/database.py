import sqlite3
import sys
from datetime import datetime
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent.parent
else:
    BASE_DIR = Path(__file__).parent.parent.parent

DB_PATH = BASE_DIR / "data" / "rss.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id TEXT PRIMARY KEY,
        title TEXT,
        link TEXT,
        published INTEGER,

        llm_status TEXT DEFAULT 'pending',
        sentiment TEXT,
        processed_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def parse_rss_date(date_str: str) -> int | None:
    try:
        dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        return int(dt.timestamp())
    except Exception:
        return None


def insert_entry(entry: object) -> bool:
    conn = get_connection()
    cur = conn.cursor()

    try:
        entry_id = getattr(entry, "id", getattr(entry, "link", None))
        if not entry_id:
            return False

        published_str = getattr(entry, "published", "")
        published_ts = parse_rss_date(published_str)

        cur.execute(
            """
        INSERT INTO entries (id, title, link, published)
        VALUES (?, ?, ?, ?)
        """,
            (
                entry_id,
                getattr(entry, "title", "Brak tytułu"),
                getattr(entry, "link", ""),
                published_ts,
            ),
        )

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        # duplikat → ignorujemy
        return False

    finally:
        conn.close()


def get_all_entries() -> list[tuple[str, str, str]]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT title, link, published FROM entries ORDER BY published DESC")

    rows = cur.fetchall()
    conn.close()

    return rows


def get_pending_entries(limit: int = 10) -> list[tuple[str, str]]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
    SELECT id, title FROM entries
    WHERE llm_status = 'pending'
    LIMIT ?
    """,
        (limit,),
    )

    rows = cur.fetchall()
    conn.close()

    return rows


def update_sentiment(entry_id: str, sentiment: str) -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
    UPDATE entries
    SET sentiment = ?, llm_status = 'done', processed_at = ?
    WHERE id = ?
    """,
        (sentiment, datetime.utcnow().isoformat(), entry_id),
    )

    conn.commit()
    conn.close()
