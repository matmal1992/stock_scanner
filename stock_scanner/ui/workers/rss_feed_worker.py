from datetime import datetime

import feedparser
from PySide6.QtCore import QObject, Signal


class RSSWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    data_ready = Signal(list)

    def run(self) -> None:
        url = "https://biznes.pap.pl/rss"
        # url = "https://www.bankier.pl/rss/wiadomosci.xml"
        self.log.emit("Start pobierania RSS from " + url)
        today = datetime.now().date()

        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
            today_entries = []

            for entry in feed.entries:
                if not hasattr(entry, "published_parsed"):
                    continue

                entry_date = datetime(*entry.published_parsed[:6]).date()

                if entry_date == today:
                    today_entries.append(entry)

            self.log.emit(f"Entries: {len(today_entries)}")

            titles = [e.title for e in today_entries]
            self.data_ready.emit(titles)

        except Exception as e:
            self.error.emit(str(e))

        self.finished.emit()
