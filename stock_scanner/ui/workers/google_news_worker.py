import feedparser
from PySide6.QtCore import QObject, Signal

from stock_scanner.download.database import (
    get_latest_entries,
    insert_entry,
)


class GoogleNewsWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    data_ready = Signal(list, bool)

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

            for entry in feed.entries[:10]:
                try:
                    link = entry.link
                    if not ("bankier.pl" in link or "stockwatch.pl" in link):
                        continue

                    if insert_entry(entry, source_type="google", query=query):
                        found_new = True

                except Exception as e:
                    self.log.emit(f"Błąd wpisu: {e}")

            entries = get_latest_entries()

            self.data_ready.emit(entries, found_new)
            self.finished.emit()

        except Exception as e:
            self.error.emit(f"Google worker error: {e}")
            self.finished.emit()
