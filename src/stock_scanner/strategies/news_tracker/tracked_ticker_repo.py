import logging
from datetime import datetime
from typing import List, Optional, TypedDict

from src.stock_scanner.download.database import Database

logger = logging.getLogger(__name__)


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
            logger.exception("Save failed")
            return False

    def remove(self, ticker: str) -> bool:
        try:
            with self.db.connect() as conn:
                cur = conn.execute(
                    """
                    DELETE FROM tracked_tickers
                    WHERE ticker_symbol = ?
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
                WHERE ticker_symbol = ?
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

    def get_tickers_with_sources(self) -> List[dict]:
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ticker_name, sources
                FROM tracked_tickers
                """
            )
            rows = cur.fetchall()

        result = []
        for name, sources in rows:
            result.append({"name": name, "sources": [s.strip() for s in sources.split(",")]})

        return result
