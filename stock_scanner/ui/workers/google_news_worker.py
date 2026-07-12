import calendar
import email.utils
import logging
from datetime import timezone
from typing import Any

import feedparser
from feedparser import FeedParserDict
from PySide6.QtCore import QObject, Signal

from stock_scanner.download.database import EntryRepository, TrackedTickerRepository

logger = logging.getLogger(__name__)


class GoogleNewsWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    data_ready = Signal(list, bool)

    def __init__(self, entry_repo: EntryRepository, tracked_repo: TrackedTickerRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.tracked_repo = tracked_repo

    def run(self) -> None:
        try:
            tickers = self.tracked_repo.get_tickers_with_sources()

            if not tickers:
                self.error.emit("Brak tickerów do wyszukania")
                self.finished.emit()
                return

            self.log.emit("Pobieranie Google News...")

            found_new = False

            for ticker in tickers:
                if self._process_ticker(ticker):
                    found_new = True

            entries = self.entry_repo.get_latest("google")
            self.data_ready.emit(entries, found_new)
            self.finished.emit()

        except Exception as e:
            self.error.emit(f"Google worker error: {e}")
            self.finished.emit()

    def _process_ticker(self, ticker: dict) -> bool:
        name = ticker["name"]
        sources = ticker["sources"]

        query = self._build_query(name, sources)
        self.log.emit(f"Szukam: {name}")

        feed = self._fetch_feed(query)

        if not feed.entries:
            self.log.emit(f"Brak wyników dla: {name}")
            return False

        return self._process_entries(feed.entries, query, name)

    def _build_query(self, name: str, sources: list[str]) -> str:
        sources_query = " OR ".join(f"site:{s}" for s in sources)
        return f'"{name}" ({sources_query})'

    def _fetch_feed(self, query: str) -> FeedParserDict:
        url = "https://news.google.com/rss/search?" f"q={query.replace(' ', '+')}" "&hl=pl&gl=PL&ceid=PL:pl"

        return feedparser.parse(url)

    def _process_entries(self, entries: list[Any], query: str, name: str) -> bool:
        found_new = False

        for index, entry in enumerate(entries[:10]):
            try:
                entry_id = (
                    getattr(entry, "id", None) or getattr(entry, "link", None) or f"google-{name}-{index}"
                )

                published_ts = self._parse_published_ts(entry)

                if self.entry_repo.save(
                    entry_id=entry_id,
                    title=getattr(entry, "title", ""),
                    link=getattr(entry, "link", ""),
                    published=published_ts,
                    source_type="google",
                    query=query,
                ):
                    found_new = True

            except Exception as e:
                self.log.emit(f"Błąd wpisu: {e}")

        return found_new

    def _parse_published_ts(self, entry: Any) -> int | None:
        if getattr(entry, "published_parsed", None) is not None:
            return int(calendar.timegm(entry.published_parsed))

        published_str = getattr(entry, "published", "")
        if not published_str:
            return None

        try:
            dt = email.utils.parsedate_to_datetime(published_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except Exception:
            return None
