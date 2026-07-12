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
                ticker_symbol TEXT NOT NULL UNIQUE,
                ticker_name TEXT NOT NULL UNIQUE,
                sources TEXT NOT NULL,
                created_at TEXT
            )
            """)


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

    def clear_all(self) -> None:
        with self.db.connect() as conn:
            conn.execute("DELETE FROM entries")


class TrackedTickerRow(TypedDict):
    id: int
    ticker_symbol: str
    ticker_name: str
    sources: str
    created_at: str


class TrackedTickerRepository:
    def __init__(self, db: Database):
        self.db = db

    def save(self, *, ticker_symbol: str, ticker_name: str, sources: str) -> bool:
        try:
            with self.db.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO tracked_tickers (ticker_symbol, ticker_name, sources, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        ticker_symbol,
                        ticker_name,
                        sources,
                        datetime.utcnow().isoformat(),
                    ),
                )
            return True
        except Exception:
            return False

    def remove(self, ticker: str) -> bool:
        try:
            with self.db.connect() as conn:
                cur = conn.execute(
                    """
                    DELETE FROM tracked_tickers
                    WHERE ticker = ?
                    """,
                    (ticker,),
                )
            return cur.rowcount > 0
        except Exception:
            return False

    def get_all(self) -> List[TrackedTickerRow]:
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, ticker_symbol, ticker_name, sources, created_at
                FROM tracked_tickers
                ORDER BY created_at DESC
                """
            )
            rows = cur.fetchall()

        return [self._to_dict(r) for r in rows]

    def get_by_ticker(self, ticker: str) -> Optional[TrackedTickerRow]:
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, ticker_symbol, ticker_name, sources, created_at
                FROM tracked_tickers
                WHERE ticker = ?
                """,
                (ticker,),
            )
            row = cur.fetchone()

        return self._to_dict(row) if row else None

    def _to_dict(self, row: list) -> TrackedTickerRow:
        return {
            "id": row[0],
            "ticker_symbol": row[1],
            "ticker_name": row[2],
            "sources": row[3],
            "created_at": row[4],
        }
