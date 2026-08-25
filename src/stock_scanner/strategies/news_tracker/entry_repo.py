import logging
from typing import Any, Literal, TypedDict

from src.stock_scanner.download.database import Database

logger = logging.getLogger(__name__)


class NewsEntry(TypedDict):
    id: int
    title: str
    link: str
    published: str | None
    source_type: str
    ticker: str | None
    llm: str
    sentiment: str


class LLMResponse(TypedDict):
    relevant: bool
    company: str | None
    ticker: str | None
    forecast: str | None
    sector: Literal[
        "zbrojeniowy",
        "dronowy",
        "medyczny",
        "hi-tech",
        "kosmiczny",
        "other",
    ]


class EntryRepository:
    def __init__(self, db: Database):
        self.db = db

    def save(self, entry: NewsEntry) -> bool:
        try:
            with self.db.connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO entries (
                        source_type, ticker, title, link, published, llm, sentiment
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry["source_type"],
                        entry["ticker"],
                        entry["title"],
                        entry["link"],
                        entry["published"],
                        entry["llm"],
                        entry["sentiment"],
                    ),
                )
                return cursor.rowcount > 0
        except Exception:
            logger.exception("Save failed")
            return False

    def get_by_id(self, entry_id: int) -> NewsEntry | None:
        with self.db.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, title, link, published, source_type, ticker, llm, sentiment
                FROM entries
                WHERE id = ?
                """,
                (entry_id,),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return self._to_dict(row)

    def get_all_entries(self) -> list[NewsEntry]:
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, title, link, published, source_type, ticker, llm, sentiment
                FROM entries
                ORDER BY published DESC
                """
            )
            rows = cur.fetchall()

        return [self._to_dict(r) for r in rows]

    def update_llm(self, entry_id: int, response: LLMResponse) -> bool:
        ticker = response["ticker"]
        forecast = response["forecast"]

        if not ticker:
            logger.warning("Nie znaleziono tickera w odpowiedzi LLM dla entry %s", entry_id)

        if not forecast:
            logger.warning("Nie znaleziono prognozy w odpowiedzi LLM dla entry %s", entry_id)
        try:
            with self.db.connect() as conn:
                cur = conn.execute(
                    """
                    UPDATE entries
                    SET 
                        ticker = ?,
                        llm = ?
                    WHERE id = ?
                    """,
                    (
                        ticker,
                        forecast,
                        entry_id,
                    ),
                )

            return cur.rowcount > 0

        except Exception as e:
            logger.exception("DB ERROR:", e)
            return False

    def _to_dict(self, row: list[Any]) -> NewsEntry:
        return {
            "id": row[0],
            "title": row[1],
            "link": row[2],
            "published": row[3],
            "source_type": row[4],
            "ticker": row[5],
            "llm": row[6],
            "sentiment": row[7],
        }

    def clear_all(self) -> None:
        with self.db.connect() as conn:
            conn.execute("DELETE FROM entries")

    def get_last_pending(self) -> NewsEntry | None:
        with self.db.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, title, link, published, source_type, ticker, llm, sentiment
                FROM entries
                WHERE llm = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                ("pending",),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return self._to_dict(row)
