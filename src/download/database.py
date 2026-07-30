import logging
import sqlite3
import sys
from pathlib import Path
from typing import Protocol

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


class Database:
    def __init__(self) -> None:
        self.db_path = DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def init_db(self) -> None:
        with self.connect() as conn:
            cur = conn.cursor()

            cur.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT,
                title TEXT,
                link TEXT UNIQUE,
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
