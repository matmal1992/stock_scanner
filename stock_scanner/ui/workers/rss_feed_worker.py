import calendar
import email.utils
from datetime import datetime, timezone
from typing import Any

import feedparser
from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from stock_scanner.core.telegram import send_telegram_message
from stock_scanner.download.database import EntryRepository


class RSSWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    data_ready = Signal(list, bool)

    WATCHLIST = ["KGHM", "CDPROJEKT", "ORLEN", "CREOTECH"]

    def __init__(self, entry_repo: EntryRepository, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.entry_repo = entry_repo
        self.manager = QNetworkAccessManager(self)
        self.reply: QNetworkReply | None = None

    def run(self) -> None:
        url = QUrl("https://www.bankier.pl/rss/gielda.xml")
        self.log.emit("Start pobierania RSS from " + url.toString())

        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"Mozilla/5.0")
        self.reply = self.manager.get(request)
        assert self.reply is not None
        self.reply.finished.connect(self._on_finished)

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

    def _check_for_tickers(self, title: str) -> list[str]:
        title_upper = title.upper()
        return [ticker for ticker in self.WATCHLIST if ticker in title_upper]

    def _on_finished(self) -> None:
        reply = self.reply
        if reply is None:
            self.error.emit("Błąd wewnętrzny RSS: brak odpowiedzi")
            self.finished.emit()
            return

        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.error.emit(f"Błąd sieciowy RSS: {reply.errorString()}")
            reply.deleteLater()
            self.finished.emit()
            return

        data = reply.readAll().data()
        reply.deleteLater()

        feed = feedparser.parse(data)
        if feed.bozo and getattr(feed, "bozo_exception", None) is not None:
            self.log.emit(f"feedparser warning: {feed.bozo_exception}")

        if not feed.entries:
            self.error.emit("Brak wpisów w RSS feed — sprawdź połączenie lub strukturę RSS")
            self.finished.emit()
            return

        found_new = False
        for entry in feed.entries[:5]:
            try:
                entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)
                if not entry_id:
                    continue

                published_ts = None
                if getattr(entry, "published_parsed", None) is not None:
                    dt = datetime(*entry.published_parsed[:6])
                    published_ts = int(dt.timestamp())

                if self.entry_repo.save(
                    entry_id=entry_id,
                    title=getattr(entry, "title", ""),
                    link=getattr(entry, "link", ""),
                    published=published_ts,
                    source_type="rss",
                ):
                    found_new = True

                    title = getattr(entry, "title", "")
                    matched = self._check_for_tickers(title)

                    if matched:
                        tickers_str = ", ".join(matched)
                        print(f"[ALERT] {tickers_str} → {title}")
                        send_telegram_message(f"ALERT: {tickers_str} → {title}")
                        self.log.emit(f"ALERT: {tickers_str} → {title}")

            except Exception as entry_error:
                self.log.emit(f"Błąd przy dodawaniu wpisu: {str(entry_error)}")

        entries = self.entry_repo.get_latest("rss")
        if entries:
            self.data_ready.emit(entries, found_new)
        else:
            self.log.emit("Nie znaleziono wpisów w bazie danych do wyświetlenia")

        self.finished.emit()
