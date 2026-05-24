import feedparser
from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from stock_scanner.download.database import insert_entry


class RSSWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    data_ready = Signal(list)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.manager = QNetworkAccessManager(self)
        self.reply = None

    def run(self) -> None:
        url = QUrl("https://biznes.pap.pl/rss")
        self.log.emit("Start pobierania RSS from " + url.toString())

        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"Mozilla/5.0")
        self.reply = self.manager.get(request)
        self.reply.finished.connect(self._on_finished)

    def _on_finished(self) -> None:
        reply = self.reply
        if reply is None:
            self.error.emit("Błąd wewnętrzny RSS: brak odpowiedzi")
            self.finished.emit()
            return

        if reply.error() != QNetworkReply.NoError:
            self.error.emit(f"Błąd sieciowy RSS: {reply.errorString()}")
            reply.deleteLater()
            self.finished.emit()
            return

        data = bytes(reply.readAll())
        reply.deleteLater()

        feed = feedparser.parse(data)
        if feed.bozo and getattr(feed, "bozo_exception", None) is not None:
            self.log.emit(f"feedparser warning: {feed.bozo_exception}")

        if not feed.entries:
            self.error.emit("Brak wpisów w RSS feed — sprawdź połączenie lub strukturę RSS")
            self.finished.emit()
            return

        today_entries = []
        for e in feed.entries[:5]:
            title = getattr(e, "title", "Brak tytułu")
            today_entries.append(title)
            try:
                insert_entry(e)
            except Exception as entry_error:
                self.log.emit(f"Błąd przy dodawaniu wpisu: {str(entry_error)}")

        if today_entries:
            self.data_ready.emit(today_entries)
        else:
            self.log.emit("Nie znaleziono wpisów do wyświetlenia")

        self.finished.emit()
