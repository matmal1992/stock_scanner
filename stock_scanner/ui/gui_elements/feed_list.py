from datetime import datetime
from typing import List, Sequence, Tuple

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stock_scanner.core.utils import FeedAdapter, NewsFormatter
from stock_scanner.download.database import (
    get_entry_link_by_id,
    get_latest_entries_with_id,
    insert_entry_raw,
)
from stock_scanner.download.news_fetcher import NewsFetcher
from stock_scanner.ui.workers.llm_worker import ManualPromptWorker


class NewsFeedList(QWidget):
    selection_changed = Signal(str)

    def __init__(self, parent) -> None:
        super().__init__()
        self.parent_window = parent
        self._ids: List[str | None] = []

        self.feed_list = QListWidget()
        self.feed_list.itemSelectionChanged.connect(self.on_selection_changed)

        get_news_btn = QPushButton("Get feed")
        self.displ_link_btn = QPushButton("Display link")
        self.test_llm_btn = QPushButton("Run LLM")
        get_news_btn.clicked.connect(self.on_get_news_clicked)
        self.displ_link_btn.clicked.connect(self.on_display_link_clicked)
        self.test_llm_btn.clicked.connect(self.on_run_llm_clicked)
        self.test_llm_btn.setEnabled(False)
        self.displ_link_btn.setEnabled(False)

        self.fetcher = NewsFetcher()
        self.fetcher.data_ready.connect(self.on_data_ready)
        self.fetcher.log.connect(self.on_log)
        self.fetcher.error.connect(self.on_error)

        test_buttons_box = QHBoxLayout()
        test_buttons_box.addWidget(get_news_btn)
        test_buttons_box.addWidget(self.displ_link_btn)
        test_buttons_box.addWidget(self.test_llm_btn)

        layout = QVBoxLayout()
        layout.addLayout(test_buttons_box)
        layout.addWidget(self.feed_list)

        self.setLayout(layout)

    def set_items(self, items: Sequence[Tuple[str, str | None]]) -> None:
        self.feed_list.clear()
        self._ids = []

        for text, entry_id in items:
            self.feed_list.addItem(text)
            self._ids.append(entry_id)

    def on_get_news_clicked(self) -> None:
        self.parent_window.notifications.set_ok("Pobieranie wiadomości...")
        self.fetcher.fetch()

        # if not self.timer.isActive():
        #     self.timer.start()

    def get_selected_id(self) -> str | None:
        index = self.feed_list.currentRow()
        if 0 <= index < len(self._ids):
            return self._ids[index]
        return None

    def on_selection_changed(self) -> None:
        self.selected_entry_id = self.get_selected_id()
        self.displ_link_btn.setEnabled(self.selected_entry_id is not None)
        self.test_llm_btn.setEnabled(self.selected_entry_id is not None)

    def on_display_link_clicked(self) -> None:
        if not self.selected_entry_id:
            self.parent_window.notifications.set_error("Brak zaznaczonego wpisu")
            return

        link = get_entry_link_by_id(self.selected_entry_id)

        if not link:
            self.parent_window.notifications.set_warning("Nie znaleziono linku w bazie")
            return

        self.parent_window.notifications.set_ok(f"Link: {link}")

    def on_run_llm_clicked(self) -> None:
        if not self.selected_entry_id:
            self.parent_window.notifications.set_error("Run LLM: Brak zaznaczonego wpisu")
            return

        link = get_entry_link_by_id(self.selected_entry_id)
        if not link:
            self.parent_window.notifications.set_error("Run LLM: Nie znaleziono linku w bazie")
            return

        self.parent_window.notifications.set_ok(f"Run LLM: Link: {link}")

        self.llm_worker = ManualPromptWorker(link)
        self.llm_worker.response_received.connect(self.on_llm_result)
        self.llm_worker.start()

    def on_llm_result(self) -> None:
        self.parent_window.notifications.set_ok("LLM zakończony")

    def on_log(self, text: str) -> None:
        self.parent_window.notifications.set_ok(text)
        # now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # self.set_status_item(0, f"{now} Status: {text}")

    def on_error(self, e: str) -> None:
        now = datetime.now()
        error_time = now.strftime("%Y-%m-%d %H:%M:%S")
        # self._set_status_item(0, f"{error_time} Błąd: {e}")
        self.parent_window.notifications.set_error(f"{error_time} Błąd: {e}")

    def on_data_ready(
        self, items: list[tuple[str, str, int | None, str]], has_new_entries: bool
    ) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. zapis do DB (czytelny i prosty)
        for item in items:
            insert_entry_raw(**FeedAdapter.to_db(item))

        # 2. DB → UI
        rows = get_latest_entries_with_id()
        formatted = NewsFormatter.format(rows)

        # 3. status
        if has_new_entries:
            status_text = f"Nowe wpisy: {now}"
        else:
            status_text = f"{now}: Brak nowych wpisów"

        # 4. UI update
        self.set_items([(status_text, "")] + formatted)
