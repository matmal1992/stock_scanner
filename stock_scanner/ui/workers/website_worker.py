import logging
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from stock_scanner.download.scrapers import (
    # clean_text_for_llm,
    extract_text_bs4,
    extract_text_newspaper,
    get_html,
)

logger = logging.getLogger(__name__)


class WebsiteWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    result = Signal(str)

    def __init__(self, url: str, type: str = "bs4") -> None:
        super().__init__()
        self.url = url
        self.type = type

    def run(self) -> None:
        try:
            self.log.emit(f"Pobieranie: {self.url}")
            html = get_html(self.url)
            self.log.emit("Parsowanie HTML...")

            text = ""

            if self.type == "bs4":
                try:
                    self.log.emit("Próba parsowania przez bs4...")
                    text = extract_text_bs4(html)
                except Exception as exc:
                    self.log.emit(f"bs4 fallback error: {exc}")

            if self.type == "newspaper":
                try:
                    self.log.emit("Próba parsowania przez newspaper...")
                    text = extract_text_newspaper(self.url)
                except Exception as exc:
                    self.log.emit(f"newspaper fallback error: {exc}")

            # clean_text = clean_text_for_llm(text)

            filename = f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            path = Path("data") / filename
            path.parent.mkdir(exist_ok=True)
            path.write_text(text, encoding="utf-8")

            self.result.emit(text)
            self.finished.emit()

        except Exception as e:
            logger.exception("Website worker error")
            self.error.emit(f"Website worker error: {e}")
            self.finished.emit()
