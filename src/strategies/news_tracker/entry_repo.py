import logging
from typing import Any, Optional, Sequence, TypedDict

from src.download.database import Database

logger = logging.getLogger(__name__)


class NewsEntry(TypedDict):
    title: str
    link: str
    published: str | None
    source_type: str
    llm: str
    sentiment: str


class NewsRow(TypedDict):
    id: int
    title: str
    link: str
    published: str | None
    source_type: str
    llm: str
    sentiment: str


class NewsFormatter:
    @staticmethod
    def format(rows: Sequence[NewsRow]) -> list[tuple[dict, int]]:
        result: list[tuple[dict, int]] = []

        for row in rows:
            formatted = {
                "published": str(row["published"]),
                "type": str(row["source_type"]),
                "title": row["title"][:100],
                "llm": str(row["llm"]),
                "sentiment": str(row["sentiment"]),
            }

            result.append((formatted, row["id"]))

        return result


class EntryRepository:
    def __init__(self, db: Database):
        self.db = db

    def save(self, entry: NewsEntry) -> bool:
        try:
            with self.db.connect() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO entries (
                        source_type, title, link, published, llm, sentiment
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry["source_type"],
                        entry["title"],
                        entry["link"],
                        entry["published"],
                        entry["llm"],
                        entry["sentiment"],
                    ),
                )
            return True
        except Exception:
            logger.exception("Save failed")
            return False

    def get_latest_with_id(self, source_type: str) -> list[NewsRow]:
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, title, link, published, source_type, llm, sentiment
                FROM entries
                WHERE source_type = ?
                ORDER BY published DESC
                LIMIT ?
                """,
                (source_type, 5),
            )
            rows = cur.fetchall()

        return [self._to_dict(r) for r in rows]

    def get_link_by_id(self, entry_id: int) -> Optional[str]:
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

    def get_all_entries(self) -> list[NewsRow]:
        with self.db.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, title, link, published, source_type, llm, sentiment
                FROM entries
                ORDER BY published DESC
                """
            )
            rows = cur.fetchall()

        return [self._to_dict(r) for r in rows]

    def update_llm(self, entry_id: int, response: str) -> bool:
        try:
            with self.db.connect() as conn:
                cur = conn.execute(
                    """
                    UPDATE entries
                    SET llm = ?
                    WHERE id = ?
                    """,
                    (
                        self._extract_forecast(response),
                        entry_id,
                    ),
                )

            return cur.rowcount > 0

        except Exception as e:
            print("DB ERROR:", e)
            return False

    def _extract_forecast(self, text: str) -> str:
        return text.split("Prognoza: ", 1)[1].strip() if "Prognoza: " in text else ""

    def _to_dict(self, row: list[Any]) -> NewsRow:
        return {
            "id": row[0],
            "title": row[1],
            "link": row[2],
            "published": row[3],
            "source_type": row[4],
            "llm": row[5],
            "sentiment": row[6],
        }

    def clear_all(self) -> None:
        with self.db.connect() as conn:
            conn.execute("DELETE FROM entries")

    def get_last_pending(self) -> NewsRow | None:
        with self.db.connect() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, title, link, published, source_type, llm, sentiment
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
