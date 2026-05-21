import feedparser
from PySide6.QtCore import QObject, Signal


class RSSWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    data_ready = Signal(list)

    def run(self) -> None:
        # url = "https://biznes.pap.pl/rss/firmy"
        url = "https://www.bankier.pl/rss/wiadomosci.xml"
        self.log.emit("Start pobierania RSS from " + url)

        try:
            feed = feedparser.parse(url)

            self.log.emit(f"Entries: {len(feed.entries)}")

            titles = [e.title for e in feed.entries[:5]]
            self.data_ready.emit(titles)

        except Exception as e:
            self.error.emit(str(e))

        self.finished.emit()
