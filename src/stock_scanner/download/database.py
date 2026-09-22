import logging
import sqlite3

from src.stock_scanner.core.paths import get_data_dir

logger = logging.getLogger(__name__)


class Database:
    def __init__(self) -> None:
        self.db_path = get_data_dir() / "database.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Database path: %s", self.db_path)

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, timeout=10)

    def init_db(self) -> None:
        with self.connect() as conn:
            cur = conn.cursor()

            cur.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT,
                ticker TEXT,
                title TEXT,
                link TEXT UNIQUE,
                published TEXT,
                llm TEXT DEFAULT 'pending',
                justification TEXT DEFAULT '-',
                skipped INTEGER NOT NULL DEFAULT 0 CHECK (skipped IN (0, 1))
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
