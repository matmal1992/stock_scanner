import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Protocol, TypedDict

logger = logging.getLogger(__name__)

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent.parent
else:
    BASE_DIR = Path(__file__).parent.parent.parent

DB_PATH = BASE_DIR / "data" / "database.db"


class FeedEntry(Protocol):
    id: str | None
    link: str
    title: str
    published_parsed: tuple[int, int, int, int, int, int] | None


class NewsRow(TypedDict):
    id: str
    title: str
    link: str
    published: int | None
    source_type: str


class Database:
    def __init__(self) -> None:
        self.db_path = DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def connect(self) -> sqlite3.Connection:
        return self._connect()

    def init_db(self) -> None:
        with self._connect() as conn:
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

            cur.execute("""
            CREATE TABLE IF NOT EXISTS tracked_tickers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL UNIQUE,
                sources TEXT NOT NULL,
                created_at TEXT
            )
            """)

    def insert_entry(self, entry: FeedEntry, source_type: str, query: Optional[str] = None) -> bool:
        entry_id = entry.id or entry.link
        if not entry_id:
            return False

        published_ts = None
        if entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6])
            published_ts = int(dt.timestamp())

        return self.insert_entry_raw(
            entry_id=entry_id,
            title=entry.title,
            link=entry.link,
            published=published_ts,
            source_type=source_type,
            query=query,
        )

    def insert_entry_raw(
        self,
        *,
        entry_id: str,
        title: str,
        link: str,
        published: int | None,
        source_type: str,
        query: Optional[str] = None,
    ) -> bool:
        try:
            with self._connect() as conn:
                conn.execute(
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
                        published,
                        query,
                        datetime.utcnow().isoformat(),
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_latest_entries(self, limit_per_source: int = 5) -> list[tuple]:
        with self._connect() as conn:
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
            rss = cur.fetchall()

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
            google = cur.fetchall()

        return rss + google

    def get_latest_entries_with_id(self, amount: int = 5) -> List[NewsRow]:
        with self._connect() as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT id, title, link, published, source_type
                FROM entries
                WHERE source_type = 'rss'
                ORDER BY published DESC
                LIMIT ?
            """,
                (amount,),
            )
            rss = cur.fetchall()

            cur.execute(
                """
                SELECT id, title, link, published, source_type
                FROM entries
                WHERE source_type = 'google'
                ORDER BY published DESC
                LIMIT ?
            """,
                (amount,),
            )
            google = cur.fetchall()

        return [self._to_dict(r) for r in (rss + google)]

    def get_entry_link_by_id(self, entry_id: str) -> Optional[str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT link FROM entries WHERE id = ?", (entry_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def get_first_entry_link(self) -> str:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT link FROM entries
                ORDER BY published DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            return row[0] if row else "Latest entry link: N/A"

    @staticmethod
    def _to_dict(row: list[Any]) -> NewsRow:
        return {
            "id": row[0],
            "title": row[1],
            "link": row[2],
            "published": row[3],
            "source_type": row[4],
        }


class EntryRepository:
    def __init__(self, db: Database):
        self.db = db

    def save(
        self,
        *,
        entry_id: str,
        title: str,
        link: str,
        published: int | None,
        source_type: str,
        query: Optional[str] = None,
    ) -> bool:
        try:
            with self.db.connect() as conn:
                conn.execute(
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
                        published,
                        query,
                        datetime.utcnow().isoformat(),
                    ),
                )
            return True
        except Exception:
            return False

    def get_latest(self, source_type: str, limit: int = 5) -> list[tuple]:
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT title, link, published, source_type
                FROM entries
                WHERE source_type = ?
                ORDER BY published DESC
                LIMIT ?
                """,
                (source_type, limit),
            )
            return cur.fetchall()

    def get_latest_with_id(self, source_type: str, limit: int = 5) -> List[NewsRow]:
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, title, link, published, source_type
                FROM entries
                WHERE source_type = ?
                ORDER BY published DESC
                LIMIT ?
                """,
                (source_type, limit),
            )
            rows = cur.fetchall()

        return [self._to_dict(r) for r in rows]

    def get_link_by_id(self, entry_id: str) -> Optional[str]:
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT link FROM entries WHERE id = ?", (entry_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def get_latest_link(self) -> Optional[str]:
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT link FROM entries
                ORDER BY published DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            return row[0] if row else None

    def _to_dict(self, row: list[Any]) -> NewsRow:
        return {
            "id": row[0],
            "title": row[1],
            "link": row[2],
            "published": row[3],
            "source_type": row[4],
        }
