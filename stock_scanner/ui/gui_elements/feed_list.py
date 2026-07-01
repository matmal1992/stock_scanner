from typing import List, Sequence,Tuple

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from stock_scanner.download.database import get_entry_link_by_id
from stock_scanner.ui.workers.llm_worker import ManualPromptWorker


class NewsFeedList(QWidget):
    selection_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._ids: List[str | None] = []
        self.list = QListWidget()
        get_news_btn = QPushButton("Get feed")
        get_news_btn.clicked.connect(self.getting_news)
        self.list.itemSelectionChanged.connect(self.on_selection_changed)
        self.displ_link_btn = QPushButton("Display link")
        self.displ_link_btn.clicked.connect(self.on_display_link_clicked)
        self.test_llm_btn = QPushButton("Run LLM")
        self.test_llm_btn.setEnabled(False)
        self.displ_link_btn.setEnabled(False)
       
        self.test_llm_btn.clicked.connect(self.on_run_llm_clicked)

        self.list.itemSelectionChanged.connect(self._on_selection_changed)
        
        test_buttons_box = QHBoxLayout()
        test_buttons_box.addWidget(get_news_btn)
        test_buttons_box.addWidget(self.displ_link_btn)
        test_buttons_box.addWidget(self.test_llm_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.list)
        layout.addLayout(test_buttons_box)
        self.setLayout(layout)

    def set_items(self, items: Sequence[Tuple[str, str | None]]) -> None:
        self.list.clear()
        self._ids = []

        for text, entry_id in items:
            self.list.addItem(text)
            self._ids.append(entry_id)

    def get_selected_id(self) -> str | None:
        index = self.list.currentRow()
        if 0 <= index < len(self._ids):
            return self._ids[index]
        return None

    def _on_selection_changed(self) -> None:
        entry_id = self.get_selected_id()
        if entry_id:
            self.selection_changed.emit(entry_id)
            
    def on_selection_changed(self) -> None:
        self.selected_entry_id = self.status.get_selected_id()
        self.displ_link_btn.setEnabled(self.selected_entry_id is not None)
        self.test_llm_btn.setEnabled(self.selected_entry_id is not None)

    def get_selected_id(self) -> str | None:
        index = self.currentRow()
        if 0 <= index < len(self._ids):
            return self._ids[index]
        return None
    
    def on_display_link_clicked(self) -> None:
        if not self.selected_entry_id:
            print("Brak zaznaczonego wpisu")
            return

        link = get_entry_link_by_id(self.selected_entry_id)

        if not link:
            print("Nie znaleziono linku w bazie")
            return

        print(f"Selected link: {link}")
        
    def on_run_llm_clicked(self) -> None:
        if not self.selected_entry_id:
            return

        link = get_entry_link_by_id(self.selected_entry_id)
        if not link:
            return

        self.status_label.setText("Wysyłanie zapytania do LLM...")

        self.llm_worker = ManualPromptWorker(link)
        self.llm_worker.response_received.connect(self.on_llm_result)
        self.llm_worker.start()

    def on_llm_result(self) -> None:
        self.status_label.set_ok("LLM zakończony")