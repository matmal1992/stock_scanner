import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent.parent
else:
    BASE_DIR = Path(__file__).parent.parent.parent

DB_PATH = BASE_DIR / "data" / "database.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class FeedEntry(Protocol):
    id: str | None
    link: str
    title: str
    published_parsed: tuple[int, int, int, int, int, int] | None


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id TEXT PRIMARY KEY,
        source_type TEXT,

        title TEXT,
        link TEXT,
        published INTEGER,

        query TEXT,
        inserted_at TEXT,

        llm_status TEXT DEFAULT 'pending',
        sentiment TEXT,
        processed_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_entry(entry: FeedEntry, source_type: str, query: str | None = None) -> bool:
    conn = get_connection()
    cur = conn.cursor()

    try:
        entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
        if not entry_id:
            return False

        title = getattr(entry, "title", "")
        link = getattr(entry, "link", "")

        published_ts = None
        published_parsed = getattr(entry, "published_parsed", None)

        if published_parsed is not None:
            dt = datetime(*published_parsed[:6])
            published_ts = int(dt.timestamp())

        cur.execute(
            """
            INSERT INTO entries (
                id, source_type, title, link, published,
                query, inserted_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                source_type,
                title,
                link,
                published_ts,
                query,
                datetime.utcnow().isoformat(),
            ),
        )

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def get_latest_entries(limit_per_source: int = 5) -> list[tuple[str, str, int | None, str, str]]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT title, link, published, source_type
        FROM entries
        WHERE source_type = 'rss'
        ORDER BY published DESC
        LIMIT ?
    """,
        (limit_per_source,),
    )
    rss_rows = cur.fetchall()

    cur.execute(
        """
        SELECT title, link, published, source_type
        FROM entries
        WHERE source_type = 'google'
        ORDER BY published DESC
        LIMIT ?
    """,
        (limit_per_source,),
    )
    google_rows = cur.fetchall()

    conn.close()

    return rss_rows + google_rows


def get_first_entry_link() -> str | None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT link
        FROM entries
        ORDER BY published DESC
        LIMIT 1
        """
    )

    row = cur.fetchone()
    conn.close()

    if row:
        return row[0]

    return None
