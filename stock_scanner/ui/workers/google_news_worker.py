import logging
from datetime import datetime

import feedparser
from PySide6.QtCore import QObject, Signal

from stock_scanner.download.database import EntryRepository

logger = logging.getLogger(__name__)


class GoogleNewsWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    data_ready = Signal(list, bool)

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo

    def run(self) -> None:
        try:
            query = '"Creotech Instruments" site:bankier.pl OR site:stockwatch.pl'

            url = (
                "https://news.google.com/rss/search?"
                f"q={query.replace(' ', '+')}"
                "&hl=pl&gl=PL&ceid=PL:pl"
            )

            self.log.emit("Pobieranie Google News...")

            feed = feedparser.parse(url)

            if not feed.entries:
                self.error.emit("Brak wyników Google News")
                self.finished.emit()
                return

            found_new = False

            for index, entry in enumerate(feed.entries[:10]):
                try:
                    entry_id = (
                        getattr(entry, "id", None)
                        or getattr(entry, "link", None)
                        or f"google-{index}"
                    )
                    published_ts = None
                    if getattr(entry, "published_parsed", None) is not None:
                        dt = datetime(*entry.published_parsed[:6])
                        published_ts = int(dt.timestamp())

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

            entries = self.entry_repo.get_latest("google")

            self.data_ready.emit(entries, found_new)
            self.finished.emit()

        except Exception as e:
            self.error.emit(f"Google worker error: {e}")
            self.finished.emit()
