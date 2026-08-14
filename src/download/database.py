import sqlite3
from typing import Protocol

from src.core.paths import get_data_dir


class FeedEntry(Protocol):
    id: str | None
    link: str
    title: str


class Database:
    def __init__(self) -> None:
        self.db_path = get_data_dir() / "database.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, timeout=10)

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")

            cur = conn.cursor()

            cur.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT,
                title TEXT,
                link TEXT UNIQUE,
                published TEXT,
                llm TEXT DEFAULT 'pending',
                sentiment TEXT DEFAULT '-'
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
