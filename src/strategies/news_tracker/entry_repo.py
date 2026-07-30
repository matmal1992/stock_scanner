import logging
from datetime import datetime
from typing import Any, Optional, Sequence, TypedDict

from src.download.database import Database

logger = logging.getLogger(__name__)


class NewsEntry(TypedDict):
    title: str
    link: str
    published: int | None
    source_type: str


class NewsRow(TypedDict):
    id: int
    title: str
    link: str
    published: int | None
    source_type: str


class NewsFormatter:
    @staticmethod
    def format(rows: Sequence[NewsRow]) -> list[tuple[str, int]]:
        result: list[tuple[str, int]] = []

        for row in rows:
            entry_id = row["id"]
            title = row["title"]
            published = row["published"]
            source_type = row["source_type"]

            prefix = f"[{source_type.upper()}]"

            if published is not None:
                dt = datetime.fromtimestamp(float(published))
                time_str = dt.strftime("%d %b %H:%M")
                text = f"{time_str} {prefix} {title}"
            else:
                text = f"{prefix} {title}"

            result.append((text, entry_id))

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
                        source_type, title, link, published,
                        query, inserted_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry["source_type"],
                        entry["title"],
                        entry["link"],
                        entry["published"],
                        None,
                        datetime.utcnow().isoformat(),
                    ),
                )
            return True
        except Exception:
            logger.exception("Save failed")
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

    def get_latest_with_id(self, source_type: str, limit: int = 5) -> list[NewsRow]:
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
                SELECT id, title, link, published, source_type
                FROM entries
                ORDER BY published DESC
                """
            )
            rows = cur.fetchall()

        return [self._to_dict(r) for r in rows]

    def update_sentiment(self, entry_id: int, sentiment: str) -> bool:
        try:
            with self.db.connect() as conn:
                cur = conn.execute(
                    """
                    UPDATE entries
                    SET sentiment = ?, processed_at = ?
                    WHERE id = ?
                    """,
                    (
                        sentiment,
                        datetime.utcnow().isoformat(),
                        entry_id,
                    ),
                )

            return cur.rowcount > 0

        except Exception:
            return False

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
