import logging
from datetime import datetime
from pathlib import Path

import cloudscraper
from bs4 import BeautifulSoup
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class WebsiteWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    result = Signal(str)

    def __init__(self, url: str) -> None:
        super().__init__()
        self.url = url

    def run(self) -> None:
        try:
            self.log.emit(f"Pobieranie: {self.url}")

            scraper = cloudscraper.create_scraper(
                browser={
                    "browser": "chrome",
                    "platform": "windows",
                    "mobile": False,
                }
            )

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Connection": "keep-alive",
            }

            # 🔁 retry logic
            for attempt in range(3):
                try:
                    response = scraper.get(
                        self.url,
                        headers=headers,
                        timeout=20,
                        allow_redirects=True,
                    )

                    if response.status_code == 200:
                        break

                    self.log.emit(f"Retry {attempt+1}: status {response.status_code}")

                except Exception as e:
                    self.log.emit(f"Retry {attempt+1} error: {e}")

            else:
                raise ValueError("Nie udało się pobrać strony")

            text = None
            html = response.text

            if not text:
                self.log.emit("Fallback do BeautifulSoup...")

                soup = BeautifulSoup(html, "html.parser")

                for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
                    tag.decompose()

                article = soup.find("article")

                if article:
                    raw_text = article.get_text(separator="\n")
                else:
                    raw_text = soup.get_text(separator="\n")

                lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                text = "\n".join(lines)

            if not text or len(text) < 200:
                raise ValueError("Za mało treści (możliwy paywall / blokada)")

            clean_text = self._prepare_for_llm(text)

            filename = f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            path = Path("data") / filename
            path.parent.mkdir(exist_ok=True)

            path.write_text(clean_text, encoding="utf-8")

            # self.result.emit(str(path))
            self.result.emit(clean_text)
            self.finished.emit()

        except Exception as e:
            logger.exception("Website worker error")
            self.error.emit(f"Website worker error: {e}")
            self.finished.emit()

    def _prepare_for_llm(self, text: str) -> str:
        lines = text.splitlines()

        cleaned = []
        seen = set()

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # usuń bardzo krótkie śmieci
            if len(line) < 30:
                continue

            # usuń duplikaty
            if line in seen:
                continue

            seen.add(line)
            cleaned.append(line)

        return "\n\n".join(cleaned)
