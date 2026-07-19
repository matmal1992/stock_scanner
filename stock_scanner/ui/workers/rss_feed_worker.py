import calendar
import email.utils
from datetime import timezone
from typing import Any

import feedparser
from feedparser import FeedParserDict
from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from stock_scanner.core.telegram import send_telegram_message
from stock_scanner.download.database import EntryRepository


class RSSWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    data_ready = Signal(list, bool)

    # WATCHLIST = ["KGHM", "CDPROJEKT", "ORLEN", "CREOTECH"]
    WATCHLIST = ["KGHM"]

    def __init__(self, entry_repo: EntryRepository, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.entry_repo = entry_repo
        self.manager = QNetworkAccessManager(self)
        self.reply: QNetworkReply

    def run(self, url: QUrl) -> None:
        self.log.emit("Start pobierania RSS from " + url.toString())

        request = QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", b"Mozilla/5.0")
        self.reply = self.manager.get(request)
        assert self.reply is not None
        self.reply.finished.connect(self._on_finished)

    def _on_finished(self) -> None:
        reply = self.reply
        if not self._validate_reply(self.reply):
            self.finished.emit()
            return

        data = self._read_reply(reply)
        entries = self._parse_feed(data)

        found_new = self._process_entries(entries)

        entries = self.entry_repo.get_latest("rss")
        if entries:
            self.data_ready.emit(entries, found_new)
        else:
            self.log.emit("Nie znaleziono wpisów w bazie danych do wyświetlenia")

        self.finished.emit()

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

    def _validate_reply(self, reply: QNetworkReply | None) -> bool:
        if reply is None:
            self.error.emit("Błąd wewnętrzny RSS: brak odpowiedzi")
            return False

        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.error.emit(f"Błąd sieciowy RSS: {reply.errorString()}")
            reply.deleteLater()
            return False

        return True

    def _read_reply(self, reply: QNetworkReply) -> bytes:
        data = reply.readAll().data()
        reply.deleteLater()
        return data

    def _parse_feed(self, data: bytes) -> list[FeedParserDict]:
        feed = feedparser.parse(data)

        if getattr(feed, "bozo", False) and getattr(feed, "bozo_exception", None):
            self.log.emit(f"feedparser warning: {feed.bozo_exception}")

        entries = feed.entries

        if not entries:
            self.error.emit("Brak wpisów w RSS")

        return entries

    def _process_entries(self, entries: list[FeedParserDict]) -> bool:
        found_new = False

        for entry in entries[:5]:
            try:
                if self._save_entry(entry):
                    found_new = True
                    self._check_alert(entry)

            except Exception as exc:
                self.log.emit(f"Błąd przy dodawaniu wpisu: {exc}")

        return found_new

    def _save_entry(self, entry: FeedParserDict) -> bool:
        entry_id = getattr(entry, "id", None) or getattr(entry, "link", None)

        if not entry_id:
            return False

        return self.entry_repo.save(
            entry_id=entry_id,
            title=getattr(entry, "title", ""),
            link=getattr(entry, "link", ""),
            published=self._parse_published_ts(entry),
            source_type="rss",
        )

    def _check_alert(self, entry: FeedParserDict) -> None:
        title = getattr(entry, "title", "")

        matched = self._check_for_tickers(title)

        if not matched:
            return

        tickers = ", ".join(matched)

        message = f"ALERT: {tickers} → {title}"

        print(message)

        send_telegram_message(message)

        self.log.emit(message)


def print_latest_rss_entries(url: str, limit: int = 20) -> None:
    feed = feedparser.parse(url)

    if not feed.entries:
        print("Brak wpisów w RSS")
        return

    for i, entry in enumerate(feed.entries[:limit], start=1):
        title = getattr(entry, "title", "")
        link = getattr(entry, "link", "")
        published = getattr(entry, "published", "")

        print(f"{i}. {title}")
        print(f"   {link}")
        print(f"   {published}")
        print("-" * 50)
