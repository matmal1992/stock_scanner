import logging
from typing import Any, TypedDict

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
    justification: str
    skipped: int


class LLMResponse(TypedDict):
    forecast: str | None
    justification: str | None


class EntryRepository:
    def __init__(self, db: Database):
        self.db = db

    def save(self, entry: NewsEntry) -> bool:
        try:
            with self.db.connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO entries (
                        source_type, ticker, title, link, published, llm, justification, skipped
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry["source_type"],
                        entry["ticker"],
                        entry["title"],
                        entry["link"],
                        entry["published"],
                        entry["llm"],
                        entry["justification"],
                        entry["skipped"],
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
                SELECT id, title, link, published, source_type, ticker, llm, justification, skipped
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
                SELECT id, title, link, published, source_type, ticker, llm, justification, skipped
                FROM entries
                WHERE skipped = 0
                ORDER BY published DESC
                """
            )
            rows = cur.fetchall()

        return [self._to_dict(r) for r in rows]

    def update_llm(self, entry_id: int, response: LLMResponse) -> bool:
        forecast = response["forecast"]
        justification = response["justification"]

        if not forecast:
            logger.warning("Nie znaleziono prognozy w odpowiedzi LLM dla entry %s", entry_id)
        try:
            with self.db.connect() as conn:
                cur = conn.execute(
                    """
                    UPDATE entries
                    SET 
                        llm = ?,
                        justification = ?
                    WHERE id = ?
                    """,
                    (
                        forecast,
                        justification,
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
            "justification": row[7],
            "skipped": row[8],
        }

    def clear_all(self) -> None:
        with self.db.connect() as conn:
            conn.execute("DELETE FROM entries")

    def get_last_pending(self) -> NewsEntry | None:
        with self.db.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, title, link, published, source_type, ticker, llm, justification, skipped
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
